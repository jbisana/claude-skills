---
name: stale-content-detector
description: >
  Scans a website's sitemap.xml to detect stale pages, analyzes each one
  with Claude for content freshness, logs results to Google Sheets, and sends
  a color-coded HTML digest email summarizing what needs updating.

  Use this skill whenever the user wants to:
  - Audit a website for outdated or stale content
  - Find pages that haven't been updated in X days/months
  - Get AI-powered recommendations on which pages to refresh
  - Set up a recurring content audit and email report
  - Check if blog posts, docs, or landing pages are still accurate
  - Build a content freshness pipeline for their site or a client's site

  The skill uses a multi-agent approach: an API Verifier agent runs first to
  confirm that the sitemap URL is reachable and all required credentials
  (Google Sheets, Gmail/SMTP) are valid. A Sitemap Parser agent then extracts
  stale URLs. Claude analyzes each page's content for freshness. Finally,
  results are logged and an email digest is delivered.
---

# Stale Content Detector

## Overview

This skill runs a full content freshness audit on a website by:

1. **Verifying** the sitemap URL and all API credentials are accessible
2. **Fetching and parsing** the sitemap to find pages not updated within the staleness threshold
3. **Analyzing** each stale page's content using Claude to rate its freshness and suggest specific updates
4. **Logging** results to a Google Sheet for tracking over time
5. **Emailing** a color-coded HTML digest to the configured alert address

The default schedule is weekly (every Monday at 7 AM), but the skill can also be run on-demand for a one-off audit.

---

## Phase 0 — API Verification (Always First)

Before doing anything else, verify that every external service is reachable. Surface all failures together so the user can fix them in one go rather than discovering them one by one.

### Check 1: Sitemap Accessibility

```
GET <SITEMAP_URL>
Accept: application/xml, text/xml
```

Expected: HTTP 200 with an XML body containing `<urlset>` or `<sitemapindex>` elements.

Common failures:
- **404** → sitemap doesn't exist at that path. Common locations to suggest: `/sitemap.xml`, `/sitemap_index.xml`, `/wp-sitemap.xml`
- **403** → sitemap is protected. The user may need to whitelist the IP or use authenticated access.
- **Timeout** → the site may be down or very slow. Retry once after 5 seconds before reporting.
- **Sitemap index** → if the response is a `<sitemapindex>` (a sitemap of sitemaps), fetch and merge the child sitemaps before proceeding.

### Check 2: Google Sheets Access

```
GET https://sheets.googleapis.com/v4/spreadsheets/<SPREADSHEET_ID>
Authorization: Bearer <GOOGLE_ACCESS_TOKEN>
```

Expected: HTTP 200 with the spreadsheet title.

Verify the `ContentAudit` tab exists in `sheets[].properties.title`. If missing, instruct the user to create it with these columns (in order):

`scan_date` | `page_url` | `last_modified` | `days_since_update` | `ai_review`

### Check 3: Email Delivery (Gmail or SMTP)

For **Gmail OAuth2**: call `GET https://gmail.googleapis.com/gmail/v1/users/me/profile` with the token. Expect HTTP 200 with the sender's email address.

For **SMTP**: attempt a connection and EHLO/STARTTLS handshake to the configured SMTP host/port. Do not send a test email — just verify the connection succeeds.

Report all checks together:

```
## API Verification Report

- Sitemap:        ✅ Reachable (247 URLs found)
- Google Sheets:  ✅ Accessible — ContentAudit tab present
- Gmail:          ✅ Authenticated (sender: you@yourdomain.com)

Result: ✅ All checks passed — ready to proceed
```

If any check fails, report `❌ BLOCKED` and stop.

---

## Configuration

| Parameter | Description | Default |
|---|---|---|
| `SITEMAP_URL` | Full URL to the sitemap XML | `https://yoursite.com/sitemap.xml` |
| `STALE_DAYS` | Pages older than this many days are flagged | `180` |
| `MAX_PAGES` | Maximum stale pages to analyze per run | `20` |
| `ALERT_EMAIL` | Email address to receive the digest | — |
| `SPREADSHEET_ID` | Google Sheets document ID for logging | — |
| `GOOGLE_ACCESS_TOKEN` | OAuth2 token for Google Sheets | — |
| `GMAIL_ACCESS_TOKEN` | OAuth2 token for Gmail sending | — |
| `SCAN_MODE` | `scheduled` (weekly) or `on-demand` | `on-demand` |

