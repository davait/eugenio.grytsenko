#!/usr/bin/env python3
"""
FastAPI service exposing:
  • GET  /       → React-based chatbot UI
  • POST /chat   → RAG chat backed by FAISS + embeddings
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import torch
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM

from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.vector_stores.faiss import FaissVectorStore
from tools import get_tools

# Embeddings online/offline
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from google.genai.errors import ClientError
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

# Paths and config
BASE = Path(__file__).parent.resolve()
INDEX_PATH   = BASE / "data/index.faiss"
STORAGE_DIR  = BASE / "data/storage"
TOP_K        = int(os.getenv("RAG_TOP_K", 5))
HISTORY_LIMIT = 20

LLM_MODEL_ID   = "meta-llama/Meta-Llama-3-8B-Instruct"
EMBED_MODEL_ID = "gemini-embedding-exp-03-07"
HF_MODEL_ID    = "all-MiniLM-L6-v2"

GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY")
USE_HF_ENVVAR     = os.getenv("USE_HF_EMBEDDINGS") == "1"

# ──────────────────────────────────────────────────────────────────────────────
# Select embedder
def get_embedder():
    if (not GEMINI_API_KEY) or USE_HF_ENVVAR:
        print("[app] 🗄️  Using HuggingFaceEmbedding (offline)")
        return HuggingFaceEmbedding(model_name=HF_MODEL_ID), "HF"
    print("[app] ☁️  Using GoogleGenAIEmbedding (online)")
    return GoogleGenAIEmbedding(model_name=EMBED_MODEL_ID, api_key=GEMINI_API_KEY), "GEMINI"

# 1) Load LLM
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_ID, trust_remote_code=True)
model     = AutoModelForCausalLM.from_pretrained(
    LLM_MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
llm = HuggingFaceLLM(
    model=model,
    tokenizer=tokenizer,
    context_window=4096,
    max_new_tokens=2048,
    generate_kwargs={"temperature": float(os.getenv("LLM_TEMPERATURE", 0.1))},
)

# 2) Select embedder
embedder, embed_tag = get_embedder()

# 3) Load FAISS + StorageContext
if not INDEX_PATH.exists() or not STORAGE_DIR.exists():
    raise RuntimeError("Index or storage not found; run ingest.py first")
vector_store = FaissVectorStore.from_persist_path(str(INDEX_PATH))
storage_context = StorageContext.from_defaults(
    persist_dir=str(STORAGE_DIR),
    vector_store=vector_store,
)

# 4) Rebuild index
try:
    index = load_index_from_storage(storage_context, embed_model=embedder)
except ClientError as e:
    if embed_tag == "GEMINI" and e.status == 429:
        print("[app] 🚨 Gemini quota exceeded, falling back to HF embeddings")
        embedder, _ = HuggingFaceEmbedding(model_name=HF_MODEL_ID), "HF"
        index = load_index_from_storage(storage_context, embed_model=embedder)
    else:
        raise

# 5) Chat engine
tools = get_tools()
chat_engine = CondensePlusContextChatEngine.from_defaults(
    llm=llm,
    retriever=index.as_retriever(similarity_top_k=TOP_K),
    memory_cls=lambda: ChatMemoryBuffer(token_limit=4096),
    tools=tools,
    verbose=True,
)

# Clear GPU cache at startup
torch.cuda.empty_cache()

app = FastAPI(title="RAG Chatbot", version="1.0.0")
SESSIONS: dict[str, dict[str, object]] = {}

# ──────────────────────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str | None = None
    message:    str

class ChatResponse(BaseModel):
    session_id: str
    answer:     str
    sources:    list[str]
    follow_up:  str | None = None

# ──────────────────────────────────────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    state = SESSIONS.get(session_id)
    if state is None:
        state = {"memory": ChatMemoryBuffer(token_limit=4096), "count": 0}
        SESSIONS[session_id] = state
    session_memory: ChatMemoryBuffer = state["memory"]
    chat_engine._memory = session_memory

    try:
        with torch.inference_mode():
            if any(tool.name in req.message.lower() for tool in tools):
                for tool in tools:
                    if tool.name in req.message.lower():
                        result = tool.run(req.message)
                        resp = chat_engine.chat(f"Tool {tool.name} used. Result: {result}")
                        break
            else:
                resp = chat_engine.chat(req.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    answer = str(resp)
    raw_paths: list[str] = []
    for node in (resp.source_nodes or []):
        meta = getattr(node.node, "metadata", {}) or getattr(node.node, "extra_info", {})
        path = meta.get("file_path") or meta.get("source")
        if path:
            raw_paths.append(path)
    sources = list(dict.fromkeys(raw_paths))

    del resp
    torch.cuda.empty_cache()

    state["count"] += 1
    follow_up: str | None = None
    if state["count"] > HISTORY_LIMIT:
        session_memory.reset()
        state["count"] = 0
        follow_up = "🔄 Chat history was cleared to optimize performance."

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        sources=sources,
        follow_up=follow_up,
    )

# ──────────────────────────────────────────────────────────────────────────────
# React UI
# ──────────────────────────────────────────────────────────────────────────────
INDEX_HTML = """<!DOCTYPE html>
<html lang="en" class="h-full bg-gray-100">
  <head>
    <meta charset="UTF-8"/>
    <title>RAG Chatbot</title>
    <meta name="viewport" content="width=device-width,initial-scale=1"/>
    <script src="https://cdn.tailwindcss.com"></script>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github-dark.min.css"/>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/python.min.js"></script>
  </head>
  <body class="h-full flex items-center justify-center p-4">
    <div id="root" class="w-full max-w-4xl h-full bg-white shadow-lg rounded-lg flex flex-col overflow-hidden"></div>
    <script type="text/javascript">
      const e = React.createElement;

      // Copy icon component (bot responses only)
      function CopyIcon({ text }) {
        const [hover, setHover] = React.useState(false);
        const copy = async () => {
          if (navigator.clipboard?.writeText) {
            try {
              await navigator.clipboard.writeText(text);
            } catch {
              fallbackCopy(text);
            }
          } else {
            fallbackCopy(text);
          }
        };
        const fallbackCopy = (t) => {
          const ta = document.createElement('textarea');
          ta.value = t;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        };
        return e('button', {
          onClick: copy,
          onMouseEnter: () => setHover(true),
          onMouseLeave: () => setHover(false),
          className: 'absolute top-2 right-2 p-1 rounded-full hover:bg-gray-200'
        }, e('svg', {
          xmlns: 'http://www.w3.org/2000/svg',
          viewBox: '0 0 24 24',
          fill: hover ? '#111' : '#666',
          className: 'w-5 h-5'
        }, e('path', {
          d: 'M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 16H8V7h11v14z'
        })));
      }

      function ChatMessage({ msg }) {
        const isUser = msg.role === 'user';
        return e('div', {
          className: `my-2 flex ${isUser ? 'justify-end' : 'justify-start'}`
        },
          e('div', { className: 'relative w-full' },
            e('div', {
              className: `whitespace-pre-wrap px-6 py-4 rounded-2xl shadow ${
                isUser
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-gray-100 text-gray-900 rounded-bl-none'
              }`,
              dangerouslySetInnerHTML: { __html: marked.parse(msg.text) }
            }),
            // only bot responses get the copy icon
            !isUser && e(CopyIcon, { text: msg.text })
          )
        );
      }

      function ChatApp() {
        const [msgs, setMsgs] = React.useState([
          { role: 'bot', text: 'How can I help you?' }
        ]);
        const [inpt, setInpt] = React.useState('');
        const [ldg, setLdg] = React.useState(false);
        const sid = React.useRef(localStorage.getItem('rag_session') || crypto.randomUUID());

        React.useEffect(() => {
          localStorage.setItem('rag_session', sid.current);
        }, []);

        React.useEffect(() => {
          document.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
          const sb = document.getElementById('scrollbox');
          if (sb) sb.scrollTop = sb.scrollHeight;
        }, [msgs]);

        const send = async () => {
          const t = inpt.trim();
          if (!t) return;
          setMsgs(m => [...m, { role: 'user', text: t }]);
          setInpt(''); setLdg(true);
          try {
            const res = await fetch('/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ session_id: sid.current, message: t })
            });
            if (!res.ok) throw new Error(await res.text());
            const d = await res.json();
            setMsgs(m => [
              ...m,
              { role: 'bot', text: d.answer },
              ...(d.follow_up ? [{ role: 'bot', text: d.follow_up }] : [])
            ]);
          } catch (e) {
            setMsgs(m => [...m, { role: 'bot', text: 'Error: ' + e.message }]);
          } finally {
            setLdg(false);
          }
        };

        const onKeyDown = e => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            send();
          }
        };

        return e('div', { className: 'flex flex-col h-full' },
          e('div', { id: 'scrollbox', className: 'flex-1 overflow-y-auto p-6 bg-white' },
            msgs.map((m, i) => e(ChatMessage, { key: i, msg: m })),
            ldg && e('div', { className: 'text-gray-500 text-sm animate-pulse' }, 'Thinking...')
          ),
          e('div', { className: 'p-4 bg-gray-50 border-t flex gap-3 items-center' },
            e('input', {
              type: 'text',
              className: 'flex-1 border rounded-lg px-4 py-2 focus:outline-none',
              placeholder: 'Type your message...',
              value: inpt,
              onChange: e => setInpt(e.target.value),
              onKeyDown
            }),
            e('button', {
              className: 'bg-blue-600 text-white px-6 py-2 rounded-lg disabled:opacity-50',
              disabled: ldg || !inpt.trim(),
              onClick: send
            }, 'Send')
          )
        );
      }

      ReactDOM.createRoot(document.getElementById('root')).render(e(ChatApp));
    </script>
  </body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)
