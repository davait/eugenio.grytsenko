#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Evaluate a RAG pipeline extracting retrieval‐quality metrics
for every question in a JSONL dataset.

Improvements:
1. Correct plugin import of BM25Retriever.
2. Updated install message.
3. Fallback to rank_bm25's BM25Okapi if plugin unavailable.
4. Fallback to simple Keyword‐Overlap retriever if BM25 not available.
5. Accept keys: user_input, question, query.
6. Unicode‐safe fallback when persisted index can’t be read.
7. Do not pass extra top_k into plugin retrieve() to avoid signature mismatch.
"""

import argparse
import json
import pickle
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from tqdm import tqdm

# ─────────────────────────────────────────────────────────────────────────────
# Try Llama-Index BM25 plugin
# ─────────────────────────────────────────────────────────────────────────────
try:
    from llama_index.retrievers.bm25 import BM25Retriever  # type: ignore
    from llama_index.core import StorageContext, load_index_from_storage  # type: ignore
    _plugin_bm25 = True
except ImportError:
    _plugin_bm25 = False
    print(
        "[evaluate] ⚠️  BM25Retriever plugin not available.",
        file=sys.stderr,
    )
    print(
        "          To enable it, run:\n"
        "              pip install llama-index-retrievers-bm25",
        file=sys.stderr,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Try rank_bm25 for a pure-Python BM25 fallback
# ─────────────────────────────────────────────────────────────────────────────
try:
    from rank_bm25 import BM25Okapi
    _has_rank_bm25 = True
except ImportError:
    _has_rank_bm25 = False

# ─────────────────────────────────────────────────────────────────────────────
# Keyword‐Overlap retriever (no external deps)
# ─────────────────────────────────────────────────────────────────────────────
TokenSet = set[str]


class KeywordOverlapRetriever:
    _split_re = re.compile(r"\w+", re.UNICODE)

    @classmethod
    def _tokenize(cls, text: str) -> TokenSet:
        return {tok.lower() for tok in cls._split_re.findall(text)}

    def __init__(self, nodes: Sequence["TextNodeLike"]):
        self._nodes = list(nodes)
        self._token_cache: Dict[str, TokenSet] = {}

    def _node_tokens(self, node: "TextNodeLike") -> TokenSet:
        if node.node_id not in self._token_cache:
            self._token_cache[node.node_id] = self._tokenize(node.text)
        return self._token_cache[node.node_id]

    def retrieve(self, query: str, top_k: int = 5) -> List["TextNodeLike"]:
        q_tokens = self._tokenize(query)
        scored: List[Tuple[int, "TextNodeLike"]] = [
            (len(q_tokens & self._node_tokens(n)), n) for n in self._nodes
        ]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [n for _, n in scored[:top_k]]


class TextNodeLike:
    """Stub node for fallback retrievers."""

    __slots__ = ("text", "node_id")

    def __init__(self, text: str, node_id: str):
        self.text = text
        self.node_id = node_id

    def get_text(self) -> str:
        return self.text


def _load_nodes(pickle_path: Path) -> List[TextNodeLike]:
    with open(pickle_path, "rb") as fh:
        return pickle.load(fh)


def _extract_question(obj: dict) -> str:
    for key in ("user_input", "question", "query"):
        if key in obj:
            return obj[key]
    raise KeyError(f"No question key found in JSON: {list(obj.keys())}")


def _get_text_from_node(result) -> str:
    # plugin BM25 result has .node, stub has .text
    if hasattr(result, "node"):
        node = result.node
        if hasattr(node, "get_content"):
            return node.get_content()
        if hasattr(node, "get_text"):
            return node.get_text()
        return str(node)
    if hasattr(result, "text"):
        return result.text
    return str(result)


def evaluate(
    storage_dir: Path,
    nodes_pickle: Path,
    questions_path: Path,
    out_path: Path,
    top_k_ctx: int = 5,
) -> None:
    # Load raw nodes for all fallbacks
    nodes = _load_nodes(nodes_pickle)

    bm25_retriever = None

    # 1) Try plugin + persisted index
    if _plugin_bm25:
        try:
            storage_ctx = StorageContext.from_defaults(persist_dir=str(storage_dir))
            idx = load_index_from_storage(storage_ctx)
            bm25_retriever = BM25Retriever.from_defaults(
                index=idx, similarity_top_k=top_k_ctx
            )
        except Exception as exc:
            print(
                f"[evaluate] ⚠️  Could not load persisted index: {exc}",
                file=sys.stderr,
            )
            print("[evaluate]     Falling back to node-based BM25.\n", file=sys.stderr)

    # 2) If plugin available but index load failed, build plugin‐BM25 on nodes
    if bm25_retriever is None and _plugin_bm25:
        try:
            bm25_retriever = BM25Retriever.from_defaults(
                nodes=nodes, similarity_top_k=top_k_ctx
            )
        except Exception as exc:
            print(f"[evaluate] ⚠️  Plugin BM25 build failed: {exc}", file=sys.stderr)

    # 3) If still none, but rank_bm25 installed, use BM25Okapi
    if bm25_retriever is None and _has_rank_bm25:
        corpus = [list(KeywordOverlapRetriever._tokenize(n.text)) for n in nodes]
        okapi = BM25Okapi(corpus)

        class OkapiRetriever:
            def retrieve(self, query: str) -> List[TextNodeLike]:
                q_toks = list(KeywordOverlapRetriever._tokenize(query))
                scores = okapi.get_scores(q_toks)
                top_idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k_ctx]
                return [nodes[i] for i in top_idxs]

        bm25_retriever = OkapiRetriever()

    # 4) Fallback: keyword overlap
    kw_retriever = KeywordOverlapRetriever(nodes)

    def get_contexts(question: str) -> List[str]:
        if bm25_retriever is not None:
            # Only pass the query string here
            return [_get_text_from_node(r) for r in bm25_retriever.retrieve(question)]
        # keyword overlap needs top_k explicitly
        return [n.text for n in kw_retriever.retrieve(question, top_k_ctx)]

    # 5) Run through questions
    with open(questions_path, encoding="utf-8") as qf, open(out_path, "w", encoding="utf-8") as outf:
        for raw in tqdm(qf, desc="Evaluating"):
            raw = raw.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            q_text = _extract_question(obj)

            ctxs = get_contexts(q_text)
            q_tokens = KeywordOverlapRetriever._tokenize(q_text)
            hits = sum(bool(q_tokens & KeywordOverlapRetriever._tokenize(ctx)) for ctx in ctxs)
            precision = hits / len(ctxs) if ctxs else 0.0

            outf.write(
                json.dumps(
                    {**obj, "retrieved_contexts": ctxs, "context_precision": precision},
                    ensure_ascii=False,
                )
                + "\n"
            )


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Evaluate RAG retrieval quality.")
    ap.add_argument("--storage_dir", type=Path, required=True,
                    help="Persisted llama_index storage dir")
    ap.add_argument("--nodes_pickle", type=Path, required=True,
                    help="Pickle of raw TextNodeLike nodes")
    ap.add_argument("--questions", type=Path, required=True,
                    help="JSONL file containing questions")
    ap.add_argument("--out", type=Path, required=True,
                    help="Output JSONL report path")
    ap.add_argument("--top_k", type=int, default=5,
                    help="Number of contexts to retrieve")
    return ap.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    evaluate(
        storage_dir=args.storage_dir,
        nodes_pickle=args.nodes_pickle,
        questions_path=args.questions,
        out_path=args.out,
        top_k_ctx=args.top_k,
    )
