"""
Adds/updates a status reaction on the original question message in a thread.

Called whenever a task card changes status so the channel gets a visual
indicator without anyone needing to open the thread.
"""

import logging

logger = logging.getLogger(__name__)

_STATUS_EMOJI: dict[str, str] = {
    "human_working": "question",
    "escalate":      "question",
    "pending_confirm": "bell",
    "unconfirmed":   "bell",
    "verified":      "white_check_mark",
}

_ALL_STATUS_EMOJIS = set(_STATUS_EMOJI.values())


def update_status_reaction(client, channel: str, thread_ts: str, status: str) -> None:
    """Remove any existing status reactions and add the one for the new status."""
    if not thread_ts:
        return

    emoji = _STATUS_EMOJI.get(status)

    # Remove stale status reactions (ignore errors — reaction may not exist)
    for old_emoji in _ALL_STATUS_EMOJIS:
        if old_emoji == emoji:
            continue
        try:
            client.reactions_remove(channel=channel, name=old_emoji, timestamp=thread_ts)
        except Exception:
            pass

    if emoji:
        try:
            client.reactions_add(channel=channel, name=emoji, timestamp=thread_ts)
        except Exception as e:
            if "already_reacted" not in str(e):
                logger.warning("Could not add reaction :%s: to %s", emoji, thread_ts, exc_info=True)
