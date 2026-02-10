# Fluxnote Open Questions & Risks (2026-02-08)

## Product / UX Questions
- **How should “context” be defined for contextual chat?** Tags, document titles, or semantic search results are options. (TODO.md:71-75; server/src/interactions.py:15-40)
- **Tag UX:** Are tags purely LLM-generated, user-edited, or hybrid? Current code supports LLM tag generation and a per-user tag list but no UX surface yet. (server/src/langchain_interface.py:411-514)
- **Note metadata schema:** Which metadata fields should be required/optional for the new note parser? (TODO.md:41-51)

## Technical Risks
- **Authentication:** Login is unauthenticated, which is risky for multi-user support. (server/src/interactions.py:417-422)
- **Vector search choice:** Embeddings are stored but no vector search engine is integrated yet; need to choose MongoDB vector search vs. dedicated vector DB vs. local FAISS. (TODO.md:57-69; server/src/langchain_interface.py:600-634)
- **Scaling embeddings:** Summary verification + tagging is heavy compute and currently synchronous. (TODO.md:34-39; server/src/langchain_interface.py:516-598)

## Implementation Gaps to Track
- **Front-end ↔ back-end command history sync** (TODO.md:90-91; server/src/langchain_interface.py:144-164)
- **GUI configuration** (e.g., WebSocket URL in macOS client). (frontend/swift/eagle/README.md:28-29)
- **Searchable knowledge graph** (graph DB exploration, highlighting, visualization). (TODO.md:76-114)

## Dependencies / External Services
- LLM provider via OpenAI-compatible endpoint is assumed by default; OpenAI API can be toggled via config. (README.md:56-61; server/src/langchain_interface.py:376-388)
- MongoDB is required for storage. (server/src/langchain_interface.py:86-100)
