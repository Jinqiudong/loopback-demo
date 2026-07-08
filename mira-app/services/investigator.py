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

from config import ANTHROPIC_API_KEY
from services.mcp_github import search_codebase, _read_file
from services.slack_search import search_slack_history as _search_slack

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_MODEL = "claude-sonnet-4-6"
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

Strategy:
1. Search GitHub with simple, broad terms (e.g. "product_type", "approval_rate", "raw_applications")
2. If you find a promising file, read it fully with read_file
3. Try reading key files directly if search doesn't return results: "schema/raw_applications.sql", "schema/da_approval_metrics.sql", "metrics/approval_rate.sql", "data_dictionary.md"
4. Search Slack history as a last resort

When you have enough information, stop and write a summary using this exact format:

*Possible cause:*
1. [one sentence — what specifically might be wrong, cite the field/table name] _(source: filename)_
2. [second finding if relevant] _(source: filename)_

Rules:
- Maximum 2 points. Direct answer to the question — not general explanations of how the system works.
- Cite the exact file name in parentheses after each point, e.g. _(raw_applications.sql)_
- Use Slack formatting: *bold* with single asterisks, numbered list with 1. 2.
- No preamble like "Here's what I found" or "Got it!" — start immediately with *Possible cause:*
- If nothing found: write "I didn't find anything relevant in the codebase." """


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute one tool call and return the result as a string."""
    try:
        if tool_name == "search_github":
            results = search_codebase(tool_input["query"])
            if not results:
                return "No matching files found in the codebase."
            return "\n\n".join(
                f"**{r['filename']}** ({r['path']}):\n{r['excerpt']}"
                for r in results
            )

        elif tool_name == "read_file":
            content = _read_file(tool_input["path"])
            if not content:
                return f"File not found: {tool_input['path']}"
            return content[:2500]

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
                model=_MODEL,
                max_tokens=300,
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
                    return block.text.strip()
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
