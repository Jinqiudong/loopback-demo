# Mira (LoopBack's conversational layer)

Week 1, Day 1-2 scope: the minimal skeleton that proves Slack -> Claude ->
Slack works end to end. No Knowledge Vault integration yet (Days 3-5),
no resolution detection yet (Week 2).

## What this does right now

1. Listens for `@Mira` mentions in Slack.
2. Classifies the message as a real question or just noise (Claude API).
3. If it's a question, posts a draft-status task card in the same thread.
4. If it's noise, stays quiet.

That's it. No Vault lookups, no escalation, no confirmation logic yet --
those come in Days 3-5 and Week 2 per the implementation plan.

## Project structure

```
mira/
├── app.py                      # entry point, starts the Bolt app
├── config.py                   # loads + validates env vars
├── handlers/
│   └── mention_handler.py      # the @Mira event listener
├── services/
│   ├── intent.py                # Claude-based question/noise classification
│   └── task_card.py             # Block Kit task card builder
├── requirements.txt
└── .env.example
```

## Setup

1. **Create a Slack app** at https://api.slack.com/apps
   - Enable **Socket Mode** (Settings → Socket Mode → toggle on)
   - Under **OAuth & Permissions**, add the `app_mentions:read` and
     `chat:write` bot token scopes, then install the app to your workspace
   - Under **Event Subscriptions**, subscribe to the `app_mention` bot event
   - Under **Basic Information → App-Level Tokens**, generate a token with
     the `connections:write` scope -- this is your `SLACK_APP_TOKEN`
   - Your bot token (`xoxb-...`) is under **OAuth & Permissions**

2. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # then fill in SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ANTHROPIC_API_KEY
   ```

4. **Run it**
   ```bash
   python app.py
   ```
   You should see `Mira is running. Waiting for @ mentions...`

5. **Test it**
   In any channel Mira's been added to, try:
   - `@Mira how do I submit expenses?` → should get a draft task card back
   - `@Mira thanks!` → should get no response (classified as noise)

## What's next (Days 3-5, per the implementation plan)

- Wire up Vault-priority query logic (against teammate's mock API first)
- No Vault match → search Slack history
- Still no match → escalate to a resolver, task card status switches

See `LoopBack_Implementation_Plan.docx` for the full timeline.
