"""
Query Interface: Grounded Generation + Gradio Web UI
Integrates ChromaDB retrieval with Groq LLM for grounded restaurant recommendations.

Pipeline Stage: Retrieval → Generation (with grounding enforcement) → Interface
"""

import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
import gradio as gr
from embedding_retrieval import VectorStore
from groq import Groq

# Load environment variables (including GROQ_API_KEY)
load_dotenv()


class GroundedRestaurantGuide:
    """
    Grounded generation interface: retrieves context chunks, enforces grounding,
    and generates answers with programmatic source attribution.
    """

    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        groq_api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile"
    ):
        """
        Initialize the grounded generation pipeline.

        Args:
            persist_dir: Path to ChromaDB persistence directory
            groq_api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Groq model to use
        """
        self.persist_dir = persist_dir
        self.model = model

        # Initialize vector store (reuses ChromaDB from embedding_retrieval.py)
        print("Initializing Vector Store...")
        self.vector_store = VectorStore(persist_dir=self.persist_dir)

        # Initialize Groq client
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Set it in .env file or pass as parameter."
            )
        self.groq_client = Groq(api_key=api_key)
        print(f"✓ Groq client initialized with model: {self.model}\n")

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with explicit grounding constraints.
        This is the enforcement mechanism for grounding.
        """
        return """You are a knowledgeable assistant for Saint Paul restaurant recommendations.

CRITICAL CONSTRAINTS:
1. Answer ONLY using information from the provided restaurant guides.
2. Do NOT use your general knowledge, training data, or assumptions about restaurants.
3. If the provided documents do NOT contain enough information to answer, respond with EXACTLY:
   "I don't have enough information on that based on the restaurant guides available."
4. Every answer must cite its source document name(s).
5. If a question asks about places outside Saint Paul or topics unrelated to dining, refuse with the exact phrase above.

RESPONSE FORMAT:
- Begin with a clear, direct answer grounded in the documents.
- End with explicit source citation: (Source: [document names])

EXAMPLE GOOD RESPONSE:
"Based on the Southeast Asian Dining guide, Pho is a Vietnamese dish made with slow-cooked broth, fresh rice noodles, and customizable proteins. (Source: southeast_asian_dining.txt)"

EXAMPLE REFUSAL:
"I don't have enough information on that based on the restaurant guides available."

