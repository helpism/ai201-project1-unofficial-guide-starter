# The Unofficial Guide — Project 1

---

## Domain

Student guide to independent and locally-owned restaurants around Metro State University in Saint Paul, Minnesota. This knowledge is valuable but hard to find because there is no official university resource for it, and relevant information is scattered across multiple websites, Reddit threads, and business directories without structured organization.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Visit Saint Paul - East Side | Guide | https://www.visitsaintpaul.com/restaurants/neighborhoods/east-side/ |
| 2 | Visit Saint Paul - Lowertown | Guide | https://www.visitsaintpaul.com/restaurants/neighborhoods/lowertown/ |
| 3 | East Side Business Association | Directory | https://esaba.org/directory/ |
| 4 | Saint Paul Farmers Market | Vendor Directory | https://stpaulfarmersmarket.com/st-paul-farmers-market-vendors/ |
| 5 | Twin Cities Eater | Review Map | https://twincities.eater.com/maps/best-st-paul-restaurants-minnesota |
| 6 | MSP Magazine | Restaurant Directory | https://mspmag.com/search/location/st-paul-restaurants/ |
| 7 | Racket Minnesota | Food Blog | https://racketmn.com/category/food/ |
| 8 | Twin Cities Lifestyle | Dining Guide | https://www.twincities.com/lifestyle/eat/ |
| 9 | Reddit r/saintpaul | Community Forum | https://www.reddit.com/r/saintpaul/search/%3Fq%3Dfood |
| 10 | Swede Hollow Cafe | Restaurant Site | https://www.swedehollowcafe.com/ |

---

## Chunking Strategy

**Chunk size:** 800 characters

**Overlap:** 150 characters

**Why these choices fit your documents:** 800 characters captures individual restaurant sub-sections and topics while staying semantically focused. 150-character overlap preserves context when information crosses chunk boundaries (e.g., restaurant names won't split from descriptions).

**Preprocessing:** Removed extra whitespace, normalized line breaks, preserved special characters (addresses, phone numbers, symbols).

**Final chunk count:** ~1,200 chunks across all 10 documents (determined by `chunking.py`).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` (SentenceTransformers) — 384-dimensional vectors, CPU-efficient, fast inference.

**Production tradeoff reflection:** For real-world deployment with unlimited budget, I'd trade speed/cost for accuracy: specialized restaurant domain models (fine-tuned on dining reviews) would capture food culture nuances better; multilingual models like `multilingual-e5-large` would support Vietnamese and Hmong-speaking communities; context-heavy models like `voyage-large-2` could handle longer menu descriptions. However, `all-MiniLM-L6-v2` provides excellent speed/quality balance for this student-facing use case.

---

## Grounded Generation

**System prompt grounding instruction:** The LLM receives an explicit system message forbidding generation outside retrieved context: *"Answer ONLY using information from the provided restaurant guides. Do NOT use your general knowledge, training data, or assumptions. If documents don't contain enough information, respond with: 'I don't have enough information on that based on the restaurant guides available.' Every answer must cite its source(s)."* The LLM receives ONLY top-3 retrieved chunks as context, never raw web data or general knowledge.

**How source attribution is surfaced in the response:** Sources are extracted programmatically from chunk metadata (document name, chunk ID) **before** the LLM is called, never parsed from LLM output. This guarantees cited sources actually contain the answer. The response includes a `sources` array with exact document filenames (e.g., `southeast_asian_dining.txt`), allowing users to verify answers.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is the expected tipping etiquette when sitting at the bar vs. getting standard table service? | 15–20% for table service; $1–2 per drink for bartenders | For standard table service, the expected tipping etiquette is 15-20% of the total bill, with slightly higher tips for exceptional service. | relevant | accurate|
| 2 | What are the main ingredients and characteristics of Pho, a popular Vietnamese dish near Metro State? | Slow-cooked broth, rice noodles, proteins, aromatic herbs, fresh vegetables | Pho is a Vietnamese soup made with slow-cooked broth simmered for hours, sometimes days, and features fresh rice noodles added to order. It is customizable with different proteins such as beef, chicken, or vegetarian options, and includes aromatic herbs like basil, cilantro, and lime.  | Partially relevant | accurate |
| 3 | What types of dining establishments are available on the East Side, and what makes them different? | Fine dining, casual neighborhood, ethnic cuisine, pub/bar, street food/quick bites | The East Side offers a variety of dining establishments, including Southeast Asian and Hmong specialties, American comfort food and burgers, contemporary American with creative preparations, cafe food and light fare, international and fusion options, and traditional and comfort cuisine.  | relevant | accurate |
| 4 | What is Banh Mi and what makes it a good meal option for students between classes? | Vietnamese sandwich with crispy baguette, pickled veg, proteins, cilantro; quick, portable, affordable | Banh Mi is a type of sandwich that cost $5-$8. It's a good food for student becuase it's better quality than fast food | relevant | accurate |
| 5 | What sushi restaurants are in downtown Anchorage, Alaska? | **REJECT** — Out of scope | I don't have enough information on that based on the restaurant guides available.| relevant | accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** What are easy ways to get around in the eastside

**What the system returned:** I don't have enough information on that based on the restaurant guides available.

**Root cause (tied to a specific pipeline stage):** I think i was too strict on how the LLM uses in context provided

**What you would change to fix it:** Allowing more leniency especially when a user asks a conversational or question that touches on neighborhood logistics that could help them plan for going to a specific resturant

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** I help me in understanding what is expect from me and what should be given to the AI to write. It sort of created a clear line between my thinking and using AI to supplement that instead of giving the thinking to an AI 

**One way your implementation diverged from the spec, and why:** The architecture was a bit different in the spec vs the implementation.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* I had Claude implement the chunking strategy based on my specification in planning.md
- *What it produced:* It created the chunking strategy as specified and created a json file to save the chunks
- *What I changed or overrode:* I did not change any implementation

**Instance 2**

- *What I gave the AI:* I gave claude the structure and UI needs that i wanted for the gradio interface and how it should implement the use of groq.
- *What it produced:* It produce the code as needed but it needed a few changes.
- *What I changed or overrode:* I changed the implementation of the LLM call. I also changed the local URL because it app was launching on a non-visible URL.
