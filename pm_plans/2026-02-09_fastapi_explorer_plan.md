# Fluxnote Explorer (FastAPI) — Implementation Plan
Date: 2026-02-09

## Goal
Create a simple, read‑only FastAPI web app to visualize what’s stored in Fluxnote’s MongoDB: summaries, ideas, tags, and basic search/filtering. No editing or auth changes in this phase.

## Scope (MVP)
- **Read‑only UI** that lists summaries and lets users drill into summary details and ideas.
- **Tag browser** with counts and filtering.
- **Basic text search** (title/summary text/idea text) via server‑side query.
- **No write actions** (no tagging, no edits, no deletions).

## Assumptions
- MongoDB is already configured for the core server (reuse existing config/connection patterns).
- Data models are the existing `Summary` / `Idea` documents stored by `langchain_interface.py`.

## Architecture
- **Backend:** New FastAPI app under `server/` (e.g., `server/explorer_app.py`) or `server/src/explorer_app.py`.
- **UI:** Jinja2 templates + static CSS (simple, fast to ship). Optionally use HTMX for pagination/filter updates.
- **DB Access:** Reuse MongoDB connection settings from `server/src/langchain_interface.py` and config files.

## API Endpoints (read‑only)
1) `GET /explorer` — main UI page (redirect to summaries list)
2) `GET /explorer/summaries`
   - Query params: `q`, `tag`, `page`, `page_size`
   - Returns list with: title, created_at, tags, idea count, source (if present).
3) `GET /explorer/summaries/{id}`
   - Full summary + idea list (idea text, tags, optional embedding length).
4) `GET /explorer/tags`
   - Tag list with counts across summaries/ideas.
5) `GET /explorer/ideas`
   - Optional: filter by `tag` and `q` for idea text.

## UI Views
- **Summaries List**
  - Left panel: tag list + counts.
  - Main panel: summary cards (title, snippet, tags, idea count, created).
- **Summary Detail**
  - Summary text at top, then ideas list.
  - Show tags per idea and per summary.
- **Search Bar**
  - Filters summaries/ideas by free text and tag.

## Data Queries (Mongo)
- Use existing collections accessed in `langchain_interface.py`:
  - Summaries collection + tags + ideas.
  - User scoping if available; else single‑user default.
- Build simple indexes (if not present):
  - `summaries.title`, `summaries.summary_text`, `ideas.text`, `tags`.

## Non‑Goals
- Auth integration (will remain as-is for now).
- Editing/creating summaries/ideas.
- Vector search or semantic search.

## Implementation Steps
1) **Read config & connect DB**
   - Reuse Mongo config from `server/config.json` + `secret_config.json`.
2) **Implement read‑only routes**
   - Summaries list + detail + tags.
3) **Templates**
   - `templates/summaries.html` and `templates/summary_detail.html`.
4) **Add minimal CSS**
   - Simple layout, readable typography, tag pills.
5) **Wire into start script**
   - Add optional `start_explorer.sh` (or note `uvicorn explorer_app:app`).

## Acceptance Criteria
- Can browse summaries and ideas in a browser.
- Tag list updates and filters summaries correctly.
- Search filters summaries/ideas by text.
- No data mutation endpoints.

## Deliverables
- New FastAPI explorer app file(s)
- Templates + static CSS
- README snippet with run instructions

## Optional Enhancements (Later)
- HTMX live filtering without full reload.
- Pagination / infinite scroll.
- Link to websocket server actions (read into chat).
