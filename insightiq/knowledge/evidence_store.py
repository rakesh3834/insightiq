"""Lightweight evidence retrieval.

This module provides a lightweight in-memory retrieval fallback. The deployment
path uses Chroma in `insightiq/knowledge/chroma_store.py`; this fallback keeps
tests and local diagnostics simple.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from insightiq.core.contracts import EvidenceItem

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:
    TfidfVectorizer = None
    cosine_similarity = None


@dataclass(frozen=True)
class KnowledgeDocument:
    source: str
    title: str
    text: str
    metadata: dict[str, Any]


class EvidenceStore:
    def __init__(self, documents: list[KnowledgeDocument]) -> None:
        self.documents = documents
        self._vectorizer = None
        self._matrix = None
        if TfidfVectorizer is not None and documents:
            self._vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
            self._matrix = self._vectorizer.fit_transform([doc.text for doc in documents])

    @classmethod
    def from_frames(cls, frames: dict[str, pd.DataFrame]) -> "EvidenceStore":
        docs: list[KnowledgeDocument] = []
        docs.extend(_review_docs(frames.get("reviews", pd.DataFrame()), frames.get("products", pd.DataFrame())))
        docs.extend(_release_docs(frames.get("release_notes", pd.DataFrame())))
        docs.extend(_incident_docs(frames.get("engineering_incidents", pd.DataFrame())))
        docs.extend(_experiment_docs(frames.get("experiments", pd.DataFrame())))
        docs.extend(_generic_docs(frames.get("product_documentation", pd.DataFrame()), "product_documentation", "doc_id", "title", "content"))
        docs.extend(_generic_docs(frames.get("business_glossary", pd.DataFrame()), "business_glossary", "term", "term", "definition"))
        return cls(docs)

    def search(self, query: str, top_k: int = 8, filters: dict[str, Any] | None = None) -> list[EvidenceItem]:
        candidates = self._filtered_documents(filters or {})
        if not candidates:
            return []
        if self._vectorizer is None or self._matrix is None or cosine_similarity is None:
            return [_to_evidence(doc, 0.5) for doc in candidates[:top_k]]

        candidate_indexes = [self.documents.index(doc) for doc in candidates]
        query_vector = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self._matrix[candidate_indexes]).ravel()
        ranked = sorted(zip(candidates, scores), key=lambda item: item[1], reverse=True)[:top_k]
        return [_to_evidence(doc, float(score)) for doc, score in ranked]

    def _filtered_documents(self, filters: dict[str, Any]) -> list[KnowledgeDocument]:
        if not filters:
            return self.documents
        docs = []
        for doc in self.documents:
            include = True
            for key, value in filters.items():
                if value is not None and doc.metadata.get(key) != value:
                    include = False
                    break
            if include:
                docs.append(doc)
        return docs


def _to_evidence(doc: KnowledgeDocument, score: float) -> EvidenceItem:
    return EvidenceItem(
        source=doc.source,
        title=doc.title,
        summary=doc.text[:500],
        confidence=round(score, 4),
        metadata=doc.metadata,
    )


def _review_docs(reviews: pd.DataFrame, products: pd.DataFrame) -> list[KnowledgeDocument]:
    if reviews.empty:
        return []
    product_cols = [col for col in ["product_id", "category", "brand", "product_name"] if col in products.columns]
    enriched = reviews.copy()
    if product_cols:
        enriched = enriched.merge(products[product_cols], on="product_id", how="left")
    docs = []
    for _, row in enriched.head(5000).iterrows():
        docs.append(
            KnowledgeDocument(
                source="reviews",
                title=f"Review {row.get('review_id', '')}",
                text=f"Rating {row.get('rating')}: {row.get('review_text', '')}",
                metadata={
                    "product_id": row.get("product_id"),
                    "category": row.get("category"),
                    "brand": row.get("brand"),
                    "date": str(row.get("review_date", ""))[:10],
                },
            )
        )
    return docs


def _release_docs(releases: pd.DataFrame) -> list[KnowledgeDocument]:
    docs = []
    for _, row in releases.iterrows():
        docs.append(
            KnowledgeDocument(
                source="release_notes",
                title=str(row.get("title", row.get("release_id", ""))),
                text=f"{row.get('release_type', '')} in {row.get('feature_area', '')}: {row.get('description', '')}. Expected metric: {row.get('expected_metric', '')}",
                metadata={"feature_area": row.get("feature_area"), "date": row.get("release_date"), "release_id": row.get("release_id")},
            )
        )
    return docs


def _incident_docs(incidents: pd.DataFrame) -> list[KnowledgeDocument]:
    docs = []
    for _, row in incidents.iterrows():
        docs.append(
            KnowledgeDocument(
                source="engineering_incidents",
                title=str(row.get("incident_id", "")),
                text=f"{row.get('severity', '')} incident in {row.get('affected_area', '')}: {row.get('customer_impact', '')}. Resolution: {row.get('resolution', '')}",
                metadata={"feature_area": row.get("affected_area"), "date": row.get("incident_date"), "severity": row.get("severity")},
            )
        )
    return docs


def _experiment_docs(experiments: pd.DataFrame) -> list[KnowledgeDocument]:
    docs = []
    for _, row in experiments.iterrows():
        docs.append(
            KnowledgeDocument(
                source="experiments",
                title=str(row.get("experiment_id", "")),
                text=f"Experiment on {row.get('feature_area', '')} for {row.get('primary_metric', '')}: lift {row.get('lift_pct')}%, p-value {row.get('p_value')}, decision {row.get('decision')}",
                metadata={"feature_area": row.get("feature_area"), "metric": row.get("primary_metric"), "experiment_id": row.get("experiment_id")},
            )
        )
    return docs


def _generic_docs(frame: pd.DataFrame, source: str, id_col: str, title_col: str, text_col: str) -> list[KnowledgeDocument]:
    docs = []
    if frame.empty:
        return docs
    for _, row in frame.iterrows():
        docs.append(
            KnowledgeDocument(
                source=source,
                title=str(row.get(title_col, row.get(id_col, ""))),
                text=str(row.get(text_col, "")),
                metadata={"id": row.get(id_col)},
            )
        )
    return docs
