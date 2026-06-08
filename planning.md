# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
I chose to build a system that helps students find good resturants, mostly locally owned, around Metro State University in Saint Paul. This information is hard to find becuase there is simply no official channel for it, also there is no structured imformation on it in a lot of websites. 
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Visit Saint Paul| A saint paul guide website|https://www.visitsaintpaul.com/restaurants/neighborhoods/east-side/ |
| 2 | Visit Saint Paul| A saint paul guide website| https://www.visitsaintpaul.com/restaurants/neighborhoods/lowertown/|
| 3 | East side business association| business association in saint paul | https://esaba.org/directory/|
| 4 | farmers market| imformation about saint paul's farmer's market| https://stpaulfarmersmarket.com/st-paul-farmers-market-vendors/|
| 5 |twincites | Contains imformation about the twincites for eating adventures | https://twincities.eater.com/maps/best-st-paul-restaurants-minnesota|
| 6 | mspmg | Another minnesota guide website| https://mspmag.com/search/location/st-paul-restaurants/|
| 7 | RacketMn|Another minnesota guide website | https://racketmn.com/category/food/|
| 8 | twincites| Contains imformation about the twincites for adventures | https://www.twincities.com/lifestyle/eat/|
| 9 | reddit | a subreddit for information about saint paul| https://www.reddit.com/r/saintpaul/search/%3Fq%3Dfood|
| 10 | swede hollow cafe| A pretty good cafe around saint paul|https://www.swedehollowcafe.com/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 800 characters

**Overlap:** 150 character overlap

**Reasoning:** 800 characters is small enough to capture the a specific restaurant sub-section/ topic. The 150 character overlap ensures that context is preserved incase a chunked information crosses the chunk boundary

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** all-MiniLM-L6-v2

**Top-k:** 3

**Production tradeoff reflection:** all-MiniLM-L6-v2 is fast and efficient

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
