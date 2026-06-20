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

from config import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """You classify a single Slack message that mentioned an AI \
assistant named Mira. Decide whether it is a QUESTION that needs an answer, \
or NOISE (a greeting, thanks, small talk, or anything that isn't actually \
asking for help with a problem).

Respond with exactly one word: QUESTION or NOISE. Nothing else."""


@dataclass
class IntentResult:
    is_question: bool
    raw_label: str


def classify_intent(message_text: str) -> IntentResult:
    """
    Classify a single message as QUESTION or NOISE.

    Deliberately fails closed: if anything goes wrong calling the API,
    we treat the message as NOISE rather than risk creating a task card
    for garbage input. Once this is stable we may want to reconsider
    that default, but for Week 1 it's the safer failure mode.
    """
    try:
        response = _client.messages.create(
            model=_MODEL,
            max_tokens=10,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message_text}],
        )
        label = response.content[0].text.strip().upper()
    except Exception:
        label = "NOISE"

    is_question = label.startswith("QUESTION")
    return IntentResult(is_question=is_question, raw_label=label)
