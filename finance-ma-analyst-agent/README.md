# Finance M&A Analyst Agent

A specialized AI automation designed to act as a junior research analyst for UK boutique M&A firms. It handles time-consuming data gathering and document creation directly through Slack.

## Core Capabilities
The agent recognizes three distinct requests in Slack:

1.  **Company Research**: Gathers live data from Companies House, news, and market sources to build a comprehensive profile in Google Docs.
2.  **Pitch Deck Generation**: Uses existing research to automatically populate a Google Slides presentation and draft a press release.
3.  **Industry Briefing**: Summarizes recent UK sector trends and economic news into a concise briefing document.

## How to Interact
Simply message the agent in its Slack channel using these formats:
*   **For Research**: `Research [Company Name], [Sector]`
*   **For a Pitch**: `Prepare pitch for [Company Name]`
*   **For a Briefing**: `Industry briefing [Sector]`

## Key Value
*   **Official Sources**: Pulls verified data from Companies House and real-time financial news.
*   **Smart Synthesis**: Uses advanced AI (Claude/GPT) to turn raw data into professional, slide-ready bullet points and summaries.
*   **Automated Storage**: Every request automatically creates a organized project folder in Google Drive.
*   **Reliability**: Includes built-in "guards" to prevent the AI from inventing facts or generating pitches without prior research.

## Requirements
To deploy this automation, you will need access to:
*   **Slack** (for the interface)
*   **Google Workspace** (Drive, Docs, Slides, Sheets)
*   **Data APIs**: Companies House, Firecrawl, and Alpha Vantage
*   **AI Access**: OpenRouter (Claude/GPT)
*   **Database**: PostgreSQL