---

## Phase 1 — Sitemap Parsing

Parse the sitemap XML to extract stale pages.

**Parsing logic:**

For each `<url>` block in the sitemap:
1. Extract `<loc>` (the page URL) — required
2. Extract `<lastmod>` (ISO 8601 date) — optional
3. Compute `daysSinceUpdate = today − lastModDate` in whole days
4. A page is **stale** if `daysSinceUpdate > STALE_DAYS` OR if `<lastmod>` is absent (unknown update date — treat as potentially stale, mark `daysSinceUpdate = -1`)

**Sort** stale pages by `daysSinceUpdate` descending (most stale first), then **cap at `MAX_PAGES`** (default 20). This cap keeps Claude's workload reasonable on large sites.

**Output example:**
```
Found 247 total URLs. 34 are stale (>180 days). Analyzing top 20 most stale.
```

---

## Phase 2 — Content Fetching

For each stale page, fetch its HTML content:

```
GET <page_url>
User-Agent: Mozilla/5.0 (compatible; ContentAuditBot/1.0)
Timeout: 10 seconds
```

Extract from the HTML:
- **Title**: content of the `<title>` tag
- **Body text**: strip all HTML tags from `<body>` content, collapse whitespace. Truncate to the first 1,500 characters — Claude needs enough context to judge freshness but not the entire page.

If a page returns a non-200 status or times out, mark it as `fetch_failed` and still log it to the sheet (with `ai_review = "Could not fetch page content"`). Don't let one broken page abort the whole run.

---

## Phase 3 — Claude Content Freshness Analysis

For each page where content was successfully fetched, invoke Claude as the analysis agent.

**System prompt:**
```
You are a content strategist who audits web pages for freshness and accuracy.
Be practical and specific. Only flag things that genuinely need updating — not
stylistic preferences or minor grammar. Your goal is to help the site owner
prioritize their content refresh backlog.
```

**User prompt:**
```
Review this webpage for content freshness. It was last modified {daysSinceUpdate} days ago.

URL: {url}
Title: {title}
Content preview: {bodyText}

Analyze:
1. Does the content contain outdated references (old dates, deprecated tools, outdated pricing, dead links to old resources)?
2. Is the topic still relevant, or has the industry significantly moved on?
3. Priority level for refresh:
   - LOW: Still accurate, minor polish only
   - MEDIUM: Some outdated elements but core content holds
   - HIGH: Significantly outdated, misleading in parts
   - CRITICAL: Actively wrong or harmful to publish
4. What specifically should be updated? (1-2 concrete sentences)

Keep your total response to 4-5 sentences.
```

The response from Claude is the `ai_review` value stored per page.

**Why Claude is the right choice here:** Unlike a rules-based system, Claude can read the actual page content and reason about whether "2021 pricing" or a reference to a deprecated API version is genuinely stale — not just flag pages based on date alone. This produces actionable, specific recommendations rather than generic "this page is old" notices.

---

## Phase 4 — Logging to Google Sheets

After each page is analyzed, append a row to the `ContentAudit` tab:

```
POST https://sheets.googleapis.com/v4/spreadsheets/<SPREADSHEET_ID>/values/ContentAudit!A1:append
  ?valueInputOption=RAW
  &insertDataOption=INSERT_ROWS
Authorization: Bearer <GOOGLE_ACCESS_TOKEN>

{
  "values": [[
    "<ISO timestamp of scan>",
    "<page_url>",
    "<lastModified or 'unknown'>",
    "<daysSinceUpdate or -1>",
    "<aiReview>"
  ]]
}
```

Log each page as it's analyzed rather than batching at the end — this way partial runs still produce useful data.

---

## Phase 5 — Email Digest

After all pages are analyzed, compose and send a color-coded HTML digest.

### Priority color coding

