"""Persistent Chroma vector database for InsightIQ evidence retrieval.

Embeddings are built ONCE and persisted to artifacts/chroma/.
On subsequent runs, if the collection already has documents, indexing is skipped.
Pass force_reindex=True to rebuild from scratch.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from insightiq.core.contracts import EvidenceItem
from insightiq.knowledge.evidence_store import KnowledgeDocument


@dataclass(frozen=True)
class VectorDbStatus:
    backend: str
    persist_path: str
    collection: str
    documents_indexed: int
    used_chroma: bool


class HashEmbeddingFunction:
    """Small local embedding function for Chroma.

    This keeps GitHub deployments simple and avoids a GPU dependency. The vector
    DB is real Chroma persistence; the embedding model can later be replaced by
    sentence-transformers or Hugging Face embeddings.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def name(self) -> str:
        return "insightiq_hash_embeddings"

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def embed_query(self, input: str | list[str]) -> list[float] | list[list[float]]:
        if isinstance(input, str):
            return self._embed(input)
        return [self._embed(text) for text in input]

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[idx] += sign
        norm = np.linalg.norm(vector)
        if norm:
            vector = vector / norm
        return vector.tolist()


DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class HFEmbeddingFunction:
    """Real semantic embeddings via the Hugging Face Inference API.

    Uses a sentence-transformer model (default all-MiniLM-L6-v2, 384-dim to match
    the persisted Chroma collection). Embeds in batches for throughput and falls
    back to the deterministic hash embeddings if the token is missing or the API
    is unreachable, so retrieval never crashes.
    """

    def __init__(
        self,
        model: str | None = None,
        token: str | None = None,
        dimensions: int = 384,
        batch_size: int = 64,
    ) -> None:
        self.model = model or os.getenv("INSIGHTIQ_EMBED_MODEL", DEFAULT_EMBED_MODEL)
        self.token = token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.dimensions = dimensions
        self.batch_size = batch_size
        self._hash = HashEmbeddingFunction(dimensions)
        self._client = None
        self._ok = bool(self.token)

    def name(self) -> str:
        return f"hf::{self.model}"

    def _get_client(self) -> Any:
        if self._client is None:
            from huggingface_hub import InferenceClient

            self._client = InferenceClient(token=self.token, timeout=60)
        return self._client

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._embed_many(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self._embed_many(input)

    def embed_query(self, input: str | list[str]) -> list[float] | list[list[float]]:
        if isinstance(input, str):
            return self._embed_many([input])[0]
        return self._embed_many(input)

    def _embed_many(self, texts: list[str]) -> list[list[float]]:
        if not self._ok or not texts:
            return self._hash(texts)
        try:
            client = self._get_client()
            out: list[list[float]] = []
            for start in range(0, len(texts), self.batch_size):
                chunk = [str(t)[:512] for t in texts[start : start + self.batch_size]]
                vecs = np.asarray(client.feature_extraction(chunk, model=self.model), dtype=np.float32)
                if vecs.ndim == 1:  # single item returned flat
                    vecs = vecs.reshape(1, -1)
                if vecs.ndim == 3:  # token-level embeddings → mean pool
                    vecs = vecs.mean(axis=1)
                for vec in vecs:
                    norm = np.linalg.norm(vec)
                    out.append((vec / norm if norm else vec).tolist())
            return out
        except Exception:
            # First failure disables HF for the rest of this process — stay on the
            # deterministic fallback so the whole corpus shares one vector space.
            self._ok = False
            return self._hash(texts)


def _make_embedding_function() -> Any:
    """Pick HF semantic embeddings when a token is configured, else hash fallback."""
    use_hf = os.getenv("INSIGHTIQ_USE_HF_EMBEDDINGS", "true").lower() == "true"
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if use_hf and token:
        return HFEmbeddingFunction()
    return HashEmbeddingFunction()


class ChromaEvidenceStore:
    def __init__(
        self,
        persist_path: Path,
        collection_name: str = "insightiq_evidence",
        embedding_function: Any | None = None,
    ) -> None:
        self.persist_path = persist_path
        self.collection_name = collection_name
        self.embedding_function = embedding_function or _make_embedding_function()
        self._fallback_docs: list[KnowledgeDocument] = []
        self._client = None
        self._collection = None
        try:
            import chromadb

            self._client = chromadb.PersistentClient(path=str(persist_path))
            self._collection = self._get_or_create_collection()
        except Exception:
            self._client = None
            self._collection = None

    def _get_or_create_collection(self) -> Any:
        """Open the collection, recreating it if a previous run used a different
        embedding function (Chroma rejects mixed embedding spaces in one collection)."""
        try:
            return self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "InsightIQ product decision evidence"},
            )
        except Exception:
            try:
                self._client.delete_collection(self.collection_name)
            except Exception:
                pass
            return self._client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "InsightIQ product decision evidence"},
            )

    @property
    def used_chroma(self) -> bool:
        return self._collection is not None

    def reset(self) -> None:
        if self._client is not None:
            try:
                self._client.delete_collection(self.collection_name)
            except Exception:
                pass
            self._collection = self._get_or_create_collection()
        self._fallback_docs = []

    def _fingerprint(self, documents: list[KnowledgeDocument]) -> str:
        """Stable hash of embedding model + document count + first/last doc text.

        The embedding model name is included so switching embeddings (e.g. hash →
        HF semantic) forces a re-index into the new vector space."""
        model = self.embedding_function.name() if hasattr(self.embedding_function, "name") else "unknown"
        sample = f"{model}|{len(documents)}|{documents[0].text[:80] if documents else ''}|{documents[-1].text[:80] if documents else ''}"
        return hashlib.sha1(sample.encode()).hexdigest()

    def _fingerprint_path(self) -> Path:
        return Path(self.persist_path) / "index_fingerprint.json"

    def _load_fingerprint(self) -> str | None:
        p = self._fingerprint_path()
        if p.exists():
            return json.loads(p.read_text()).get("fingerprint")
        return None

    def _save_fingerprint(self, fingerprint: str) -> None:
        self._fingerprint_path().parent.mkdir(parents=True, exist_ok=True)
        self._fingerprint_path().write_text(json.dumps({"fingerprint": fingerprint}))

    def index_documents(self, documents: list[KnowledgeDocument], reset: bool = True, force_reindex: bool = False) -> VectorDbStatus:
        self._fallback_docs = list(documents)

        if self._collection is not None and documents:
            current_fp = self._fingerprint(documents)
            saved_fp = self._load_fingerprint()
            already_indexed = (
                not force_reindex
                and saved_fp == current_fp
                and self._collection.count() > 0
            )
            if already_indexed:
                # Embeddings already exist — skip re-indexing
                return VectorDbStatus(
                    backend="chroma",
                    persist_path=str(self.persist_path),
                    collection=self.collection_name,
                    documents_indexed=self._collection.count(),
                    used_chroma=True,
                )
            # New data or forced reindex — rebuild
            if reset:
                self.reset()
            ids = [_stable_id(doc, idx) for idx, doc in enumerate(documents)]
            self._collection.upsert(
                ids=ids,
                documents=[doc.text for doc in documents],
                metadatas=[_clean_metadata({**doc.metadata, "source": doc.source, "title": doc.title}) for doc in documents],
            )
            self._save_fingerprint(current_fp)
        elif reset:
            self.reset()

        return VectorDbStatus(
            backend="chroma" if self.used_chroma else "in_memory_fallback",
            persist_path=str(self.persist_path),
            collection=self.collection_name,
            documents_indexed=len(documents),
            used_chroma=self.used_chroma,
        )

    def search(self, query: str, top_k: int = 8, filters: dict[str, Any] | None = None) -> list[EvidenceItem]:
        filters = {key: value for key, value in (filters or {}).items() if value is not None}
        if self._collection is not None:
            try:
                where = _clean_metadata(filters) if filters else None
                result = self._collection.query(query_texts=[query], n_results=top_k, where=where)
                docs = result.get("documents", [[]])[0]
                metadatas = result.get("metadatas", [[]])[0]
                distances = result.get("distances", [[]])[0] if result.get("distances") else [0.0] * len(docs)
                return [
                    EvidenceItem(
                        source=str(meta.get("source", "chroma")),
                        title=str(meta.get("title", "Evidence")),
                        summary=doc,
                        confidence=round(1 / (1 + float(distance)), 4),
                        metadata=dict(meta),
                    )
                    for doc, meta, distance in zip(docs, metadatas, distances)
                ]
            except Exception:
                return self._fallback_search(query, top_k, filters)
        return self._fallback_search(query, top_k, filters)

    def _fallback_search(self, query: str, top_k: int, filters: dict[str, Any]) -> list[EvidenceItem]:
        terms = set(query.lower().split())
        scored = []
        for doc in self._fallback_docs:
            if any(doc.metadata.get(key) != value for key, value in filters.items()):
                continue
            score = len(terms.intersection(doc.text.lower().split())) / max(len(terms), 1)
            scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            EvidenceItem(
                source=doc.source,
                title=doc.title,
                summary=doc.text[:500],
                confidence=round(float(score), 4),
                metadata=doc.metadata,
            )
            for score, doc in scored[:top_k]
        ]


def documents_from_frames(frames: dict[str, pd.DataFrame]) -> list[KnowledgeDocument]:
    from insightiq.knowledge.evidence_store import EvidenceStore

    return EvidenceStore.from_frames(frames).documents


def _stable_id(doc: KnowledgeDocument, idx: int) -> str:
    digest = hashlib.sha1(f"{doc.source}|{doc.title}|{idx}|{doc.text[:120]}".encode("utf-8")).hexdigest()
    return digest


def _clean_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    clean: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean
