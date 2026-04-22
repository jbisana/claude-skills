# Meta Ads Insights → Google Sheets ETL

Extract Meta (Facebook/Instagram) Ads performance data into Google Sheets for reporting and BI (e.g., Looker Studio).

## 🚀 Key Features
- **Two Operating Modes:** Historical Backfill (chunked into 7-day periods) and Incremental Sync (last 7 days).
- **Multi-Agent Architecture:** Automated API verification, period generation, and parallel data fetching.
- **Robust Sync:** Automatic retries, pagination handling, and zero-spend filtering.
- **Audit Logs:** Detailed logging of skipped or errored periods in separate sheet tabs.

## 🛠 Prerequisites
- **Meta Ads:** Long-lived Access Token (`ads_read` scope) and Ad Account IDs.
- **Google Sheets:** Spreadsheet ID and OAuth2 Access Token with edit permissions.
- **Sheet Tabs:** Four required tabs: `Account_A`, `Account_B`, `Account_A_Log`, and `Account_B_Log`.

## 📂 Project Structure
- `SKILL.md`: Main orchestration logic and configuration schema.
- `agents/api-verifier.md`: Validates credentials and tab existence before execution.
- `agents/period-generator.md`: Splits date ranges into 7-day API-safe chunks.
- `agents/account-fetcher.md`: Handles parallel insights extraction and data cleaning.

## 🔄 Workflow
1. **Verify:** Confirm Meta and Google API access.
2. **Plan:** Generate time-period chunks based on mode (Backfill vs. Incremental).
3. **Fetch:** Run Account A (Campaign level) and Account B (Ad level, daily) fetchers in parallel.
4. **Load:** Append cleaned records to Sheets; log any skips to Audit tabs.
5. **Report:** Provide a summary of rows written and periods processed.
