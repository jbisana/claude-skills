import argparse
import requests
import json
import sys

def send_to_slack(webhook_url, text):
    payload = {"text": text}
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            print(f"Error sending to Slack: {response.status_code} - {response.text}")
            sys.exit(1)
        print("Successfully sent report to Slack.")
    except Exception as e:
        print(f"Failed to send to Slack: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send text to a Slack webhook.")
    parser.add_argument("--webhook", required=True, help="Slack Webhook URL")
    parser.add_argument("--text", required=True, help="Text to send")
    
    args = parser.parse_args()
    send_to_slack(args.webhook, args.text)
