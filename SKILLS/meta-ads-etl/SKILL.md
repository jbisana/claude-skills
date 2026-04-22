---
name: meta-ads-etl
description: >
  Extracts Meta (Facebook) Ads performance data and loads it into Google Sheets
  for reporting or BI use (e.g., Looker Studio). Supports two operating modes
  in a single run: Historical Backfill (pull any date range, chunked into 7-day
  periods to stay within API limits) and Incremental Sync (last 7 days,
  suitable for scheduled/recurring runs).

  Use this skill whenever the user wants to:
  - Pull Meta Ads insights data into a spreadsheet
  - Sync Facebook/Instagram ad performance to Google Sheets
  - Backfill historical Meta campaign, ad-set, or ad-level metrics
  - Schedule recurring Meta Ads reporting into a Google Sheet
  - Extract spend, impressions, CTR, CPC, CPM, actions, or conversion data from Meta

  The skill uses a multi-agent approach: an API Verifier agent runs first to confirm
  that both the Meta Graph API token and Google Sheets credentials are valid before
  any data is fetched. Two fetcher agents then run in parallel — one per ad account —
  so both accounts are synced concurrently.
---

# Meta Ads Insights → Google Sheets ETL

## Overview

This skill orchestrates an end-to-end ETL pipeline that:

1. **Verifies** both APIs before doing anything else
2. **Generates** time periods (weekly chunks) from the requested date range
3. **Fetches** Meta Ads Insights from each ad account in parallel
4. **Writes** the cleaned rows to Google Sheets, skipping zero-spend records
5. **Logs** any skipped or errored periods to a separate log tab for auditability

---

## Phase 0 — API Verification (Always First)

Before fetching any data, verify that both required APIs are accessible. If either check fails, halt immediately and report what's broken with a clear remediation step. Never proceed past this phase on a failed check.

### Meta Graph API Check

Make a lightweight test call using the user's long-lived access token:

```
GET https://graph.facebook.com/v24.0/me?fields=id,name
Authorization: Bearer <META_ACCESS_TOKEN>
```

Expected: HTTP 200 with `{ "id": "...", "name": "..." }`.

Common failures to catch and explain:
- **190 / OAuthException** → token is expired or revoked. The user needs a new long-lived token with `ads_read` scope.
- **100 / Invalid parameter** → malformed token or wrong API version.
- **4 / Application request limit** → rate limited; advise the user to wait or reduce request frequency.

After the token passes, also verify the ad account IDs are accessible:

```
GET https://graph.facebook.com/v24.0/<ACT_ID>?fields=id,name,account_status
```

For each configured account ID. Confirm `account_status` is `1` (ACTIVE) and the token has read access.

### Google Sheets Check

Attempt to read the spreadsheet metadata:

```
GET https://sheets.googleapis.com/v4/spreadsheets/<SPREADSHEET_ID>
Authorization: Bearer <GOOGLE_ACCESS_TOKEN>
```

Expected: HTTP 200 with the spreadsheet title.

Verify all four required sheet tabs exist in the `sheets[].properties.title` list:
- `Account_A`
- `Account_B`
- `Account_A_Log`
- `Account_B_Log`

If a tab is missing, report which ones are absent and instruct the user to create them before continuing.

---

## Configuration

Collect from the user (or infer from context) before proceeding:

| Parameter | Description | Example |
|---|---|---|
| `META_ACCESS_TOKEN` | Long-lived Meta User Access Token with `ads_read` | `EAABwzLixnjY...` |
| `ACT_ID_A` | Meta Ad Account ID for Account A | `act_123456789` |
| `ACT_ID_B` | Meta Ad Account ID for Account B | `act_987654321` |
| `SPREADSHEET_ID` | Google Sheets document ID | `1BxiMVs0XRA5nF...` |
| `GOOGLE_ACCESS_TOKEN` | OAuth2 access token for Google Sheets API | `ya29.a0...` |
| `MODE` | `backfill` or `incremental` | `backfill` |
| `START_DATE` | Only for `backfill` mode (YYYY-MM-DD) | `2024-01-01` |
| `END_DATE` | Only for `backfill` mode (YYYY-MM-DD) | `2024-12-31` |

