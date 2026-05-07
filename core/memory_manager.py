"""
ChromaDB Memory Manager for NeuroDesk AI Multi-Agent System.
Handles persistent vector memory for each agent.
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings


class MemoryManager:
    """Manages ChromaDB collections for agent memory."""

    def __init__(self, agent_id: str, memory_dir: str = "memory"):
        self.agent_id = agent_id
        self.memory_dir = Path(memory_dir)
        self.collection_name = f"{agent_id.lower()}_memory"
        self.client = None
        self.collection = None
        self._ensure_memory_dir()

    def _ensure_memory_dir(self):
        """Ensure memory directory exists."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def _get_client(self) -> chromadb.Client:
        """Get or create ChromaDB client."""
        if self.client is None:
            # Use PersistentClient to ensure data is saved to disk in the memory directory
            self.client = chromadb.PersistentClient(
                path=str(self.memory_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self.client

    def _get_collection(self) -> chromadb.Collection:
        """Get or create collection for this agent."""
        if self.collection is None:
            client = self._get_client()
            try:
                # Try to get existing collection
                self.collection = client.get_collection(self.collection_name)
            except Exception:
                # Create new collection
                self.collection = client.create_collection(self.collection_name)
        return self.collection

    def add(self, document: str, metadata: Optional[Dict[str, Any]] = None, id: Optional[str] = None) -> str:
        """Add a document to memory."""
        collection = self._get_collection()

        if metadata is None:
            metadata = {"timestamp": str(os.urandom(8).hex())}

        if id is None:
            id = str(os.urandom(8).hex())

        collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[id]
        )

        return id

    def query(self, query_text: str, n_results: int = 3) -> Dict[str, List]:
        """Query memory for relevant documents."""
        collection = self._get_collection()
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all documents in memory."""
        collection = self._get_collection()
        results = collection.get()
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])

        return [
            {"id": ids[i], "document": documents[i], "metadata": metadatas[i]}
            for i in range(len(documents))
        ]

    def delete(self, id: str) -> bool:
        """Delete a document by ID."""
        collection = self._get_collection()
        collection.delete(ids=[id])
        return True

    def clear(self) -> bool:
        """Clear all memory for this agent."""
        try:
            collection = self._get_collection()
            collection.delete()
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        collection = self._get_collection()
        count = collection.count()
        return {
            "agent_id": self.agent_id,
            "collection_name": self.collection_name,
            "document_count": count
        }


# Global memory manager instances
_memory_managers = {}


def get_memory_manager(agent_id: str) -> MemoryManager:
    """Get or create a memory manager for an agent."""
    if agent_id not in _memory_managers:
        _memory_managers[agent_id] = MemoryManager(agent_id)
    return _memory_managers[agent_id]


def reset_memory_managers():
    """Reset all memory managers (useful for testing)."""
    global _memory_managers
    _memory_managers = {}
