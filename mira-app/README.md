# Mira — LoopBack's conversational layer

Mira is the Slack-facing half of LoopBack. It listens for `@Mira` mentions,
classifies them with Claude, queries the Knowledge Vault for existing answers,
and posts a live-updating task card in the thread.

## Week 1 scope (Days 1-5) — what's implemented

| Step | What happens |
|------|-------------|
| `@Mira` mention | Bolt picks up the `app_mention` event |
| Intent classification | Claude decides QUESTION vs NOISE; noise is silently ignored |
| Draft card | Posted immediately in-thread so the user sees instant feedback |
| Vault search | `VaultClient.search()` queries the Knowledge Vault |
| Vault upsert | The new question is recorded via `VaultClient.upsert_entry()` |
| Result found | Card updates to `pending_confirm` with the suggested answer + Confirm / Not Helpful buttons |
| No result | Card updates to `human_working` so a teammate knows to follow up |

What's not here yet: button action handlers, resolution detection,
App Home Dashboard (Week 3).

## Project structure

```
mira-app/
├── app.py                      # entry point, starts the Bolt app
├── config.py                   # loads + validates env vars
├── handlers/
│   └── mention_handler.py      # @Mira event listener + vault query flow
├── services/
│   ├── intent.py               # Claude-based QUESTION/NOISE classification
│   ├── task_card.py            # Block Kit card builder (all statuses)
│   └── vault_client.py         # thin wrapper around Knowledge Vault API
├── dashboard/
│   └── home_view.py            # App Home (Week 3, placeholder)
├── requirements.txt
└── .env.example
```

## Setup

1. **Create a Slack app** at https://api.slack.com/apps
   - Enable **Socket Mode** (Settings → Socket Mode → toggle on)
   - Under **OAuth & Permissions**, add `app_mentions:read` and `chat:write`
     bot token scopes, then install the app to your workspace
   - Under **Event Subscriptions**, subscribe to the `app_mention` bot event
   - Under **Basic Information → App-Level Tokens**, generate a token with
     the `connections:write` scope — this is your `SLACK_APP_TOKEN`

2. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Fill in SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ANTHROPIC_API_KEY
   # Set VAULT_STUB=true to run without the real Knowledge Vault package
   ```

4. **Run**
   ```bash
   python app.py
   ```
   You should see `Mira is running. Waiting for @ mentions...`

5. **Test**
   In any channel Mira's been invited to:
   - `@Mira how do I submit expenses?` → draft card → searching → answer or human_working
   - `@Mira thanks!` → no response (classified as noise)
