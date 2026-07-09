"""
Intent classification: decides whether a message Mira was @-mentioned in
is an actual question that should start the resolution cycle, or just
noise (a thank-you, a greeting, banter) that Mira should ignore.

This is intentionally a simple binary classification for Week 1.
Finer-grained intent (policy question vs. technical issue vs. ambiguous)
comes later, once the resolution cycle itself is wired up.
"""

from dataclasses import dataclass

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM_PROMPT = """You classify a single Slack message directed at an AI assistant named Mira.

Classify as exactly one of:
INSIGHTS    — user wants to see channel analytics or the Knowledge Vault dashboard
ANALYZE     — user wants Mira to analyze patterns and generate improvement proposals
QUESTION    — a genuine question or problem that needs an answer
NOISE       — greeting, thanks, small talk, or anything that doesn't need a response

Respond with exactly one word: INSIGHTS, ANALYZE, QUESTION, or NOISE. Nothing else."""


@dataclass
class IntentResult:
    is_question: bool
    raw_label: str  # QUESTION | NOISE | INSIGHTS | ANALYZE


def classify_intent(message_text: str) -> IntentResult:
    """
    Classify a message into one of four intents.
    Fails closed to NOISE if the API call fails.
    """
    try:
        response = _client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=10,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message_text}],
        )
        label = response.content[0].text.strip().upper()
    except Exception:
        label = "NOISE"

    is_question = label == "QUESTION"
    return IntentResult(is_question=is_question, raw_label=label)


_RESOLUTION_SYSTEM_PROMPT = """You are reading a Slack message sent by someone \
who previously asked a question in a thread. Decide whether this message signals \
that their question has been answered and they are satisfied — regardless of exact \
wording, language, or tone.

Examples of RESOLVED: "thanks", "got it", "ok cool", "makes sense", "alright", \
"好的谢谢", "明白了", "👍 got it", "that works", "perfect".
Examples of ONGOING: "still not sure", "what do you mean", "can you clarify", \
"that didn't work", "but what about".

Respond with exactly one word: RESOLVED or ONGOING. Nothing else."""


def classify_resolution(message_text: str) -> bool:
    """Return True if the asker's message signals the question was resolved."""
    try:
        response = _client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=10,
            system=_RESOLUTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message_text}],
        )
        label = response.content[0].text.strip().upper()
    except Exception:
        label = "ONGOING"

    return label.startswith("RESOLVED")


_DIRECTION_RESPONSE_PROMPT = """Mira (an AI) posted investigation findings in a Slack thread \
and asked the original asker: "Does this look right?" The asker has now replied.

Classify the reply as exactly one of:
ESCALATE — asker wants a human to investigate or confirm \
(e.g. "yes", "correct", "please loop someone in", "yes escalate", "yes get the DE")
RESOLVED — asker's question is already answered by Mira's findings, no human needed \
(e.g. "makes sense thanks", "got it!", "that explains it", "that answers it")
UNCLEAR  — not enough signal (e.g. "maybe", "hmm", a new question)

Respond with exactly one word: ESCALATE, RESOLVED, or UNCLEAR. Nothing else."""


def classify_is_deflection(answer_text: str) -> bool:
    """Return True if an answer deflects rather than resolves (e.g. 'create a ticket')."""
    try:
        response = _client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=10,
            system=(
                "You are reading a Slack message that was given as an answer to a question. "
                "Decide whether this answer DEFLECTS the question (redirects to a ticket, "
                "Jira issue, or another process without actually answering it) or ANSWERS it "
                "(provides real information or resolution). "
                "Respond with exactly one word: DEFLECTION or ANSWER. Nothing else."
            ),
            messages=[{"role": "user", "content": answer_text}],
        )
        label = response.content[0].text.strip().upper()
    except Exception:
        label = "ANSWER"
    return label.startswith("DEFLECTION")


def classify_direction_response(message_text: str) -> str:
    """
    Classify asker's reply to a direction check.
    Returns: 'ESCALATE' | 'RESOLVED' | 'UNCLEAR'
    """
    try:
        response = _client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=10,
            system=_DIRECTION_RESPONSE_PROMPT,
            messages=[{"role": "user", "content": message_text}],
        )
        label = response.content[0].text.strip().upper()
    except Exception:
        label = "UNCLEAR"

    if "ESCALATE" in label:
        return "ESCALATE"
    if "RESOLVED" in label:
        return "RESOLVED"
    return "UNCLEAR"
