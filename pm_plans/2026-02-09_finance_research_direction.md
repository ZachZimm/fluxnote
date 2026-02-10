# Fluxnote PM Plan — Ambitious Finance Research Direction
Date: 2026-02-09
Direction: **Financial Research Intelligence Graph + Living Investment Memos**

## 1) Core Vision
Turn Fluxnote’s idea-centric knowledge base into a **finance-native research system** that continuously builds, debates, and updates investment theses. Instead of static notes, users maintain **living research dossiers** that automatically ingest filings, transcripts, macro data, and analyst notes, then map them to a knowledge graph of claims, evidence, and contradictions.

This direction aligns with Fluxnote’s core philosophy (idea graphs + Socratic questioning) while applying it to finance where **evidence, citations, and time series** matter.

## 2) Target Users & Jobs-to-be-Done
**Primary:** public market analysts, buy-side researchers, founders/VCs, and advanced retail investors.

**Top JTBD:**
- Build a coherent thesis fast (with citations) from noisy sources.
- Track if a thesis is strengthening or weakening as new data arrives.
- Compare companies, sectors, and macro factors without losing context.
- Generate a professional investment memo or teardown quickly.

## 3) Key Workflows (End-to-End)
1) **Research Intake**
   - Upload/clip: 10-K/10-Q, earnings call transcript, macro reports, investor presentations.
   - Connect data streams: SEC filings, earnings call transcripts, macro series (FRED), prices, options, news RSS.

2) **Idea Extraction (Fluxnote Core)**
   - LLM extracts claims, assumptions, forecasts, and risks.
   - Each claim becomes a node: `claim`, `evidence`, `counterevidence`, `open_question`.
   - Semantic linking: tie claims to financial metrics or source pages (citations).

3) **Thesis Builder**
   - User creates a thesis template (bull/base/bear).
   - Claims and evidence auto-populate sections.
   - Contradiction engine flags weak links, missing evidence, and data gaps.

4) **Living Memo + Alerts**
   - Memo auto-updates with new data: “3 nodes strengthened, 1 contradicted.”
   - Alerts when key metrics cross thresholds or filings mention key risks.

5) **Report Generation**
   - Output a clean investment memo or teardown with a full citation ledger.
   - Share read-only link or export to PDF/Markdown.

## 4) Differentiating Features
- **Claim Ledger:** Every note becomes structured claims with provenance and confidence.
- **Thesis Drift Monitor:** Track when new evidence shifts a claim’s confidence.
- **Contradiction Engine (Socratic):** Auto-generates counter-arguments and requires evidence.
- **Evidence Heatmap:** Highlight which memo sections have thin evidence.
- **Comparative Graphs:** Compare companies by claims/risks, not just metrics.

## 5) Data/Integrations (Phase 1/2)
**Phase 1 (core):**
- SEC filings (EDGAR), earnings call transcripts (public sources), news RSS.
- Manual upload for PDFs and notes.

**Phase 2 (advanced):**
- Macro series (FRED), pricing and fundamentals API, options flow.
- CRM/notes imports (Notion/Obsidian).

## 6) Architecture Notes
- **Document ingestion:** OCR + chunking + citation anchors.
- **Idea graph:** nodes for claims/assumptions/evidence/metrics.
- **Time-series linking:** claims referencing metrics bind to time series.
- **Socratic pipeline:** auto-generate contradictions, flag weak claims.
- **LLM configuration:** local model optional, with citation requirements enforced.

## 7) MVP Scope (Finance Vertical)
- Upload 10-Q + transcript + 1 report; auto-extract claims.
- Create a thesis memo with citations.
- Provide a contradiction report and evidence gaps.
- Share/export memo.

## 8) Roadmap (Aggressive)
**0–3 months:**
- Prototype ingestion + claim extraction on 10-Q PDFs.
- UI for claim nodes + citations.
- Generate a basic “living memo” from nodes.

**3–6 months:**
- Add transcript parsing + contradiction engine.
- Add evidence heatmap + claim confidence.

**6–12 months:**
- Integrate macro + pricing data.
- Automated alerts for thesis drift.
- Comparative analysis across companies.

## 9) Success Metrics
- Time-to-first-memo < 30 minutes from new filings.
- % of claims with citations > 80%.
- User-reported confidence in thesis reasoning.
- Repeat usage rate per company tracked.

## 10) Risks & Open Questions
- **Data licensing** for transcripts and pricing feeds.
- **Hallucination risk** if evidence links are weak.
- **User trust** requires visible citations and raw source access.

---

# Review Pass Additions (Meaningful)

## A) Thesis Health Scoring (Quant + Qual)
Introduce a **Thesis Health Score** derived from:
- claim confidence (evidence strength),
- diversity of evidence sources,
- contradiction count/severity,
- recency of confirming evidence,
- sensitivity to macro variables.

This gives a simple “up/down” indicator without hiding the underlying logic.

## B) Financial Entity Ontology
Define a finance-native ontology:
- entities: company, segment, product, competitor, geography, customer cohort.
- metrics: revenue, margin, ARPU, churn, CAC, FCF, capex.
- events: earnings, guidance, regulatory, M&A.

This makes cross-company comparisons and macro linkages possible.

## C) Research Quality Gate
Add an **audit mode**: no claim can be promoted to a memo unless it has at least 1 primary citation and a confidence threshold. This preserves integrity and aligns with finance expectations.

## D) Counterfactuals & Scenario Engine
Allow users to define base/bull/bear scenarios and connect claims to assumptions. This enables structured what-if reasoning (e.g., “If GMV growth slows to 5%, update margin thesis”).

## E) Compliance & Sharing Controls
- Redact sensitive data on export.
- Audit log for edits and source changes.
- “Read-only research room” for sharing with teams.

## F) Evaluation Plan
- Create a benchmark set of 10 public companies and 3 macro themes.
- Compare memo quality + speed vs baseline manual note-taking.
- Track “error” rate (claims without citations) to gauge reliability.
