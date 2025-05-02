#!/usr/bin/env python3
"""
ingest.py – build & persist a FAISS + embeddings index with fine-grained chunks
--------------------------------------------------------------------------
 1. Loads all files under --input_dir
 2. Splits them into 256-token chunks with 96-token overlap
 3. Embeds with Gemini (or fallback HF) and stores in FAISS
 4. Persists the index and node dump for BM25
"""

from __future__ import annotations
import argparse
import os
import pickle
from pathlib import Path
from dotenv import load_dotenv

import faiss  # pip install faiss-cpu  (or faiss-gpu)
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader
from llama_index.vector_stores.faiss import FaissVectorStore

# Google GenAI Embeddings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from google.genai.errors import ClientError

# HuggingFace Embeddings (offline fallback)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# ── Configuration ─────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_MODEL = "gemini-embedding-exp-03-07"
# Correct path for MiniLM in sentence-transformers
HF_MODEL = "all-MiniLM-L6-v2"
USE_HF = os.getenv("USE_HF_EMBEDDINGS") == "1"

# ── Helpers ───────────────────────────────────────────────────────────────────
def infer_dim(embedder) -> int:
    # probe to get embedding dimensionality
    return len(embedder.get_text_embedding("dim_probe"))

# ── Embedding batcher with fallback ───────────────────────────────────────────
def get_embedder() -> tuple[object, str]:
    """
    Returns (embedder, label), choosing GoogleGenAI or HuggingFace
    """
    if USE_HF or not API_KEY:
        print("[ingest] 🗄️  Using HuggingFace embeddings (offline)")
        return HuggingFaceEmbedding(model_name=HF_MODEL), "HF"
    print("[ingest] ☁️  Using Google Gemini embeddings")
    return GoogleGenAIEmbedding(model_name=EMBED_MODEL, api_key=API_KEY), "GEMINI"

# ── Build and persist index ───────────────────────────────────────────────────
def build_index(input_dir: Path, index_path: Path) -> None:
    # 1) Load documents
    docs = SimpleDirectoryReader(str(input_dir), recursive=True).load_data()
    print(f"[ingest] 📄  Loaded {len(docs)} documents from {input_dir}")

    # 2) Chunking
    splitter = SentenceSplitter(chunk_size=256, chunk_overlap=96, paragraph_separator="\n\n")
    nodes: list = []
    for doc in docs:
        nodes.extend(splitter.get_nodes_from_documents([doc]))
    print(f"[ingest] ✂️  Created {len(nodes)} chunks (256/96)")

    # 3) FAISS setup
    embedder, embed_tag = get_embedder()
    dim = infer_dim(embedder)
    cpu_index = faiss.IndexFlatIP(dim)
    try:
        from faiss import StandardGpuResources, index_cpu_to_gpu
        gpu_ix = index_cpu_to_gpu(StandardGpuResources(), 0, cpu_index)
        faiss_index = gpu_ix
        print("[ingest] 🌟 FAISS-GPU enabled")
    except ImportError:
        faiss_index = cpu_index
        print("[ingest] ⚠️  FAISS-GPU not available → using CPU")

    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_ctx = StorageContext.from_defaults(vector_store=vector_store)

    # 4) Build index, retrying with HF if Gemini hits 429
    try:
        VectorStoreIndex(
            nodes,
            embed_model=embedder,
            storage_context=storage_ctx,
        )
    except ClientError as e:
        if embed_tag == "GEMINI" and e.status == 429:
            print("[ingest] 🚨 Gemini quota exhausted, switching to HF embeddings")
            embedder, _ = ("HF", HuggingFaceEmbedding(model_name=HF_MODEL))
            VectorStoreIndex(
                nodes,
                embed_model=embedder,
                storage_context=storage_ctx,
            )
        else:
            raise

    # 5) Persist FAISS + storage
    vector_store.persist(persist_path=str(index_path))
    meta_dir = index_path.parent / "storage"
    storage_ctx.persist(persist_dir=str(meta_dir))
    print(f"[ingest] ✅ Vector index stored in {meta_dir}")

    # 6) Dump nodes for BM25
    node_dump = index_path.parent / "nodes.pkl"
    with open(node_dump, "wb") as f:
        pickle.dump(nodes, f)
    print(f"[ingest] ✅ Saved raw nodes for BM25 → {node_dump}")

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = argparse.ArgumentParser("Create FAISS index with Gemini/HF embeddings")
    p.add_argument("--input_dir", required=True, help="Document folder")
    p.add_argument(
        "--index_path",
        required=True,
        help="Path to store .faiss (meta in ./storage/)",
    )
    args = p.parse_args()
    build_index(Path(args.input_dir), Path(args.index_path))
