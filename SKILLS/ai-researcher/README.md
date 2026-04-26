# AI Researcher Skill

The **AI Researcher** skill empowers CLAUDE CLI to conduct deep, autonomous research on any topic and deliver a polished, Slack-ready report. It is designed for analysts, researchers, and teams who need synthesized, high-quality insights from the web delivered directly to their communication channels.

## 🚀 Features

- **Autonomous Research**: Automatically identifies, fetches, and synthesizes content from the most authoritative web sources.
- **Targeted Synthesis**: Tailors findings to a specific audience, ensuring the report is relevant and actionable.
- **Slack Optimized**: Uses Slack-specific `mrkdwn` (`*bold*`, `_italic_`, `•` bullets) for perfect rendering in Slack channels.
- **Direct Slack Integration**: Includes a built-in script to push reports directly to Slack via webhooks.

## 🛠️ How It Works

1.  **Requirement Gathering**: The skill captures the "Research Goal" and "Target Audience" to frame the investigation.
2.  **Discovery**: Uses `google_web_search` to find the top 3-5 relevant sources.
3.  **Deep Read**: Uses `web_fetch` to extract full content from those sources, ensuring accuracy beyond search snippets.
4.  **Report Generation**: Synthesizes the data into a structured Slack-formatted report.
5.  **Delivery**: Outputs the report and, if a `SLACK_WEBHOOK_URL` is provided, transmits it to Slack.

## 📝 Report Format

The skill generates a consistent, scannable report:
- **🔍 Research Report**: Clear topic heading.
- **TL;DR**: 3-4 high-level bullet points.
- **Key Findings**: Detailed numbered list of critical insights.
- **Sources**: Direct URLs to the investigated material.
- **Recommended Next Step**: A tailored, actionable recommendation.

## ⚙️ Configuration & Usage

### Triggering the Skill
Invoke the skill by asking for "research," "investigation," "deep dives," or a "research report."

### Slack Integration
To enable automated posting to Slack, set your webhook URL as an environment variable:
- `SLACK_WEBHOOK_URL`: Your Incoming Webhook URL from Slack.

The skill utilizes the included Python bridge:
```bash
python scripts/send_to_slack.py --webhook "$SLACK_WEBHOOK_URL" --text "$REPORT_CONTENT"
```

### Prerequisites
- Python 3.x
- `requests` library (`pip install requests`)

## 📂 Project Structure

- `SKILL.md`: The core skill definition and system prompts.
- `scripts/send_to_slack.py`: Python utility for webhook delivery.
- `assets/`: Supplemental visuals or icons.
- `references/`: Documentation and research templates.
