"""
Agentic Tier 2 investigation via Claude tool use.

Claude receives the question and a set of tools, then autonomously decides
what to search and which files to read — running multiple tool calls until
it has enough context to summarise its findings.

This is the MCP pattern: the AI drives the investigation, not scripted Python.
Claude decides the strategy; we execute whatever it asks for.

Tools available to Claude:
  search_github(query)        — searches loopback-analytics codebase (SQL, schema, docs)
  read_file(path)             — reads a specific file from the analytics repo
  search_slack_history(query) — searches Slack workspace history (RTS API)

All persistent knowledge lives in the Knowledge Vault, not in static files.
Mira finds clues from code/schema; humans confirm and explain; Vault learns from that.
"""

import logging
from typing import Any

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from services.mcp_github import search_codebase, read_file, _ANALYTICS_REPO
from services.slack_search import search_slack_history as _search_slack

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_MAX_ITERATIONS = 5

_TOOLS = [
    {
        "name": "search_github",
        "description": (
            "Search the analytics codebase (SQL schema, metric definitions, documentation) "
            "for information relevant to the question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant code or documentation"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the full content of a specific file from the analytics repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to repo root, e.g. 'schema/raw_applications.sql'"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_slack_history",
        "description": "Search Slack workspace message history for conversations relevant to the question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for Slack messages"
                }
            },
            "required": ["query"]
        }
    },
]

_SYSTEM = """You are Mira, an AI analyst embedded in a Slack workspace.
A team member has asked a question. Your job is to investigate using the available tools
and surface the most relevant information to help answer it.

Strategy — follow this order exactly:
1. Read these files directly (do NOT search first):
   - read_file("schema/raw_applications.sql")
   - read_file("schema/da_approval_metrics.sql")
2. If those give you enough context, stop and summarise.
3. Only use search_github if the direct reads fail or return nothing.

When you have enough information, stop and write a summary using this exact format:

*Possible cause:*
1. [one sentence max — specific finding, field or table name] <github_url|filename>
2. [second finding if relevant] <github_url|filename>

Rules:
- Maximum 2 points, one sentence each. Direct and specific — no background explanations.
- Link format MUST be: <url|filename> with angle brackets, e.g. <https://github.com/org/repo/blob/main/schema/raw_applications.sql|raw_applications.sql>
  Do NOT use parentheses, do NOT URL-encode the pipe character. Use angle brackets only.
- Keep each point under 20 words before the link.
- Use *bold* with single asterisks. Numbered list with 1. 2.
- Start immediately with *Possible cause:* — no preamble.
- If nothing found: write ONLY this exact line and nothing else: "I didn't find anything relevant in the codebase."
  Do NOT add suggestions, next steps, bullet points, or any other content. Stop immediately after that line. """


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute one tool call and return the result as a string."""
    try:
        if tool_name == "search_github":
            results = search_codebase(tool_input["query"])
            if not results:
                return "No matching files found in the codebase."
            return "\n\n".join(
                f"{r['filename']} (github: {r['html_url']}):\n{r['excerpt']}"
                for r in results
            )

        elif tool_name == "read_file":
            path = tool_input["path"]
            content = read_file(path)
            if not content:
                return f"File not found: {path}"
            github_url = f"https://github.com/{_ANALYTICS_REPO}/blob/main/{path}" if _ANALYTICS_REPO else path
            return f"github: {github_url}\n\n{content[:2500]}"

        elif tool_name == "search_slack_history":
            results = _search_slack(tool_input["query"])
            if not results:
                return "No relevant messages found in Slack history."
            return "\n\n".join(
                f"@{r.get('username', 'unknown')} in #{r.get('channel_name', '?')}:\n{r['text'][:300]}"
                for r in results[:3]
            )

        else:
            return f"Unknown tool: {tool_name}"

    except Exception as e:
        logger.warning(f"Tool {tool_name} failed: {e}", exc_info=True)
        return f"Tool execution failed: {str(e)}"


def investigate(question: str) -> str:
    """
    Run an agentic investigation loop.

    Claude calls tools autonomously until it has enough context, then
    returns a concise bullet-point summary of its findings.
    Returns empty string if nothing useful was found.
    """
    if not question:
        return ""

    messages = [{"role": "user", "content": question}]

    for iteration in range(_MAX_ITERATIONS):
        try:
            response = _client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1500,
                system=_SYSTEM,
                tools=_TOOLS,
                messages=messages,
            )
        except Exception:
            logger.exception("Claude tool use call failed in investigator")
            return ""

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text") and block.text.strip():
                    # Slack renders *text* as bold, not **text** — normalise here
                    return block.text.strip().replace("**", "*")
            return ""

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"Mira calling tool: {block.name}({list(block.input.keys())})")
                    result = _execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    logger.warning("Investigator hit max iterations without a final answer")
    return ""
