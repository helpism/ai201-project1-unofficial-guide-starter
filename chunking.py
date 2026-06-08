"""
Document Chunking Script
Implements the chunking strategy from planning.md:
- Chunk size: 800 characters
- Overlap: 150 characters
- Input: Text files from documents/ folder
- Output: Cleaned chunks with metadata
"""

import os
import json
from pathlib import Path
from typing import List, Tuple, Dict


def load_documents(docs_dir: str) -> Dict[str, str]:
    """
    Load all .txt files from the documents directory.

    Args:
        docs_dir: Path to documents folder

    Returns:
        Dictionary with filename: content pairs
    """
    documents = {}
    docs_path = Path(docs_dir)

    if not docs_path.exists():
        raise FileNotFoundError(f"Documents directory not found: {docs_dir}")

    txt_files = sorted(docs_path.glob("*.txt"))

    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {docs_dir}")

    for file_path in txt_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                documents[file_path.name] = content
                print(f"✓ Loaded: {file_path.name} ({len(content)} chars)")
        except Exception as e:
            print(f"✗ Error loading {file_path.name}: {e}")

    return documents


def clean_text(text: str) -> str:
    """
    Clean document text by normalizing whitespace and removing artifacts.

    Args:
        text: Raw document text

    Returns:
        Cleaned text
    """
    # Replace multiple newlines with single newline
    lines = text.split("\n")
    cleaned_lines = [line.rstrip() for line in lines]
    cleaned_text = "\n".join(cleaned_lines)

    # Replace multiple spaces with single space (but preserve newlines)
    cleaned_text = "\n".join(
        " ".join(line.split()) for line in cleaned_text.split("\n")
    )

    # Remove leading/trailing whitespace
    cleaned_text = cleaned_text.strip()

    return cleaned_text


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters (default: 800)
        overlap: Character overlap between chunks (default: 150)

    Returns:
        List of text chunks
    """
    if chunk_size <= overlap:
        raise ValueError("Chunk size must be larger than overlap")

    chunks = []
    step = chunk_size - overlap

    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size]

        # Only add chunk if it has meaningful content
        if chunk.strip():
            chunks.append(chunk)

        # Stop if we've reached the end
        if i + chunk_size >= len(text):
            break

    return chunks


def process_documents(
    docs_dir: str,
    chunk_size: int = 800,
    overlap: int = 150,
    output_file: str = None
) -> List[Dict[str, any]]:
    """
    Load, clean, and chunk all documents.

    Args:
        docs_dir: Path to documents folder
        chunk_size: Chunk size in characters
        overlap: Overlap size in characters
        output_file: Optional path to save chunks as JSON

    Returns:
        List of chunk objects with metadata
    """
    print(f"\n{'='*60}")
    print("Document Processing Pipeline")
    print(f"{'='*60}")
    print(f"Chunk size: {chunk_size} chars")
    print(f"Overlap: {overlap} chars")
    print(f"{'='*60}\n")

    # Step 1: Load documents
    print("STEP 1: Loading documents...")
    documents = load_documents(docs_dir)
    print(f"\nLoaded {len(documents)} documents\n")

    # Step 2: Clean and chunk
    print("STEP 2: Cleaning and chunking...\n")
    all_chunks = []

    for filename, content in documents.items():
        print(f"Processing: {filename}")

        # Clean the text
        cleaned_content = clean_text(content)
        original_size = len(content)
        cleaned_size = len(cleaned_content)
        size_reduction = ((original_size - cleaned_size) / original_size * 100) if original_size > 0 else 0

        print(f"  Original size: {original_size} chars → Cleaned: {cleaned_size} chars ({size_reduction:.1f}% reduction)")

        # Create chunks
        chunks = chunk_text(cleaned_content, chunk_size, overlap)
        print(f"  Created {len(chunks)} chunks")

        # Store chunks with metadata
        for chunk_idx, chunk in enumerate(chunks):
            chunk_obj = {
                "document": filename,
                "chunk_id": chunk_idx,
                "text": chunk,
                "char_count": len(chunk),
                "word_count": len(chunk.split())
            }
            all_chunks.append(chunk_obj)

        print()

    # Step 3: Save results
    print(f"{'='*60}")
    print(f"RESULTS: {len(all_chunks)} total chunks created")
    print(f"{'='*60}\n")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        print(f"✓ Chunks saved to: {output_file}\n")

    return all_chunks


def display_sample_chunks(chunks: List[Dict], num_samples: int = 3):
    """Display sample chunks from different documents."""
    print(f"SAMPLE CHUNKS (showing {num_samples} samples):\n")
    print(f"{'='*60}\n")

    # Group by document
    docs = {}
    for chunk in chunks:
        doc = chunk["document"]
        if doc not in docs:
            docs[doc] = []
        docs[doc].append(chunk)

    # Show first chunk from first num_samples documents
    for i, (doc, doc_chunks) in enumerate(sorted(docs.items())[:num_samples]):
        sample = doc_chunks[0]
        print(f"Document: {sample['document']}")
        print(f"Chunk ID: {sample['chunk_id']}")
        print(f"Size: {sample['char_count']} chars, {sample['word_count']} words")
        print(f"\nContent:\n{sample['text'][:300]}...\n")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    # Configuration
    DOCS_DIR = "documents"
    OUTPUT_FILE = "chunks.json"
    CHUNK_SIZE = 800
    OVERLAP = 150

    # Process documents
    chunks = process_documents(
        docs_dir=DOCS_DIR,
        chunk_size=CHUNK_SIZE,
        overlap=OVERLAP,
        output_file=OUTPUT_FILE
    )

    # Display samples
    display_sample_chunks(chunks, num_samples=3)

    # Statistics
    print(f"\nStatistics:")
    print(f"  Total chunks: {len(chunks)}")
    avg_chars = sum(c["char_count"] for c in chunks) / len(chunks)
    avg_words = sum(c["word_count"] for c in chunks) / len(chunks)
    print(f"  Avg chunk size: {avg_chars:.0f} chars, {avg_words:.0f} words")
    print(f"  Min chunk: {min(c['char_count'] for c in chunks)} chars")
    print(f"  Max chunk: {max(c['char_count'] for c in chunks)} chars")
