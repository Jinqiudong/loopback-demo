# LoopBack — Repo Structure

```
loopback-demo/
│
├── README.md                          Project overview
├── ARCHITECTURE.md                    System architecture + component descriptions
├── repo-structure.md                  This file
├── .gitignore
├── Procfile                           Railway entry point: web: python mira-app/app.py
├── railway.toml                       Railway build + deploy config
├── requirements.txt                   Root-level deps for Railway (installs vault-service)
├── runtime.txt                        Python version pin for Railway
│
├── mira-app/                          Conversational layer — Slack Bolt app
│   ├── app.py                         Entry point — starts the Slack Bolt app (Socket Mode)
│   ├── config.py                      Loads + validates env vars (fail-fast on startup)
│   ├── requirements.txt
│   │
│   ├── handlers/
│   │   ├── mention_handler.py         @Mira listener — routes INSIGHTS to Canvas period
│   │   │                              selector; QUESTION to the same 3-tier flow as proactive
│   │   ├── resolution_handler.py      ALL message events — four sub-flows:
│   │   │                              1. Proactive detection: top-level question, no @Mira
│   │   │                                 → full 3-tier Vault / Claude / human flow
│   │   │                              2. direction_check: requester confirms Claude findings
│   │   │                              3. Resolution detection: resolver replies in thread
│   │   │                              4. Ambient detection: untracked Q&A resolved → nudge to save
│   │   └── action_handler.py          Button actions: vault_confirm / vault_not_helpful /
│   │                                  insights_this_month|quarter|year / ambient_save
│   │
│   ├── services/
│   │   ├── intent.py                  Claude classifiers — QUESTION/INSIGHTS/NOISE,
│   │   │                              RESOLVED/ONGOING, ESCALATE/RESOLVED/UNCLEAR,
│   │   │                              DEFLECTION/ANSWER — all max_tokens=10, fail-closed
│   │   ├── investigator.py            Claude tool-use agentic loop (MCP pattern)
│   │   │                              Tools: search_github, read_file, search_slack_history
│   │   ├── task_card.py               Block Kit builder — 7 states:
│   │   │                              draft → ai_searching → direction_check →
│   │   │                              human_working → pending_confirm → verified / escalate
│   │   ├── vault_client.py            Python wrapper — 5-function API to vault-service
│   │   ├── slack_search.py            Slack Real-Time Search API
│   │   ├── mcp_github.py              GitHub tool implementations for investigator
│   │   └── reactions.py               Slack reaction helpers (status → emoji mapping)
│   │
│   ├── pm/
│   │   └── proposal_engine.py         Claude-powered pattern analysis → Enhancement
│   │                                  Opportunities (doc / code / ux / process / product)
│   │
│   └── dashboard/
│       ├── home_view.py               App Home tab (Block Kit)
│       └── channel_canvas.py          Channel Insights Canvas — four sections:
│                                      📊 Impact · 🧠 Knowledge Vault · ❓ Open · 🌱 Opportunities
│                                      Semantic clustering, answer-as-title, user name lookup,
│                                      auto-refreshes on every vault_confirm
│
└── vault-service/                     Storage + verification layer
    ├── requirements.txt
    ├── setup.py                       pip install -e — makes knowledge_vault importable
    ├── schema.sql                     CREATE TABLE for task_cards + vault_entries
    ├── embeddings.py                  OpenAI text-embedding-3-small wrapper
    ├── confidence.py                  Confidence scoring + accumulation logic
    ├── smoke_test.py                  End-to-end test against real Supabase
    │
    ├── knowledge_vault/
    │   └── __init__.py                Public API — 5 functions:
    │                                  create_task_card, search_vault, upsert_vault_entry,
    │                                  update_status, get_channel_task_cards
    │                                  All Supabase access lives here
    │
    └── api/                           Internal modules (called by knowledge_vault/__init__.py)
        ├── search_vault.py            Semantic search against vault_entries
        ├── upsert_vault_entry.py      Write/update entry, applies three-signal logic
        └── update_status.py           Status field update on task_cards
```

---

## Status Enum

| Value | Meaning |
|-------|---------|
| `draft` | Just created, no Vault check yet |
| `ai_searching` | Mira is querying the Vault + investigating |
| `direction_check` | Claude found context — waiting for requester to confirm direction |
| `human_working` | No answer found, waiting on a resolver |
| `pending_confirm` | Answer suggested, waiting on requester |
| `verified` | Confirmed correct — reusable (confidence 0.90+) |
| `unconfirmed` | Saved but not yet confirmed (confidence 0.30–0.55) |
| `escalate` | Answer was wrong, old answer archived to version_history |

---

## Running Locally

```bash
cd mira-app
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e ../vault-service
cp .env.example .env
# Required: SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ANTHROPIC_API_KEY
# Vault:    SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
# Search:   SLACK_USER_TOKEN (xoxp-...)
# GitHub:   GITHUB_TOKEN, GITHUB_ANALYTICS_REPO=Jinqiudong/loopback-analytics
# Canvas:   CANVAS_ID_<CHANNEL_ID> (set in Railway Variables for each channel)
python app.py
```
