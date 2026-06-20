"""
Entry point. Run with: python app.py

Uses Socket Mode so this can run locally during development without
needing a public URL / ngrok tunnel for Slack's Events API to hit.
Switch to HTTP mode + a real endpoint once this deploys to Railway.
"""

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN
from handlers.mention_handler import register_mention_handler

app = App(token=SLACK_BOT_TOKEN)

register_mention_handler(app)


if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    print("Mira is running. Waiting for @ mentions...")
    handler.start()
