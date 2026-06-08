"""
Embedding & Retrieval Module
Integrates chunked documents into ChromaDB using all-MiniLM-L6-v2 embeddings.
Provides semantic search with top-k retrieval and structured result formatting.

Pipeline Stage: Embedding + Vector Store → Retrieval
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import chromadb
from sentence_transformers import SentenceTransformer


class VectorStore:
    """Manages ChromaDB vector store for semantic retrieval."""

    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        collection_name: str = "restaurant_chunks",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the vector store with local persistent ChromaDB.

        Args:
            persist_dir: Directory for ChromaDB persistence
            collection_name: Name of the collection to create/use
            model_name: SentenceTransformer model identifier
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.model_name = model_name

        # Initialize local persistent ChromaDB client (ChromaDB 0.4+ API)
        # PersistentClient stores data locally in the specified path
        self.client = chromadb.PersistentClient(path=self.persist_dir)

        # Load embedding model (downloads on first run)
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"✓ Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}\n")

    def get_or_create_collection(self) -> chromadb.Collection:
        """
        Get existing collection or create new one.
        ChromaDB collections store vectors with associated metadata.

        Returns:
            ChromaDB collection object
        """
        # get_or_create_collection() handles both existing and new collections
        # If collection exists, returns it; otherwise creates with given name
        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine distance for similarity
        )
        return collection

    def add_chunks_to_vector_store(self, chunks_file: str) -> int:
        """
        Load chunks from JSON and ingest into ChromaDB.
        Embeds each chunk and stores with metadata.

        Args:
            chunks_file: Path to chunks.json from chunking.py

        Returns:
            Number of chunks successfully added
        """
        print(f"{'='*60}")
        print("STEP 1: Loading chunks from JSON...")
        print(f"{'='*60}\n")

        # Load chunks from JSON output of chunking.py
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        print(f"Loaded {len(chunks)} chunks\n")

        collection = self.get_or_create_collection()
        print(f"{'='*60}")
        print("STEP 2: Embedding and upserting chunks...")
        print(f"{'='*60}\n")

        # Process chunks in batches for efficiency
        batch_size = 32
        added_count = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            batch_ids = []
            batch_texts = []
            batch_embeddings = []
            batch_metadatas = []

            for chunk in batch:
                # Create unique ID: document_name + chunk_index
                chunk_id = f"{chunk['document'].replace('.txt', '')}_{chunk['chunk_id']}"
                batch_ids.append(chunk_id)
                batch_texts.append(chunk["text"])

                # Preserve metadata for source attribution
                metadata = {
                    "document": chunk["document"],
                    "chunk_id": chunk["chunk_id"],
                    "char_count": chunk["char_count"],
                    "word_count": chunk["word_count"]
                }
                batch_metadatas.append(metadata)

            # Embed all texts in batch using SentenceTransformer
            # Returns shape (batch_size, 384) for all-MiniLM-L6-v2
            batch_embeddings = self.model.encode(
                batch_texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            # Upsert to ChromaDB: creates new records or updates existing ones
            # (based on ID matching)
            collection.upsert(
                ids=batch_ids,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                documents=batch_texts
            )

            added_count += len(batch)
            progress = min(i + batch_size, len(chunks))
            print(f"Processed {progress}/{len(chunks)} chunks...")

        print(f"\n✓ Successfully added {added_count} chunks to vector store\n")
        return added_count

    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = 3,
        distance_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Semantic search: query vector store and return top-k relevant chunks.

        Args:
            query: Plain-language query string
            top_k: Number of results to return (default: 3 from planning.md)
            distance_threshold: Optional filter (only return if distance < threshold)

        Returns:
            List of dicts with keys:
                - text: Chunk content
                - metadata: {document, chunk_id, char_count, word_count}
                - distance: Cosine distance score (0=perfect match, 2=opposite)
        """
        collection = self.get_or_create_collection()

        # Embed the query using the same model
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        # Query ChromaDB: query() searches the collection using nearest neighbors
        # Returns the top_k most similar chunks based on embedding distance
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        # Format results for return
        formatted_results = []

        if results and results["documents"] and len(results["documents"]) > 0:
            for i, doc_text in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]

                # Skip if distance exceeds threshold
                if distance_threshold and distance > distance_threshold:
                    continue

                result_obj = {
                    "text": doc_text,
                    "metadata": metadata,
                    "distance": distance
                }
                formatted_results.append(result_obj)

        return formatted_results


def verify_retrieval(vector_store: VectorStore, test_queries: Optional[List[str]] = None):
    """
    Test retrieval with sample queries from planning.md evaluation set.
    Prints results with warnings for weak matches (distance > 0.6).

    Args:
        vector_store: Initialized VectorStore instance
        test_queries: Optional custom queries; uses defaults if None
    """
    if test_queries is None:
        # Sample queries from planning.md evaluation plan
        test_queries = [
            "What is the expected tipping etiquette when sitting at the bar?",
            "What are the main ingredients and characteristics of Pho?",
            "What types of dining establishments are available on the East Side?",
            "What is Banh Mi and why is it good for students?",
            "What makes Southeast Asian cuisine in St. Paul authentic?"
        ]

    print(f"\n{'='*60}")
    print("VERIFICATION: Testing Semantic Retrieval")
    print(f"{'='*60}\n")

    for query_idx, query in enumerate(test_queries, 1):
        print(f"Query {query_idx}: {query}\n")

        results = vector_store.retrieve_relevant_chunks(query, top_k=3)

        if not results:
            print("⚠ No results found\n")
            continue

        for result_idx, result in enumerate(results, 1):
            distance = result["distance"]
            metadata = result["metadata"]
            text = result["text"]

            # Flag weak matches (distance > 0.6 in cosine space)
            quality_marker = " ⚠ WEAK MATCH (distance > 0.6)" if distance > 0.6 else ""

            print(f"  Result {result_idx}:{quality_marker}")
            print(f"    Document: {metadata['document']}")
            print(f"    Chunk ID: {metadata['chunk_id']}")
            print(f"    Distance: {distance:.4f}")
            print(f"    Text preview: {text[:150]}...")
            print()

        print(f"{'-'*60}\n")


if __name__ == "__main__":
    # Configuration
    CHUNKS_FILE = "chunks.json"
    PERSIST_DIR = "./chroma_db"
    COLLECTION_NAME = "restaurant_chunks"

    # Initialize vector store
    print("\nInitializing Vector Store...\n")
    vector_store = VectorStore(
        persist_dir=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
        model_name="all-MiniLM-L6-v2"
    )

    # Ingest chunks (only if chunks.json exists)
    if os.path.exists(CHUNKS_FILE):
        chunk_count = vector_store.add_chunks_to_vector_store(CHUNKS_FILE)
    else:
        print(f"⚠ {CHUNKS_FILE} not found. Skipping ingestion.\n")
        chunk_count = 0

    # Run verification test
    verify_retrieval(vector_store)

    # Quick summary
    print(f"{'='*60}")
    print(f"Vector store ready for retrieval")
    print(f"Location: {PERSIST_DIR}")
    print(f"Model: all-MiniLM-L6-v2")
    print(f"Chunks ingested: {chunk_count}")
    print(f"{'='*60}\n")
