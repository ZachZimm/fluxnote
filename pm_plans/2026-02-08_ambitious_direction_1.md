# Ambitious Direction 1: Living Knowledge Universe + Agentic Research OS

## Vision
Turn Fluxnote into a “living knowledge universe” that continuously ingests, links, and debates information across modalities, producing dynamic, self-updating briefs and decision-ready insights.

## Why this direction
Fluxnote already breaks documents into ideas, stores embeddings, and supports chat + summaries. This direction pushes that into a long-term, continuously updating, multi-modal research operating system rather than a static note store.

## 5–7 Step Arc (far‑flung)
1) **Universal Ingestion Fabric**
   - Native pipelines for PDFs, web articles, audio, images, and slide decks, all mapped into the existing Summary/Idea schema (extends TODO backlog).  
   - Auto‑attach provenance metadata (source, timestamp, trust score, media fingerprints).
2) **Knowledge Graph 2.0**
   - Replace “flat tags” with a typed, time‑aware knowledge graph (entities, claims, evidence, contradictions).  
   - Auto‑link new ideas to existing nodes using embeddings + symbolic rules.
3) **Claim‑Level Reasoning & Contradiction Engine**
   - Every idea becomes a claim with supporting evidence and counter‑evidence.  
   - Contradiction detection runs as background jobs and tags conflicting claims for review.
4) **Living Briefs / Auto‑Updating Reports**
   - Create “briefs” that stay current; they refresh when new evidence arrives.  
   - Users subscribe to a brief and receive diffs instead of re‑reading entire docs.
5) **Active Research Agents**
   - Agents monitor topics, discover new sources, and run recurring syntheses.  
   - Agent results are injected into the knowledge graph with confidence scores.
6) **Decision Simulator & Scenario Spaces**
   - Model “what‑if” outcomes using curated evidence sets.  
   - Generate competing narratives for the same topic to surface risks.
7) **Personal Research Co‑pilot Mode**
   - Fluxnote becomes a daily “intelligence layer” with personalized alerts, weekly digests, and a “what changed since last time” view.

## Enablers / Foundational Work
- Reliable auth + user isolation (known gap)
- Vector search + retrieval APIs (Priority 1)
- Metadata schema for notes (Priority 0)
- Graph DB selection and query layer
- Background job queue for summarization/verification/tagging

## Risks / Hard Problems
- Claim extraction + contradiction detection accuracy
- Running cost of continuous ingestion + background evaluation
- UX overload: showing “living” changes without noise

## Why it’s compelling
Fluxnote stops being a note app and becomes a research OS: always current, always challenging stale assumptions, and built around evidence‑first reasoning.