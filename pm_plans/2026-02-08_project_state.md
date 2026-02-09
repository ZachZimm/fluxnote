# Fluxnote Project State (2026-02-08)

## Snapshot (What it is)
- Vision: LLM-enhanced, idea-centric notes backend that breaks documents into ideas, builds a knowledge base, and supports Socratic/contradiction-style exploration. (README.md:1-82)
- Current implementation is “bare bones” vs. the long-term vision and expects an OpenAI-compatible server by default. (README.md:56-61)

## Current Architecture & Capabilities (evidence-based)
### Backend (server)
- WebSocket API in FastAPI/uvicorn. The server accepts JSON `{func: ...}` payloads and dispatches to a set of interaction handlers; supports async flows for chat, summarize, wiki, verify summary, etc. (server/src/api_server.py:1-75)
- Interaction layer exposes commands for:
  - Streaming chat (LLM) with chat history management. (server/src/interactions.py:15-40)
  - Summarization (text / article), summary retrieval, and reading summaries into chat history. (server/src/interactions.py:110-229)
  - Tag/idea retrieval by tag, reading tagged ideas into chat history. (server/src/interactions.py:230-296)
  - Wiki search + page retrieval with optional persistence. (server/src/interactions.py:329-373)
  - Server status (CPU/GPU/Disk), user history, and login (no auth yet). (server/src/interactions.py:392-458)
- Core application logic is centralized in `langchain_interface`:
  - User login initializes MongoDB-backed config/history/system prompts. (server/src/langchain_interface.py:78-110)
  - CRUD-ish retrieval for summaries/articles and history (MongoDB collections). (server/src/langchain_interface.py:166-235, 328-350)
  - LLM chain creation uses `ChatOpenAI` with either OpenAI API or OpenAI-compatible base URL. (server/src/langchain_interface.py:376-388)
  - Summarization flow returns `Summary` objects; embeddings added to each idea. (server/src/langchain_interface.py:600-634)
  - Idea verification and re-write routines exist, with tagging helpers. (server/src/langchain_interface.py:516-598)
  - Tagging for ideas/summaries and tag aggregation are implemented. (server/src/langchain_interface.py:411-514)
- Embeddings use BGE-M3 via FlagEmbedding; dense embeddings are primary. (server/src/embeddings.py:1-16)
- Data models: `Summary` contains `Idea` list + tags; `Idea` includes `embedding` and `tags`. (server/src/models/Summary.py:1-18)

### Clients
- Python CLI client connects to WebSocket server, supports streaming chat, summary rendering, wiki commands, and TTS playback (server-directed). (frontend/python-cli/main.py:96-207)
- macOS Swift GUI client “Eagle” supports WebSocket comms, TTS, and OS STT; WebSocket URL still not user-configurable. (frontend/swift/eagle/README.md:1-29)
- GNOME Swift client is prototype / not functional yet. (frontend/swift/GnomeApp/README.md:1-9)

## Implemented vs. Planned (from TODOs)
- ✅ Implemented: vector embedding manager + embeddings stored on summaries/ideas, summary verification + idea rewrite, wiki article persistence, user command history (server-side). (TODO.md:17-55)
- ⏳ Planned / Open:
  - “Note-parser” prompt + metadata for user notes. (TODO.md:41-51)
  - Vector database + tagging system for semantic search and idea spaces. (TODO.md:57-69)
  - User-specified context chat (depends on tagging + vector search). (TODO.md:71-75)
  - Graph database exploration, command history sync front-end↔back-end, UI highlighting. (TODO.md:76-102)
  - Broader ingestion: PDFs, news feeds, audio-to-text, images, PPT, etc. (TODO.md:133-201)

## Key Gaps / Risks
- Authentication is not implemented for login/WS sessions. (server/src/interactions.py:417-422)
- Vector DB + semantic search is listed but not integrated; only embeddings are stored. (TODO.md:57-69; langchain_interface.py:600-634)
- Client history sync + up-arrow behavior still missing (server has history). (TODO.md:90-91; langchain_interface.py:144-164)
- Front-end GUI configuration is thin (e.g., WS URL not configurable). (frontend/swift/eagle/README.md:28-29)

## Ambitious Direction Note (Finance)
A finance‑native direction has been scoped: “Financial Research Intelligence Graph + Living Investment Memos.” It would ingest filings/transcripts/macro data, extract claim/evidence nodes with citations, and maintain living memos with thesis‑drift alerts; see `pm_plans/2026-02-09_finance_research_direction.md`.

## Repo Navigation
- Backend: `server/src/` (FastAPI WS, LLM interface, models, embeddings)
- CLI: `frontend/python-cli/`
- GUI: `frontend/swift/eagle/`, `frontend/swift/GnomeApp/`
- Roadmap: `TODO.md`