For `incremental` mode, the date range is computed automatically as `[today − 7 days, today]`.

---

## Phase 1 — Generate Time Periods

Split the date range into non-overlapping 7-day windows (the last window is clamped to the end date if shorter than 7 days):

```
Input:  start_date=2024-01-01, end_date=2024-01-21
Output: [
  { since: "2024-01-01", until: "2024-01-07" },
  { since: "2024-01-08", until: "2024-01-14" },
  { since: "2024-01-15", until: "2024-01-21" }
]
```

The chunking is important: the Meta Ads Insights API can throttle or time out on large date ranges. Smaller windows also make partial failures easier to recover from — if one window errors, you only need to re-run that chunk.

For `incremental` mode, there is always exactly one period: the last 7 days.

---

## Phase 2 — Parallel Account Fetching

Spawn two fetcher agents simultaneously, one per ad account. They share the same list of time periods but hit different ad account endpoints with different granularity settings.

> Why parallel? The two accounts are independent — there's no data dependency between them. Running them in parallel roughly halves the total wall-clock time.

### Agent: Account A Fetcher (Campaign Level)

For each period `{ since, until }`:

**API call:**
```
GET https://graph.facebook.com/v24.0/<ACT_ID_A>/insights
  ?fields=date_start,date_stop,account_id,account_name,campaign_id,campaign_name,
          adset_id,adset_name,ad_id,ad_name,objective,buying_type,
          spend,impressions,reach,frequency,clicks,unique_clicks,
          ctr,cpc,cpm,actions,cost_per_action_type,action_values,
          quality_ranking,engagement_rate_ranking,conversion_rate_ranking
  &level=campaign
  &time_range[since]=<since>
  &time_range[until]=<until>
Authorization: Bearer <META_ACCESS_TOKEN>
```

**Pagination:** Follow `paging.next` until it is absent or empty. Wait 3 seconds between page requests to respect rate limits.

**Retry policy:** Up to 5 retries with 3-second back-off on network errors or HTTP 5xx. Use `continueOnFail` semantics — a failed period should be logged, not crash the whole run.

**Response validation:** If the response has no `data` array, or `data.length === 0`, log the period as skipped (see Phase 3) and move on.

**Data cleaning:** For each row in `data`:
- Cast `spend`, `impressions`, `reach`, `frequency`, `clicks`, `unique_clicks`, `ctr`, `cpc`, `cpm` to `Number` (default `0` if missing/null).
- Leave `actions`, `cost_per_action_type`, `action_values` as arrays (or `[]`).
- Leave quality ranking fields as strings (or `''`).

**Zero-spend filter:** Skip rows where `spend === 0` — they represent inactive campaigns with no delivery and inflate row counts without adding analytical value.

