# Mira — LoopBack's conversational layer

Mira is the Slack-facing half of LoopBack. She listens for `@Mira` mentions,
runs a three-tier search (Vault → GitHub MCP + Slack history → human escalation),
posts a live-updating task card, and generates Enhancement Proposals from patterns.

## What's implemented

| Feature | Status |
|---------|--------|
| @Mira mention → intent classification (Claude) | ✅ |
| Tier 1: Knowledge Vault semantic search | ✅ |
| Tier 2: Slack Real-Time Search API | ✅ |
| Tier 2: GitHub MCP (reads loopback-analytics) | ✅ |
| Pre-escalation direction check with requester | ✅ |
| Block Kit task card — all 7 states + direction_check | ✅ |
| Resolution detection (listens for resolver replies) | ✅ |
| Button handlers (confirm / not helpful) | ✅ |
| App Home Dashboard (Block Kit, stub data) | ✅ |
| Enhancement Proposal engine (@Mira analyze) | ✅ |
| Slack Canvas Dashboard | ⏳ |
| Real Vault connected (needs Supabase config) | ⏳ |

## Project structure

```
mira-app/
├── app.py                       # entry point + proposal button handlers
├── config.py                    # env var loading + validation
├── handlers/
│   ├── mention_handler.py       # @Mira listener — full 3-tier flow
│   ├── action_handler.py        # Confirm / Not Helpful button actions
│   ├── resolution_handler.py    # detects resolver replies in thread
│   └── direction_handler.py     # pre-escalation direction confirmation
├── services/
│   ├── intent.py                # Claude QUESTION/NOISE classification
│   ├── task_card.py             # Block Kit builder (8 states including direction_check)
│   ├── vault_client.py          # 4-function API wrapper for vault-service
│   ├── slack_search.py          # Real-Time Search API (needs SLACK_USER_TOKEN)
│   └── mcp_github.py            # GitHub MCP — reads loopback-analytics repo
├── pm/
│   └── proposal_engine.py       # Claude-powered Enhancement Proposal generation
├── dashboard/
│   └── home_view.py             # App Home Dashboard (Block Kit)
├── requirements.txt
└── .env.example
```

## Setup

**1. Create a Slack app** at https://api.slack.com/apps
- Enable **Socket Mode**
- Bot Token Scopes: `app_mentions:read`, `chat:write`, `channels:history`, `im:write`
- User Token Scopes: `search:read`
- Event Subscriptions → Subscribe to bot events: `app_mention`, `message.channels`, `app_home_opened`
- App Home → enable Home Tab

**2. Install dependencies**
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e ../vault-service   # once Supabase is configured
```

**3. Configure .env**
```bash
cp .env.example .env
# Required: SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ANTHROPIC_API_KEY
# Vault:    SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY, then VAULT_STUB=false
# Search:   SLACK_USER_TOKEN (xoxp-...)
# MCP:      GITHUB_TOKEN, GITHUB_ANALYTICS_REPO=Jinqiudong/loopback-analytics
```

**4. Run**
```bash
python app.py
```

**5. Test**
```
@Mira we're seeing an unexpected drop in our approval rate   → direction_check → human_working → verified
@Mira how do I submit expenses?                              → human_working → resolver answers → verified
@Mira analyze                                                → Enhancement Proposal card
@Mira thanks!                                                → no response (noise)
```
