"""
Confidence scoring constants and helpers — standalone reference.
The knowledge_vault package uses these values internally.
"""

INITIAL_SCORES = {
    "signal_1":           0.90,
    "signal_2_ambiguous": 0.55,
    "signal_2_silence":   0.30,
    "signal_3":           0.40,
}
USAGE_INCREMENT       = 0.05
AUTO_VERIFY_THRESHOLD = 0.85


def initial_score(signal: str, ambiguous: bool = False) -> float:
    if signal == "signal_1":
        return INITIAL_SCORES["signal_1"]
    if signal == "signal_2":
        return INITIAL_SCORES["signal_2_ambiguous" if ambiguous else "signal_2_silence"]
    if signal == "signal_3":
        return INITIAL_SCORES["signal_3"]
    return 0.0


def after_usage(current_score: float) -> float:
    return min(current_score + USAGE_INCREMENT, 1.0)


def should_auto_verify(score: float) -> bool:
    return score >= AUTO_VERIFY_THRESHOLD
