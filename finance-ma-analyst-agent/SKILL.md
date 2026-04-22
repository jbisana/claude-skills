---
name: finance-ma-analyst-agent
description: >
  Build a multi-intent automation that acts as a UK boutique M&A finance research analyst AI employee.
  Handles three Slack-triggered intents — company research, pitch deck generation, and industry briefing —
  by wiring together Companies House, Firecrawl, Alpha Vantage, OpenRouter (Claude/GPT), Google Drive/Docs/Sheets/Slides,
  and a PostgreSQL memory store. Use this skill whenever the user wants to:
  - automate financial research workflows
  - build a Slack-triggered AI agent for M&A or finance tasks
  - generate pitch decks or company profiles automatically from a chat message
  - set up a multi-intent routing agent
  - recreate or extend the "Finance Research Analyst AI Employee" automation template
  - connect Companies House API, Firecrawl, or Alpha Vantage into a research pipeline
---

# Finance M&A Analyst Agent

This skill builds an automation that behaves like a junior UK boutique M&A research analyst — all triggered from a Slack message. It classifies the user's intent, gathers real data from free/low-cost APIs, asks an LLM to synthesise it, and delivers polished artefacts (Google Docs, Slides, Drive folders) back to the Slack thread.

## What This Agent Does

A user types a message in a Slack channel. The agent:

1. **Classifies intent** → `research`, `pitch`, `brief`, or `unknown`
2. Branches into the matching sub-pipeline
3. Gathers data from external APIs in parallel
4. Feeds everything to an LLM (via OpenRouter) with a strict JSON schema
5. Saves artefacts to Google Drive and a PostgreSQL memory store
6. Replies in the Slack thread with links

### Intent → Example Phrase Mapping

| Intent | User says… |
|--------|-----------|
| `research` | `Research Revolut, fintech` |
| `pitch` | `Prepare pitch for Monzo` |
| `brief` | `Industry briefing UK fintech` |
| `unknown` | Anything else → helpful error reply |

---

## Architecture Overview

```
Slack Trigger
  └─► Valid message filter (no bots, has text)
       └─► Prepare Slack context
            └─► Build intent request (Claude Haiku / structured JSON schema)
                 └─► Intent Classifier (OpenRouter HTTP)
                      └─► Parse Intent
                           └─► Intent Switch
                                ├─► [research] → Research Pipeline
                                ├─► [pitch]    → Pitch Pipeline
                                ├─► [brief]    → Brief Pipeline
                                └─► [unknown]  → Error Reply
                                         └─► Send Slack Reply
```

---

## Pipeline Details

### 1. Intake & Routing

- **Slack Trigger** → listens for `message` events on a dedicated channel
- **Valid Slack Message?** (IF node) — filters out bot messages (`bot_id` absent), requires `text` field, requires `type == "message"`
- **Prepare Slack Context** (Code) — extracts `raw_text`, `channel`, `message_ts`, `thread_ts`, `user`
- **Build Intent Request** (Code) — constructs an OpenRouter chat completion body targeting `anthropic/claude-haiku-4.5` at temperature 0, with a strict `json_schema` response format:
  ```json
  { "intent": "research|pitch|brief|unknown", "company_name": "...", "sector": "...", "ticker": "...", "company_url": "...", "confidence": 0.95, "reasoning_note": "..." }
  ```
  System prompt instructs the model to infer missing fields (ticker, sector, URL) where safely possible.
- **Intent Classifier** (HTTP Request → OpenRouter)
- **Parse Intent** (Code) — robust JSON extraction helper that strips markdown fences before parsing

---

### 2.1 Research Pipeline

**Trigger phrase:** `Research [company_name], [sector]`

**Guard:** Requires `company_name` to be non-empty, otherwise returns a helpful error.

#### Step A — Companies House Lookup (parallel)
1. **Companies House Search** → `GET /search/companies?q={company_name}` (Basic Auth, free API)
2. **Pick Best Company Match** (Code) — scores results: active status (+5), exact title (+20), prefix match (+10), substring match (+5), UK address (+1). Returns `company_number` and `matched_title`.
3. **Company Match Found?** (IF) — halts with an error reply if no reliable match.

#### Step B — Data Gathering (parallel fan-out after match)
All 5 sources run simultaneously:

| Source | Node | API |
|--------|------|-----|
| Company profile | Companies House Profile | `GET /company/{number}` |
| Officers | Companies House Officers | `GET /company/{number}/officers` |
| Filing history | Companies House Filings | `GET /company/{number}/filing-history` |
| Website & news | Website Search + Company News | Firecrawl `/v2/search` |
| Market data | Alpha Vantage Overview | `GLOBAL_QUOTE` (if ticker exists) |

Each source is wrapped in a `Wrap *` Code node that tags it: `{ source: 'profile', data: ... }`. A sequence of Merge nodes collects all 5 into one item.

