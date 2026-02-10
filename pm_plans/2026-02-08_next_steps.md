# Fluxnote Next Steps Plan (2026-02-08)

This plan prioritizes work to unlock the “chat with user-specified context” feature (TODO.md:71-75), using existing server capabilities as a base.

## Priority 0: Stabilize Core Data Flow (1–2 weeks)
**Goal:** Make summaries/ideas more reliable and support durable user sessions.

1) **Note-parser prompt + metadata**
   - Add new system prompt ("Note-Parser") + schema for metadata (completeness/reliability/context). (TODO.md:41-51)
   - Update `langchain_summarize_text_async` to accept metadata and pass it to the system prompt. (server/src/langchain_interface.py:600-634)
   - Evidence baseline: current system prompts are loaded from `system_prompts.json` at login. (server/src/langchain_interface.py:78-83)
   - **Deliverable:** new prompt + metadata fields wired into summarization.

2) **User authentication / session identification**
   - Implement API key or token-based auth at login (currently TODO). (server/src/interactions.py:417-422)
   - Tie MongoDB collections to authenticated user IDs (already present, but login is unauthenticated). (server/src/langchain_interface.py:78-110)
   - **Deliverable:** login requires key; invalid logins rejected.

3) **Command history sync**
   - Persist user command history (currently in-memory only). (server/src/langchain_interface.py:144-164)
   - Add “fetch user history on login” + CLI up-arrow integration. (TODO.md:53-55, 90-91; frontend/python-cli/main.py:204-239)
   - **Deliverable:** up-arrow history works across sessions in CLI.

## Priority 1: Semantic Search + Tagging System (2–4 weeks)
**Goal:** Implement vector-backed semantic search and tag-driven filters to power contextual chat.

1) **Vector DB integration & retrieval APIs**
   - Choose initial vector store (MongoDB vector search, external vector DB, or local FAISS).
   - Add search endpoints to `interactions.available_request_functions` (e.g., `semantic_search`). (server/src/interactions.py:460-505)
   - Reuse stored embeddings from summaries/ideas (already generated). (server/src/langchain_interface.py:625-629)
   - **Deliverable:** ability to query top-k ideas/summaries by embedding similarity.

2) **Tagging system completion**
   - Connect existing `tag_idea`/`tag_summary` outputs to user-facing tag views and filters. (server/src/langchain_interface.py:430-514)
   - Decide tag schema (freeform vs. controlled vocab); store per-user tag list (already supported). (server/src/langchain_interface.py:411-428)
   - **Deliverable:** stable tags surfaced in CLI and/or GUI.

## Priority 2: Contextual Chat (1–2 weeks after Priority 1)
**Goal:** Enable “chat with user-specified context.”

- Define “context” as either tags, document titles, or semantic search result sets. (TODO.md:71-75)
- Implement a `chat_with_context` function that retrieves top-k ideas/summaries by tag or vector search and injects them into chat history before chat. (server/src/interactions.py:15-40)
- **Deliverable:** CLI command that accepts a tag list or search query and starts a context-aware chat.

## Priority 3: Client UX Improvements (ongoing)
- macOS GUI: make WebSocket URL configurable. (frontend/swift/eagle/README.md:28-29)
- GNOME GUI: copy WebSocket manager from macOS + functional shell. (frontend/swift/GnomeApp/README.md:7-9)
- Optional: add lightweight UI for tags/search results.

## Longer-Term (Backlog from TODO.md)
- Graph DB exploration, idea highlighting in documents, PDF parsing, news ingestion, audio/image ingestion, model-per-task routing. (TODO.md:76-201)

## Suggested Acceptance Criteria
- **Note-parser:** metadata fields visible in summary output and can be set via API/CLI.
- **Vector search:** query returns ranked ideas/summaries with titles and tags.
- **Contextual chat:** chat endpoint accepts tag list or query and uses retrieved ideas in prompt.
- **Auth:** unauthorized login attempts rejected, API key stored in secret config.
