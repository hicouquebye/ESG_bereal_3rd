"""Chroma 벡터 DB 검색 스크립트 (Semantic + BM25 + 로컬 Reranker).

Semantic 후보를 넓게 뽑고(BGE 임베딩), 같은 페이지의 본문/표/그림 청크 전체를 corpus로 삼아
BM25 점수를 다시 계산한 뒤 정규화해 가중합을 만든다. 마지막으로 CrossEncoder reranker를 적용하고
동일 페이지(`doc_id`, `page_no`)에 해당하는 결과는 하나만 노출한다.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from sentence_transformers import CrossEncoder, SentenceTransformer

try:
    from kiwipiepy import Kiwi
except Exception as exc:  # pylint: disable=broad-except
    raise RuntimeError("키워드 검색을 위해 kiwipiepy가 필요합니다. 'pip install kiwipiepy' 후 다시 실행하세요.") from exc

KIWI = Kiwi()

try:
    RERANKER = CrossEncoder("BAAI/bge-reranker-v2-m3")
except Exception:  # pylint: disable=broad-except
    RERANKER = None

from pathlib import Path
VECTOR_DB_DIR = str(Path(__file__).resolve().parent / "vector_db")
COLLECTIONS = ["esg_pages", "esg_chunks"]
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
MAX_KEYWORD_DOCS = 2000
RERANK_CANDIDATES = 50
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4


@dataclass
class Candidate:
    collection: str
    document: str
    metadata: Dict
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    combined_score: float = 0.0
    rerank_score: float | None = None


def tokenize(text: str) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    return [token.form for token in KIWI.tokenize(text) if token.form.strip()]


def bm25_scores(corpus_tokens: List[List[str]], query_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> List[float]:
    if not corpus_tokens:
        return []
    N = len(corpus_tokens)
    doc_lens = [len(tokens) for tokens in corpus_tokens]
    avgdl = sum(doc_lens) / max(N, 1)
    df: Counter[str] = Counter()
    for tokens in corpus_tokens:
        for term in set(tokens):
            df[term] += 1
    scores = []
    for tokens, doc_len in zip(corpus_tokens, doc_lens):
        freq = Counter(tokens)
        score = 0.0
        for term in query_tokens:
            if term not in df:
                continue
            idf = math.log(1 + (N - df[term] + 0.5) / (df[term] + 0.5))
            tf = freq.get(term, 0)
            if tf == 0:
                continue
            denom = tf + k1 * (1 - b + b * doc_len / avgdl)
            score += idf * ((tf * (k1 + 1)) / denom)
        scores.append(score)
    return scores


def load_collections(client: chromadb.PersistentClient):
    collections = {}
    for name in COLLECTIONS:
        try:
            collections[name] = client.get_collection(name)
        except Exception:
            continue
    return collections


def semantic_search(collections, model, query: str, top_k: int, metadata_filter: Dict | None) -> List[Candidate]:
    query_vec = model.encode([query]).tolist()
    results: List[Candidate] = []
    for collection in collections.values():
        if metadata_filter:
            resp = collection.query(query_embeddings=query_vec, n_results=top_k, where=metadata_filter)
        else:
            resp = collection.query(query_embeddings=query_vec, n_results=top_k)
        docs = resp.get("documents") or []
        if not docs:
            continue
        for doc, meta, dist in zip(docs[0], resp["metadatas"][0], resp["distances"][0]):
            sim = 1.0 - float(dist)
            results.append(Candidate(collection.name, doc, meta or {}, semantic_score=sim))
    results.sort(key=lambda cand: cand.semantic_score, reverse=True)
    return results[:top_k]


def keyword_search_full(collections, query: str, top_k: int, metadata_filter: Dict | None) -> List[Candidate]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    docs_all = []
    for collection in collections.values():
        data = collection.get(include=["documents", "metadatas"], limit=MAX_KEYWORD_DOCS, where=metadata_filter)
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        for text, meta in zip(docs, metas):
            docs_all.append((collection.name, text, meta or {}))
    corpus_tokens = [tokenize(text) for _, text, _ in docs_all]
    scores = bm25_scores(corpus_tokens, query_tokens)
    ranked = sorted(zip(docs_all, scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [Candidate(name, text, meta, keyword_score=score) for (name, text, meta), score in ranked]


def aggregate_page_text(cand: Candidate, chunk_collection) -> str:
    texts = [cand.document]
    if not chunk_collection:
        return " ".join(texts)
    doc_id = cand.metadata.get("doc_id")
    page_id = cand.metadata.get("page_id")
    if doc_id is None or page_id is None:
        return " ".join(texts)
    filters = {"$and": [{"doc_id": doc_id}, {"page_id": page_id}]}
    data = chunk_collection.get(where=filters, include=["documents"])
    docs = data.get("documents") or []
    for group in docs:
        if isinstance(group, list):
            texts.extend(group)
        else:
            texts.append(group)
    return " ".join(texts)


def keyword_scores_for_candidates(candidates: List[Candidate], query: str, chunk_collection) -> None:
    query_tokens = tokenize(query)
    corpus_tokens = [tokenize(aggregate_page_text(cand, chunk_collection)) for cand in candidates]
    scores = bm25_scores(corpus_tokens, query_tokens)
    for cand, score in zip(candidates, scores):
        cand.keyword_score = score


def normalize(scores: List[float]) -> List[float]:
    if not scores:
        return []
    mn, mx = min(scores), max(scores)
    if mx - mn < 1e-8:
        return [0.5] * len(scores)
    return [(s - mn) / (mx - mn) for s in scores]


def apply_combined_score(candidates: List[Candidate], use_sem: bool, use_kw: bool) -> None:
    sem_norm = normalize([cand.semantic_score for cand in candidates]) if use_sem else [0.0] * len(candidates)
    kw_norm = normalize([cand.keyword_score for cand in candidates]) if use_kw else [0.0] * len(candidates)
    for cand, s_norm, k_norm in zip(candidates, sem_norm, kw_norm):
        if use_sem and not use_kw:
            cand.combined_score = cand.semantic_score
        elif use_kw and not use_sem:
            cand.combined_score = cand.keyword_score
        else:
            cand.combined_score = SEMANTIC_WEIGHT * s_norm + KEYWORD_WEIGHT * k_norm


def rerank_candidates(query: str, candidates: List[Candidate], limit: int) -> List[Candidate]:
    if not candidates:
        return []
    if RERANKER is None:
        return sorted(candidates, key=lambda c: c.combined_score, reverse=True)[:limit]
    pool = sorted(candidates, key=lambda c: c.combined_score, reverse=True)
    subset = pool[: min(RERANK_CANDIDATES, max(limit * 2, limit))]
    pairs = [[query, cand.document] for cand in subset]
    scores = RERANKER.predict(pairs, batch_size=16)
    for cand, score in zip(subset, scores):
        cand.rerank_score = float(score)
    reranked = sorted(subset, key=lambda c: c.rerank_score or 0.0, reverse=True)[:limit]
    return reranked


def format_result(rank: int, cand: Candidate, show_scores: bool) -> None:
    meta = cand.metadata
    preview = cand.document[:200].replace("\n", " ")
    print(f"[Rank {rank}] ({cand.collection}) Score: {cand.combined_score:.4f}")
    print(f"   Source: {meta.get('company_name')} ({meta.get('report_year')}) | p.{meta.get('page_no')} | chunk={meta.get('chunk_index')}")
    if show_scores:
        rerank_val = "nan" if cand.rerank_score is None else f"{cand.rerank_score:.4f}"
        print(f"   semantic={cand.semantic_score:.4f}, keyword={cand.keyword_score:.4f}, combined={cand.combined_score:.4f}, rerank={rerank_val}")
    print(f"   Content: {preview}...")
    print("-" * 80)


def build_metadata_filter(filter_company: str | None, filter_year: int | None) -> Dict | None:
    conditions = []
    if filter_company:
        conditions.append({"company_name": filter_company})
    if filter_year:
        conditions.append({"report_year": filter_year})
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}

def build_chroma_client(
    vector_db_path: str | Path | None = None,
    chroma_host: Optional[str] = None,
    chroma_port: Optional[int] = None,
    verbose: bool = True,
):
    """
    원격 Chroma가 설정되어 있으면 HttpClient를 우선 사용하고,
    실패하거나 미설정이면 로컬 PersistentClient로 fallback한다.
    """
    env_host = os.getenv("CHROMA_HOST")
    env_port = os.getenv("CHROMA_PORT")
    host = chroma_host or env_host

    port: Optional[int] = chroma_port
    if port is None and env_port:
        try:
            port = int(env_port)
        except ValueError:
            port = None
    if port is None:
        port = 8000

    if host:
        try:
            if verbose:
                print(f"🌐 Chroma HttpClient 연결 시도: {host}:{port}")
            return chromadb.HttpClient(host=host, port=port), f"http://{host}:{port}"
        except Exception as exc:
            if verbose:
                print(f"⚠️ 원격 Chroma 연결 실패, 로컬로 fallback: {exc}")

    db_dir = Path(vector_db_path or VECTOR_DB_DIR)
    if verbose:
        print(f"📁 Chroma PersistentClient 사용: {db_dir}")
    return chromadb.PersistentClient(path=str(db_dir)), str(db_dir)


def search_vector_db(
    query: str,
    top_k: int = 5,
    mode: str = "hybrid",
    semantic_top_k: int = 40,
    show_scores: bool = False,
    filter_company: str | None = None,
    filter_year: int | None = None,
    vector_db_path: str | Path | None = None,
    chroma_host: str | None = None,
    chroma_port: int | None = None,
    verbose: bool = True,
):
    client, target = build_chroma_client(
        vector_db_path=vector_db_path,
        chroma_host=chroma_host,
        chroma_port=chroma_port,
        verbose=verbose,
    )
    if verbose:
        print(f"🔎 Query='{query}' | Mode={mode} | Top {top_k} | Target={target}")
    collections = load_collections(client)
    if not collections:
        if verbose:
            print("❌ 사용 가능한 컬렉션이 없습니다.")
        return []

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    chunk_collection = collections.get("esg_chunks")
    metadata_filter = build_metadata_filter(filter_company, filter_year)

    if mode == "semantic":
        candidates = semantic_search(collections, model, query, max(top_k, semantic_top_k), metadata_filter)
        apply_combined_score(candidates, use_sem=True, use_kw=False)
    elif mode == "keyword":
        candidates = keyword_search_full(collections, query, top_k, metadata_filter)
        apply_combined_score(candidates, use_sem=False, use_kw=True)
    else:
        sem_candidates = semantic_search(collections, model, query, semantic_top_k, metadata_filter)
        if not sem_candidates:
            if verbose:
                print("검색 결과가 없습니다 (semantic).")
            return []
        keyword_scores_for_candidates(sem_candidates, query, chunk_collection)
        apply_combined_score(sem_candidates, use_sem=True, use_kw=True)
        candidates = sem_candidates

    rerank_limit = max(top_k * 5, top_k)
    reranked = rerank_candidates(query, candidates, rerank_limit)
    if not reranked:
        if verbose:
            print("검색 결과가 없습니다.")
        return []

    seen_pages = set()
    deduped: List[Candidate] = []
    for cand in reranked:
        key = (cand.metadata.get("doc_id"), cand.metadata.get("page_no"))
        if key in seen_pages:
            continue
        seen_pages.add(key)
        deduped.append(cand)
        if len(deduped) >= top_k:
            break

    if not deduped:
        if verbose:
            print("검색 결과가 없습니다.")
        return []

    results_payload = []
    for idx, cand in enumerate(deduped, start=1):
        if verbose:
            format_result(idx, cand, show_scores)
        page_text = aggregate_page_text(cand, chunk_collection)
        payload = {
            "content": page_text or cand.document,
            "metadata": dict(cand.metadata or {}),
            "scores": {
                "semantic": cand.semantic_score,
                "keyword": cand.keyword_score,
                "combined": cand.combined_score,
                "rerank": cand.rerank_score,
            },
        }
        results_payload.append(payload)

    return results_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chroma 기반 ESG Vector 검색기")
    parser.add_argument("query", type=str, help="검색 질의어")
    parser.add_argument("--top-k", type=int, default=5, help="출력할 결과 수")
    parser.add_argument(
        "--mode",
        choices=("semantic", "keyword", "hybrid"),
        default="hybrid",
        help="검색 방식 선택",
    )
    parser.add_argument("--semantic-top-k", type=int, default=40, help="hybrid 모드에서 semantic 후보 수")
    parser.add_argument("--show-scores", action="store_true", help="각 결과의 내부 점수 출력")
    parser.add_argument("--company", type=str, default=None, help="회사명 필터")
    parser.add_argument("--year", type=int, default=None, help="보고서 연도 필터")
    parser.add_argument("--chroma-host", type=str, default=None, help="원격 Chroma host")
    parser.add_argument("--chroma-port", type=int, default=None, help="원격 Chroma port")
    args = parser.parse_args()

    search_vector_db(
        args.query,
        top_k=args.top_k,
        mode=args.mode,
        semantic_top_k=args.semantic_top_k,
        show_scores=args.show_scores,
        filter_company=getattr(args, "company", None),
        filter_year=getattr(args, "year", None),
        chroma_host=getattr(args, "chroma_host", None),
        chroma_port=getattr(args, "chroma_port", None),
    )