#### Step C — AI Synthesis
- **Build Research Bundle** (Code) — assembles the full payload: `channel`, `thread_ts`, `company_name`, `sector`, `ticker`, `company_url`, `company_number`, `matched_title`, `sources: { profile, officers, filings, news, website, alphavantage }`, `warnings[]`, `market_cap`, `website_url`
- **Build Research Prompt** (Code) — wraps the bundle into an OpenRouter request targeting `anthropic/claude-sonnet-4.5` at temperature 0.2 with a strict schema:
  ```json
  { "profile_markdown": "...", "slack_summary": "...", "market_cap_summary": "...", "risks_summary": "..." }
  ```
  System prompt: junior finance analyst, use only supplied data, say "unavailable" rather than inventing facts.
- **Research AI** (HTTP → OpenRouter)
- **Parse Research Output** (Code)

#### Step D — Storage
1. **Create Research Folder** (Google Drive) — folder name: `{company_name} - research - {yyyy-LL-dd}` inside a fixed parent folder
2. **Create Profile Doc** (Google Docs) — empty doc inside the research folder
3. **Update Profile Doc** (Google Docs) — inserts `profile_markdown`
4. **Upsert Company Record** (Postgres) — `INSERT … ON CONFLICT (companies_house_number) DO UPDATE` on table `aiemp_research_analyst_companies`
5. **Save Research Memory** (Postgres) — inserts `profile_markdown` as `content_text` into `aiemp_research_analyst_research_memory` (intent = `'research'`)
6. **Update Client DB Research** (Google Sheets) — `appendOrUpdate` matching on `companies_house_number`

#### Step E — Reply
- **Research Response** → Slack thread reply with `profile_doc` link and `slack_summary`

---

### 2.2 Pitch Pipeline

**Trigger phrase:** `Prepare pitch for [company_name]`

**Guard:** Requires `company_name`, then checks that a prior research record exists in Postgres. If not found → error reply telling user to run research first.

1. **Load Company Record** (Postgres) — `SELECT` from `aiemp_research_analyst_companies` by name (case-insensitive)
2. **Has Prior Research?** (IF) — checks that the record `id` is non-empty
3. **Load Research Memory** (Postgres) — fetches the most recent `content_text` for `intent = 'research'`
4. **Has Research Memory?** (IF) — checks that `content_text` is non-empty
5. **Create Pitch Folder** (Google Drive)
6. **Build Pitch Prompt** (Code) — uses `anthropic/claude-haiku-4.5`, strict schema:
   ```json
   { "profile_summary": "...", "financials": "...", "opportunity_summary": "...", "comps_note": "...", "press_release_markdown": "...", "slack_summary": "..." }
   ```
   System prompt: slide-ready bullet points only (3–5 per field), no narrative paragraphs, no invented comps.
7. **Pitch AI** (HTTP → OpenRouter)
8. **Parse Pitch Output** (Code)
9. **Copy Slides Template** (Google Drive `copy`) — copies a master `Slides template` file into the pitch folder
10. **Create Custom Presentation** (Google Slides `replaceText`) — replaces placeholders: `{company_name}`, `{sector}`, `{profile_summary}`, `{financials}`, `{opportunity_summary}`, `{comps_note}`
11. **Create Press Release Doc** + **Update Press Release Doc** (Google Docs)
12. **Update Pitch Assets** (Postgres) — sets `pitch_deck_url` on the company record
13. **Update Client DB Pitch** (Google Sheets)
14. **Pitch Response** → Slack thread reply with deck URL and press release URL

---

### 2.3 Brief Pipeline

**Trigger phrase:** `Industry briefing [sector]`

**Guard:** Requires `sector` to be non-empty.

1. **Sector News** (Firecrawl `/v2/search`) — query: `{sector} UK mergers acquisitions trends recent news`, 10 results
2. **ONS M&A Source** (HTTP GET) — fetches ONS macro M&A bulletin (free, no auth)
3. **Merge Brief Sources** → **Build Brief Bundle** (Code)
4. **Build Brief Prompt** (Code) — uses `anthropic/claude-haiku-4.5`, strict schema:
   ```json
   { "brief_markdown": "...", "slack_summary": "..." }
   ```
   System prompt: concise UK corporate finance briefing, ONS data is macro context not sector comps.
5. **Brief AI** (HTTP → OpenRouter)
6. **Parse Brief Output** (Code)
7. **Create Brief Folder** + **Create Brief Doc** + **Update Brief Doc** (Google Drive + Docs)
8. **Brief Response** → Slack thread reply with briefing doc URL

---

### 3. Final Reply

All success and error paths funnel into a single **Send Slack Reply** node (Slack `message` operation, `mrkdwn: true`, threaded reply using `thread_ts`). Retry on fail: 2 attempts, 3s wait.

---

## Key Implementation Patterns

### Intent Classification with Structured Output

Always use `response_format.json_schema` with `strict: true` so the model returns machine-parseable JSON without prose. The intent classifier at temperature 0 is deterministic enough to act as a hard router.