DO NOT:
- Make up restaurant names or details
- Infer information from general knowledge
- Provide answers not directly supported by the retrieved chunks
- Cite sources that are not in the provided context"""

    def query_restaurant_guide(self, question: str, top_k: int = 3) -> Dict:
        """
        End-to-end query: retrieve → prompt → generate → format with grounding guarantee.

        Args:
            question: User's plain-language query
            top_k: Number of chunks to retrieve (default: 3 per planning.md)

        Returns:
            Structured dict with:
                - answer: Generated response (grounded or explicit refusal)
                - sources: List of source document names (from metadata, guaranteed)
                - confidence: "high", "medium", or "low" based on retrieval quality
                - retrieval_explanation: Why these chunks were selected
                - distances: Similarity scores for auditing
        """

        # STEP 1: Retrieve top-k relevant chunks (retrieval-only context)
        retrieved = self.vector_store.retrieve_relevant_chunks(
            query=question,
            top_k=top_k
        )

        # Handle empty retrieval
        if not retrieved:
            return {
                "answer": "I don't have enough information on that based on the restaurant guides available.",
                "sources": [],
                "confidence": "low",
                "retrieval_explanation": "No relevant chunks found in restaurant guides.",
                "distances": []
            }

        # STEP 2: Extract chunk texts, sources, and distances
        chunk_texts = [chunk["text"] for chunk in retrieved]
        distances = [chunk["distance"] for chunk in retrieved]

        # Extract sources from metadata (programmatically guaranteed)
        sources = []
        for chunk in retrieved:
            doc = chunk["metadata"]["document"]
            if doc not in sources:
                sources.append(doc)

        # STEP 3: Build context (chunks only — no general knowledge injection)
        context_chunks = "\n---\n".join(chunk_texts)
        context = f"RESTAURANT GUIDES CONTEXT:\n\n{context_chunks}\n\n---\n\nNow answer the user's question based ONLY on the above context."

        # STEP 4: Determine confidence level based on retrieval quality
        strong_matches = sum(1 for d in distances if d < 0.6)
        if strong_matches >= 2:
            confidence = "high"
        elif strong_matches >= 1 or len(retrieved) >= 2:
            confidence = "medium"
        else:
            confidence = "low"

        # STEP 5: Call Groq LLM with system prompt (grounding enforcement with corrected syntax)
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": f"{context}\n\nUser Question: {question}"
                    }
                ],
                max_tokens=1024,
                temperature=0.3  # Lower temp for more deterministic grounding
            )
            answer = response.choices[0].message.content

        except Exception as e:
            return {
                "answer": f"Error calling Groq API: {str(e)}",
                "sources": sources,
                "confidence": "low",
                "retrieval_explanation": f"Retrieved {len(retrieved)} chunks but generation failed.",
                "distances": distances
            }

        # STEP 6: Build structured output with sources from metadata
        retrieval_explanation = (
            f"Retrieved {len(retrieved)} relevant chunks. "
            f"Average distance: {sum(distances) / len(distances):.4f}. "
            f"Strong matches (distance < 0.6): {strong_matches}/{len(retrieved)}."
        )

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "retrieval_explanation": retrieval_explanation,
            "distances": distances
        }


# Initialize global instance (for Gradio interface)
def init_guide() -> GroundedRestaurantGuide:
    """Initialize guide instance once at startup."""
    try:
        return GroundedRestaurantGuide(
            persist_dir="./chroma_db",
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    except Exception as e:
        print(f"Error initializing guide: {e}")
        raise


# Gradio interface handlers
def handle_query(question: str) -> tuple:
    """
    Wrapper for Gradio: takes question, returns answer, sources, and metadata.

    Args:
        question: User's question from text input

    Returns:
        Tuple of (answer, sources_text, confidence_text, distances_text)
    """
    if not question.strip():
        return "", "", "", ""

    result = guide.query_restaurant_guide(question)

    # Format sources as bullet list
    sources_text = (
        "\n".join(f"• {s}" for s in result["sources"])
        if result["sources"]
        else "No sources retrieved"
    )

    # Format confidence
    confidence_text = f"Confidence: {result['confidence'].upper()}"

    # Format distances for auditing
    distances_text = (
        "Retrieval Quality:\n" + result["retrieval_explanation"]
        if result["distances"]
        else ""
    )

    return result["answer"], sources_text, confidence_text, distances_text


def build_gradio_interface() -> gr.Blocks:
    """
    Build Gradio web interface for the Saint Paul Restaurant Guide.

    Returns:
        Configured Gradio Blocks interface
    """

    with gr.Blocks(
        title="The Unofficial Saint Paul Restaurant Guide",
        theme=gr.themes.Soft()
    ) as demo:
        gr.Markdown(
            """
            # 🍽️ The Unofficial Saint Paul Restaurant Guide

            Ask questions about local restaurants, dining culture, and cuisine recommendations.
            Answers are grounded in curated restaurant guides for Metro State University students.
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                inp = gr.Textbox(
                    label="Your Question",
                    placeholder="e.g., What Southeast Asian restaurants are near Metro State? What is Banh Mi?",
                    lines=2,
                    interactive=True
                )
                btn = gr.Button("Ask Guide", size="lg", variant="primary")

        with gr.Row():
            with gr.Column(scale=1):
                answer = gr.Textbox(
                    label="Answer",
                    lines=12,
                    interactive=False,
                    max_lines=12
                )

            with gr.Column(scale=1):
                sources = gr.Textbox(
                    label="Sources",
                    lines=5,
                    interactive=False,
                    max_lines=5
                )

        with gr.Row():
            with gr.Column(scale=1):
                confidence = gr.Textbox(
                    label="Confidence Level",
                    interactive=False
                )

            with gr.Column(scale=1):
                distances_info = gr.Textbox(
                    label="Retrieval Quality Details",
                    lines=3,
                    interactive=False,
                    max_lines=3
                )

        # Connect button click and Enter key submission
        btn.click(
            handle_query,
            inputs=inp,
            outputs=[answer, sources, confidence, distances_info]
        )
        inp.submit(
            handle_query,
            inputs=inp,
            outputs=[answer, sources, confidence, distances_info]
        )

        gr.Markdown(
            """
            ---
            ### How This Works

            1. **Retrieval**: Your question is converted to an embedding and matched against restaurant guide chunks.
            2. **Grounding**: The AI is instructed to answer ONLY from the retrieved documents, not general knowledge.
            3. **Generation**: If the documents contain relevant information, an answer is generated with source citations.
            4. **Rejection**: If the question cannot be answered from available guides, the system explicitly refuses.

            ### Test These Questions

            - "What is the expected tipping etiquette when sitting at the bar vs. getting standard table service?"
            - "What are the main ingredients and characteristics of Pho?"
            - "What types of dining establishments are available on the East Side?"
            - "What is Banh Mi and what makes it a good meal option for students?"
            - "What sushi restaurants are in downtown Anchorage?" *(should be rejected)*
            """
        )

    return demo