**Output:** Append surviving rows to the `Account_A` tab in the spreadsheet. See the [Schema Reference](#schema-reference) below.

---

### Agent: Account B Fetcher (Ad Level, Daily Breakdown)

Same structure as Account A, but with two key differences:

**API differences:**
- `&level=ad` instead of `level=campaign`
- `&time_increment=1` added — this requests a separate row for each day within the period, rather than one aggregated row per period

**Output:** Append to the `Account_B` tab. Same column schema, same zero-spend filter.

---

## Phase 3 — Logging Skipped Periods

Any period that returns no data or an API error should be recorded in the log tab rather than silently dropped. This makes re-runs and debugging much easier.

**Log row schema:**

| Column | Value |
|---|---|
| `status` | `"skipped"` |
| `reason` | Human-readable explanation (e.g., "API returned empty data array") |
| `account` | `"Account A"` or `"Account B"` |
| `since` | Period start date |
| `until` | Period end date |
| `execution_id` | A unique ID for the current run (use a UUID or timestamp) |
| `timestamp` | ISO 8601 UTC timestamp of when the skip was recorded |

Write Account A skips to `Account_A_Log` and Account B skips to `Account_B_Log`.

---

## Phase 4 — Completion Report

After both fetcher agents finish, produce a summary:

```
✅ Meta Ads ETL Complete

Mode:        Backfill
Date range:  2024-01-01 → 2024-12-31
Periods:     52 weekly chunks

Account A (Campaign level):
  Rows written:   1,847
  Periods skipped: 3

Account B (Ad level, daily):
  Rows written:   12,394
  Periods skipped: 1

Spreadsheet: https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>

⚠️  Note: This is an append-only operation. If you re-run the same date
    range, duplicate rows will be created. Deduplicate by (account_id,
    campaign_id, date_start, date_stop) if needed before connecting
    a BI tool.
```

---

## Schema Reference

Both sheet tabs use the same column layout:

| Column | Type | Notes |
|---|---|---|
| `date_start` | string | YYYY-MM-DD |
| `date_stop` | string | YYYY-MM-DD |
| `account_id` | string | |
| `account_name` | string | |
| `campaign_id` | string | |
| `campaign_name` | string | |
| `adset_id` | string | |
| `adset_name` | string | |
| `ad_id` | string | |
| `ad_name` | string | |
| `objective` | string | |
| `buying_type` | string | |
| `spend` | number | USD, 2 decimal places |
| `impressions` | number | |
| `reach` | number | |
| `frequency` | number | |
| `clicks` | number | |
| `unique_clicks` | number | |
| `ctr` | number | Click-through rate |
| `cpc` | number | Cost per click |
| `cpm` | number | Cost per 1,000 impressions |
| `actions` | JSON array | Conversion events (serialized) |
| `cost_per_action_type` | JSON array | CPA breakdown (serialized) |
| `action_values` | JSON array | Revenue attribution (serialized) |
| `quality_ranking` | string | ABOVE_AVERAGE / AVERAGE / BELOW_AVERAGE |
| `engagement_rate_ranking` | string | |
| `conversion_rate_ranking` | string | |

> **Tip:** When connecting Google Sheets to Looker Studio, use a calculated field to parse the `actions` JSON column rather than trying to display it raw.

---

## Multi-Agent Architecture

```
Orchestrator
│
├── [Phase 0] API Verifier Agent
│     ├── Check Meta Graph API token → GET /me
│     ├── Check each ad account → GET /act_X?fields=id,name,account_status
│     └── Check Google Sheets → GET /spreadsheets/<ID> + verify tabs
│     ↓ (halt on any failure)
│
├── [Phase 1] Period Generator
│     └── Produce list of { since, until } weekly windows
│     ↓
│
├── [Phase 2a] Account A Fetcher Agent  ←──── runs in parallel ────→  [Phase 2b] Account B Fetcher Agent
│     For each period:                                                   For each period:
│     ├── Fetch /act_A/insights (level=campaign)                        ├── Fetch /act_B/insights (level=ad, time_increment=1)
│     ├── Paginate to completion                                         ├── Paginate to completion
│     ├── Clean + filter (drop spend=0)                                 ├── Clean + filter (drop spend=0)
│     ├── Append to Account_A tab                                       ├── Append to Account_B tab
│     └── Log skipped periods → Account_A_Log                          └── Log skipped periods → Account_B_Log
│
└── [Phase 4] Orchestrator collects results → Completion Report
```

---

## Known Limitations & Gotchas

- **Append-only writes:** Re-running over the same date range creates duplicate rows. Advise users to track which periods have been synced and only run new ones, or to add a deduplication step downstream.
- **Token expiry:** Meta long-lived tokens expire after ~60 days. The API Verifier will catch this, but mention it proactively so users know to rotate tokens.
- **Rate limits:** The 3-second inter-page delay is conservative but necessary. Very large ad accounts with many campaigns can still hit rate limits; if the Verifier detects throttling, surface this before starting the backfill.
- **Actions column:** The `actions` field is a nested array of `{ action_type, value }` objects. It's stored as-is (JSON-serialized string) in the sheet. Users who need specific action types (e.g., `purchase`, `lead`) will need to parse this column in their BI tool or request a custom extraction.
- **Historical data availability:** Meta Ads Insights data is available for approximately 37 months. Requests beyond this window return empty arrays, which will be logged as skipped periods.