```javascript
// Standard JSON extraction helper used in every Parse* node
function parseJson(text) {
  const cleaned = String(text || '').trim()
    .replace(/^```json\s*/i, '').replace(/^```/, '').replace(/```$/, '').trim();
  const first = cleaned.indexOf('{');
  const last = cleaned.lastIndexOf('}');
  const candidate = first >= 0 && last >= first ? cleaned.slice(first, last + 1) : cleaned;
  return JSON.parse(candidate);
}
```

### Parallel Fan-Out → Merge Pattern

When gathering multiple data sources for one company, fire all HTTP requests simultaneously, tag each output with `{ source: 'profile', data: ... }` in a Code node, then use sequential Merge nodes to collect them. The final Bundle Code node iterates `$input.all()` and assembles `bundle.sources[source] = data`.

### Companies House Scoring

The best-match scorer is critical for accuracy. Always apply: active status bonus, exact/prefix/substring title match, UK address hint. This prevents picking dissolved companies or subsidiaries with similar names.

### Research-First Gate for Pitch

Never generate pitch materials from scratch. The pitch pipeline must:
1. Load the company record from Postgres
2. Load the most recent `research` memory text
3. Feed both to the LLM

If either is missing, reply with a helpful error. This prevents hallucinated financials.

### Slide Content Discipline

When generating pitch content, the system prompt must explicitly prohibit narrative paragraphs and require 3–5 bullet points per slide field. Failure to do this results in slide content that overflows text boxes.

---

## Required Credentials

| Service | Credential Type | Notes |
|---------|----------------|-------|
| Slack | `slackApi` | Two accounts: one for webhook trigger (`slackApi WH`), one for sending replies |
| OpenRouter | `openRouterApi` | Routes to Claude Haiku (intent + pitch + brief) and Claude Sonnet (research) |
| Companies House | `httpBasicAuth` | Free API key as username, empty password |
| Firecrawl | `httpHeaderAuth` | `Authorization: Bearer {key}` header |
| Alpha Vantage | None (API key in URL) | Free tier, only used if ticker is known |
| Google Drive | `googleDriveOAuth2Api` | For folder creation and file copy |
| Google Docs | `googleDocsOAuth2Api` | For document creation and content insertion |
| Google Slides | `googleSlidesOAuth2Api` | For placeholder replacement |
| Google Sheets | `googleSheetsOAuth2Api` | For client DB append/update |
| PostgreSQL | `postgres` | Two tables: `aiemp_research_analyst_companies`, `aiemp_research_analyst_research_memory` |

---

## Database Schema

```sql
-- Company master record
CREATE TABLE aiemp_research_analyst_companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name TEXT,
  sector TEXT,
  companies_house_number TEXT UNIQUE,
  registered_address JSONB,
  incorporation_date DATE,
  sic_codes TEXT[],
  directors JSONB,
  market_cap NUMERIC,
  stock_ticker TEXT,
  website_url TEXT,
  profile_doc_url TEXT,
  pitch_deck_url TEXT,
  last_researched_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Research memory store (supports future vector embeddings)
CREATE TABLE aiemp_research_analyst_research_memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID REFERENCES aiemp_research_analyst_companies(id),
  intent TEXT,           -- 'research' | 'pitch'
  content_text TEXT,
  embedding VECTOR(1536), -- NULL until pgvector is wired up
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Google Drive Setup

1. Create a parent folder in Google Drive (e.g., "Finance Research Analyst")
2. Note its folder URL — paste into the `folderId` field of all three `Create * Folder` nodes
3. Create a Google Slides pitch deck template with these exact text placeholders:
   - `{company_name}`, `{sector}`, `{profile_summary}`, `{financials}`, `{opportunity_summary}`, `{comps_note}`
4. Note the Slides template file ID — paste into the `Copy Slides Template` node's `fileId`

---

## Customisation Options

| Change | How |
|--------|-----|
| Replace Slack with Telegram or a web form | Swap the Slack Trigger node; Prepare Context node stays the same |
| Use Supabase instead of Postgres | Replace Postgres nodes with Supabase HTTP nodes|
| Use cheaper LLM (e.g., Mistral, Kimi k2) | Change `model` string in each Build * Prompt node |
| Add vector search to memory | Enable `pgvector`, generate embeddings at Save Research Memory step, query by cosine similarity |
| Add paid deal databases | Insert an additional HTTP source node in the research fan-out and wrap it like the others |
| Expand to 4+ intents | Add a new branch to the Intent Switch node and build a sub-pipeline |

---

## Error Handling Philosophy

Every intent branch has a guard IF node at the top. If the required input is missing or invalid, the branch immediately builds an error `reply_text` and routes to **Send Slack Reply** — the same exit point used by all success paths. This keeps the graph clean and ensures every execution ends with a user-visible message.

Missing-input error messages follow the pattern:
> `"{Intent} requests need a {field}. Example: \`{example phrase}\`."`

---

## Model Selection Rationale

| Step | Model | Why |
|------|-------|-----|
| Intent classification | `claude-haiku-4.5` | Deterministic, cheap, fast; temperature 0 |
| Pitch & briefing synthesis | `claude-haiku-4.5` | Output is compact bullets; Haiku is sufficient |
| Research synthesis | `claude-sonnet-4.5` | Needs richer synthesis across 5 data sources; Sonnet handles nuance better |