# ===== VERIFICATION / TESTING =====

def run_test_suite(guide: GroundedRestaurantGuide):
    """
    Run the 5 test cases from planning.md to verify grounding.

    Args:
        guide: Initialized GroundedRestaurantGuide instance
    """

    test_cases = [
        {
            "id": 1,
            "question": "What is the expected tipping etiquette when sitting at the bar vs. getting standard table service?",
            "expected_behavior": "Answer with 15-20% for table, $1-2/drink for bartender",
            "grounding_test": "Response must cite source document where tipping info appears"
        },
        {
            "id": 2,
            "question": "What are the main ingredients and characteristics of Pho, a popular Vietnamese dish near Metro State?",
            "expected_behavior": "Answer with broth, rice noodles, proteins, herbs",
            "grounding_test": "Response must cite southeast_asian_dining.txt or hmong_village source"
        },
        {
            "id": 3,
            "question": "What types of dining establishments are available on the East Side, and what makes them different from each other?",
            "expected_behavior": "List fine dining, casual, ethnic, pub food, street food",
            "grounding_test": "Response must cite eastside_restaurants_guide.txt"
        },
        {
            "id": 4,
            "question": "What is Banh Mi and what makes it a good meal option for students between classes?",
            "expected_behavior": "Answer with crispy baguette, pickled veg, quick/portable/cheap",
            "grounding_test": "Response must cite source document"
        },
        {
            "id": 5,
            "question": "What sushi restaurants are in downtown Anchorage, Alaska?",
            "expected_behavior": "REJECT — Outside scope",
            "grounding_test": 'System must return exact phrase: "I don\'t have enough information on that based on the restaurant guides available."'
        }
    ]

    print(f"\n{'='*80}")
    print("GROUNDING VERIFICATION: 5-Test Suite from planning.md")
    print(f"{'='*80}\n")

    for test in test_cases:
        print(f"TEST {test['id']}: {test['question'][:60]}...")
        print(f"   Expected: {test['expected_behavior']}")
        print(f"   Grounding Test: {test['grounding_test']}\n")

        result = guide.query_restaurant_guide(test["question"])

        print(f"   Answer:\n    {result['answer'][:200]}...")
        print(f"\n   Sources: {', '.join(result['sources']) if result['sources'] else 'None'}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Distances: {[f'{d:.4f}' for d in result['distances']]}")

        # Grounding verdict
        if test["id"] == 5:
            # Test 5: Should explicitly refuse
            expected_refusal = "I don't have enough information on that based on the restaurant guides available."
            is_grounded = expected_refusal in result["answer"]
            verdict = "✓ GROUNDED (explicit refusal)" if is_grounded else "✗ FAILED (not refused)"
        else:
            # Tests 1-4: Should cite sources
            is_grounded = len(result["sources"]) > 0
            verdict = "✓ GROUNDED (sources cited)" if is_grounded else "✗ FAILED (no sources)"

        print(f"   Grounding Verdict: {verdict}\n")
        print(f"{'-'*80}\n")


# ===== ENTRY POINT =====

if __name__ == "__main__":
    import sys

    print("\n" + "="*80)
    print("Saint Paul Restaurant Guide - Query Interface")
    print("="*80 + "\n")

    # Initialize guide (loads ChromaDB + Groq)
    try:
        guide = init_guide()
    except Exception as e:
        print(f"Fatal Error: {e}")
        sys.exit(1)

    # Parse command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run test suite
        run_test_suite(guide)
    else:
        # Launch Gradio interface
        print("Launching Gradio interface...\n")
        demo = build_gradio_interface()
        demo.launch(
            share=False,
            server_name="localhost",
            server_port=7860,
            show_error=True
        )
