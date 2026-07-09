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
from handlers.action_handler import register_action_handlers
from handlers.resolution_handler import register_resolution_handler
from dashboard.home_view import register_home_handler

# Fetch bot user ID at startup so all handlers can filter out Mira's own messages
_app = App(token=SLACK_BOT_TOKEN)
_bot_user_id = _app.client.auth_test()["user_id"]

app = _app

register_mention_handler(app)
register_action_handlers(app)
register_home_handler(app)
register_resolution_handler(app, _bot_user_id)


if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    print(f"Mira is running (bot_user_id={_bot_user_id}). Listening to all channels...")
    handler.start()