| Staleness | Badge color |
|---|---|
| > 365 days | 🔴 Red `#e74c3c` |
| 271–365 days | 🟠 Orange `#e67e22` |
| 181–270 days | 🟡 Yellow `#f1c40f` |
| Unknown (`-1`) | 🟠 Orange `#e67e22` |

### Email structure

```html
Subject: Weekly Stale Content Report – {YYYY-MM-DD}

[Header: "Stale Content Audit Report"]
[Summary: "X pages flagged for review"]

For each page (most stale first):
  [Colored left-border card]
  [Page path (e.g., /blog/my-post)]
  [Last updated: N days ago — colored to match staleness]
  [Claude's review text]

[Footer: threshold reminder + link to Google Sheet]
```

If zero stale pages are found, send a short "all clear" email rather than skipping it — this confirms the check ran successfully.

---

## Multi-Agent Architecture

```
Orchestrator
│
├── [Phase 0] API Verifier Agent
│     ├── GET sitemap URL → verify reachable + count URLs
│     ├── GET Google Sheets → verify accessible + ContentAudit tab exists
│     └── GET Gmail profile → verify OAuth token valid
│     ↓ (halt on any ❌)
│
├── [Phase 1] Sitemap Parser Agent
│     ├── Parse XML → extract (url, lastmod) pairs
│     ├── Filter stale pages (> STALE_DAYS or no lastmod)
│     ├── Sort most-stale-first
│     └── Cap at MAX_PAGES
│     ↓
│
├── [Phase 2+3] Content Analyzer Agent  (one invocation per stale page, sequential)
│     ├── Fetch page HTML
│     ├── Extract title + body text (truncate to 1500 chars)
│     ├── Call Claude with freshness analysis prompt
│     └── Emit: { url, lastModified, daysSinceUpdate, aiReview }
│     ↓
│
├── [Phase 4] Sheet Logger Agent
│     └── Append each analyzed page row to ContentAudit tab
│     ↓
│
└── [Phase 5] Email Composer Agent
      ├── Aggregate all rows
      ├── Build color-coded HTML email body
      └── Send via Gmail to ALERT_EMAIL
```

> **Why sequential for page analysis?** Fetching and analyzing pages in parallel would be faster but risks triggering rate limits on the target site and on Claude's API. Sequential processing with no artificial delays is a reasonable default. For sites with > 50 stale pages, consider batching 5 pages per Claude call to improve throughput.

---

## Completion Report

After the email is sent, report back:

```
✅ Stale Content Audit Complete

Site:           https://yoursite.com
Pages scanned:  247 total in sitemap
Stale pages:    34 (threshold: 180 days)
Analyzed:       20 (capped at MAX_PAGES)

Priority breakdown:
  🔴 CRITICAL:  2 pages
  🟠 HIGH:      7 pages
  🟡 MEDIUM:   8 pages
  ✅ LOW:        3 pages

Results logged to: Google Sheets (ContentAudit tab)
Digest sent to:    you@yourdomain.com

Most urgent page: /blog/setup-guide (847 days since update)
  → Claude's verdict: "References deprecated API v1 endpoints that no longer
    exist; update to v3 and revise the authentication section."
```

---

## Known Limitations & Gotchas

- **Sitemap `<lastmod>` accuracy:** Many CMSes update `<lastmod>` whenever any site change occurs (even unrelated ones), causing false negatives. Claude's actual content analysis helps compensate — a page might be recently "modified" but still contain stale content.
- **JavaScript-rendered pages:** The fetch step retrieves raw HTML. Pages that require JavaScript to render meaningful content will return a sparse body, leading to weak AI analysis. For SPAs, recommend the user add a static sitemap with accurate `<lastmod>` dates.
- **Gmail OAuth token expiry:** Google OAuth tokens expire after 1 hour. For scheduled weekly runs, use a refresh token flow or a service account instead of a short-lived access token.
- **MAX_PAGES cap:** The 20-page default keeps each run fast and cheap. Increase it for thorough quarterly audits; lower it for quick weekly pulses on large sites.
- **Append-only logging:** Re-running over the same week creates duplicate rows. Consider filtering by `scan_date` before appending, or deduplicate in the sheet with a formula.
