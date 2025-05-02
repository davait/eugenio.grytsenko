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

LLM_MODEL_ID   = "meta-llama/Meta-Llama-3-8B-Instruct"
EMBED_MODEL_ID = "gemini-embedding-exp-03-07"
HF_MODEL_ID    = "all-MiniLM-L6-v2"

GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY")
USE_HF_ENVVAR     = os.getenv("USE_HF_EMBEDDINGS") == "1"

# ──────────────────────────────────────────────────────────────────────────────
# Select embedder: Google Gemini if key exists and HF is not forced; otherwise HF.
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

# 4) Rebuild index injecting the selected embedder
try:
    index = load_index_from_storage(storage_context, embed_model=embedder)
except ClientError as e:
    # fallback if Gemini fails at runtime
    if embed_tag == "GEMINI" and e.status == 429:
        print("[app] 🚨 Gemini quota exceeded, falling back to HF embeddings")
        embedder, _ = HuggingFaceEmbedding(model_name=HF_MODEL_ID), "HF"
        index = load_index_from_storage(storage_context, embed_model=embedder)
    else:
        raise

# 5) Create chat engine
chat_engine = CondensePlusContextChatEngine.from_defaults(
    llm=llm,
    retriever=index.as_retriever(similarity_top_k=TOP_K),
    memory_cls=ChatMemoryBuffer,
    verbose=True,
)

app = FastAPI(title="RAG Chatbot", version="1.0.0")
SESSIONS: dict[str, ChatMemoryBuffer] = {}

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

# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    try:
        resp = chat_engine.chat(req.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Extract source paths
    raw_paths: list[str] = []
    for node in (resp.source_nodes or []):
        meta = getattr(node.node, "metadata", {}) or getattr(node.node, "extra_info", {})
        path = meta.get("file_path") or meta.get("source")
        if path:
            raw_paths.append(path)
    sources = list(dict.fromkeys(raw_paths))

    return ChatResponse(session_id=session_id, answer=str(resp), sources=sources)

# ──────────────────────────────────────────────────────────────────────────────
# React UI at GET /
# ──────────────────────────────────────────────────────────────────────────────
INDEX_HTML = """<!DOCTYPE html>
<html lang="en" class="h-full bg-gray-50">
  <head>
    <meta charset="UTF-8"/>
    <title>RAG Chatbot</title>
    <meta name="viewport" content="width=device-width,initial-scale=1"/>
    <script src="https://cdn.tailwindcss.com"></script>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  </head>
  <body class="h-full flex flex-col">
    <div id="root" class="flex-1 flex flex-col"></div>
    <script type="module">
      // polyfill uuid
      function getUUID(){
        if(window.crypto?.randomUUID) return window.crypto.randomUUID();
        if(window.crypto?.getRandomValues){
          const b=crypto.getRandomValues(new Uint8Array(16));
          b[6]=(b[6]&0x0f)|0x40; b[8]=(b[8]&0x3f)|0x80;
          return [...b].map(x=>x.toString(16).padStart(2,'0'))
            .join('').match(/.{1,8}/g).join('-');
        }
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>(
          (c==='x'?Math.random()*16:(Math.random()*4+8))|0
        ).toString(16));
      }

      function ChatMessage({msg}){
        const isUser = msg.role==='user';
        return React.createElement('div',{
          className:'my-2 flex '+(isUser?'justify-end':'justify-start')
        },
          React.createElement('div',{
            className:
              'max-w-lg px-4 py-2 rounded-2xl shadow '+
              (isUser?'bg-blue-600 text-white rounded-br-none':'bg-white text-gray-800 rounded-bl-none')
          }, msg.text)
        );
      }

      function ChatApp(){
        const [msgs,setMsgs]=React.useState([]);
        const [inpt,setInpt]=React.useState('');
        const [ldg,setLdg]=React.useState(false);
        const sid=React.useRef(localStorage.getItem('rag_session')||getUUID());
        React.useEffect(()=>{localStorage.setItem('rag_session',sid.current)},[]);
        const send=async t=>{
          if(!t.trim())return;
          setMsgs(m=>[...m,{role:'user',text:t}]);
          setInpt(''); setLdg(true);
          try{
            const res=await fetch('/chat',{
              method:'POST',
              headers:{'Content-Type':'application/json'},
              body:JSON.stringify({session_id:sid.current,message:t})
            });
            if(!res.ok)throw new Error(await res.text());
            const d=await res.json();
            setMsgs(m=>[
              ...m,
              {role:'bot',text:d.answer,sources:d.sources},
              ...(d.follow_up?[{role:'bot',text:d.follow_up}]:[])
            ]);
          }catch(e){alert('Error: '+e.message)}
          finally{setLdg(false)}
        };
        return React.createElement('div',{className:'flex flex-col h-full'},
          React.createElement('div',{id:'scrollbox',className:'flex-1 overflow-y-auto p-4 space-y-1'},
            msgs.map((m,i)=>React.createElement(ChatMessage,{key:i,msg:m})),
            ldg&&React.createElement('div',{className:'text-gray-400 text-sm animate-pulse'},'Typing...')
          ),
          React.createElement('form',{
            className:'p-4 border-t flex gap-2',
            onSubmit:e=>{e.preventDefault();send(inpt);}
          },
            React.createElement('input',{
              className:'flex-1 border rounded-xl px-4 py-2 focus:outline-none',
              placeholder:'Type your message...',
              value:inpt,onChange:e=>setInpt(e.target.value)
            }),
            React.createElement('button',{
              className:'bg-blue-600 text-white px-4 py-2 rounded-xl disabled:opacity-50',
              disabled:ldg||!inpt.trim()
            },'Send')
          )
        );
      }

      ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(ChatApp));
    </script>
  </body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)
