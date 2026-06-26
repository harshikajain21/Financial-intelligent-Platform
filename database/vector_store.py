"""
Vector Store — embedding-based semantic search for research documents.

Uses ChromaDB (local persistent store) as the default backend.
Documents (research reports, news articles) are embedded and stored for
similarity search by the Research Agent and dashboard.
"""

from __future__ import annotations

from typing import Any

from utils.logger import get_logger

logger = get_logger("VectorStore")


class VectorStore:
    """Persistent vector store backed by ChromaDB.

    Usage::

        store = VectorStore(collection="research_reports")
        store.add(documents=["text..."], ids=["doc-1"], metadatas=[{"ticker": "AAPL"}])
        results = store.query("Apple earnings forecast", n_results=5)
    """

    def __init__(
        self,
        collection: str = "financial_documents",
        persist_directory: str = "./data/chroma_db",
    ) -> None:
        self.collection_name = collection
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _init(self) -> None:
        if self._client is not None:
            return
        try:
            import chromadb  # type: ignore
            from chromadb.config import Settings  # type: ignore

            self._client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "ChromaDB collection '%s' loaded from '%s'.",
                self.collection_name,
                self.persist_directory,
            )
        except ImportError as exc:
            raise ImportError(
                "chromadb not installed. Run: pip install chromadb"
            ) from exc

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    def add(
        self,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to the vector store.

        Args:
            documents: List of raw text strings to embed and store.
            ids:       Unique IDs for each document.
            metadatas: Optional metadata dicts associated with each document.
        """
        self._init()
        self._collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas or [{} for _ in documents],
        )
        logger.info("Added %d documents to collection '%s'.", len(documents), self.collection_name)

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search over stored documents.

        Args:
            query_text: Natural language query string.
            n_results:  Maximum number of results to return.
            where:      Optional metadata filter (ChromaDB where clause).

        Returns:
            List of dicts with 'id', 'document', 'metadata', and 'distance'.
        """
        self._init()
        kwargs: dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)
        items = []
        for doc_id, doc, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            items.append({"id": doc_id, "document": doc, "metadata": meta, "distance": dist})
        return items

    def delete(self, ids: list[str]) -> None:
        """Remove documents by ID."""
        self._init()
        self._collection.delete(ids=ids)
        logger.info("Deleted %d documents from collection '%s'.", len(ids), self.collection_name)

    def count(self) -> int:
        """Return total number of documents in the collection."""
        self._init()
        return self._collection.count()
