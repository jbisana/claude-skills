# Stale Content Detector

A multi-agent skill that audits website freshness by scanning sitemaps, analyzing content with Claude, and delivering actionable reports.

## Core Features
- **Sitemap Analysis:** Automatically parses `sitemap.xml` to identify pages older than a specific threshold.
- **AI-Powered Freshness Check:** Claude analyzes page content for outdated references, dead links, and deprecated information.
- **Automated Logging:** Saves all audit results to a Google Sheet for historical tracking.
- **Alerting:** Sends a color-coded HTML digest email with prioritized refresh recommendations.
- **Safety First:** Includes an API Verifier agent to validate all credentials (Sitemap, Google Sheets, Gmail) before execution.

## How It Works
1. **Verify:** Checks access to the Sitemap, Google Sheets API, and Gmail/SMTP.
2. **Parse:** Extracts URLs from the sitemap and filters for "stale" pages based on `lastmod`.
3. **Analyze:** Fetches page content and uses Claude to categorize the refresh priority (Low to Critical).
4. **Report:** Logs data to Sheets and sends a summary email to the site owner.

## Configuration
| Parameter | Description | Default |
|---|---|---|
| `SITEMAP_URL` | URL to the site's `sitemap.xml` | — |
| `STALE_DAYS` | Threshold for flagging content as old | `180` |
| `MAX_PAGES` | Max pages to analyze per run | `20` |
| `ALERT_EMAIL` | Destination for the HTML report | — |
| `SPREADSHEET_ID`| Google Sheets ID for logging | — |

## Multi-Agent Architecture
- **API Verifier:** Validates environment and connectivity.
- **Sitemap Parser:** Handles XML extraction and filtering.
- **Content Analyzer:** Manages page fetching and Claude-powered analysis.
- **Sheet Logger:** Records results in Google Sheets.
- **Email Composer:** Generates and sends the final HTML digest.
