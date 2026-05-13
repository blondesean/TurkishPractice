"""Per-word mastery computation, shared by the recommender and graphs."""

# Weight for each of the last WINDOW answers, most-recent first.
# Sum = 1.0 so the result is a fraction in [0, 1].
MASTERY_WEIGHTS = [0.30, 0.25, 0.20, 0.10, 0.05, 0.02, 0.02, 0.02, 0.02, 0.02]
WINDOW = len(MASTERY_WEIGHTS)


def compute_mastery(history):
    """Weighted accuracy over the last WINDOW answers.

    `history` is a list of booleans where the last element is the most recent
    answer. Missing slots (history shorter than WINDOW) count as 0, so an
    untested word has mastery 0 and a partially-tested word can never reach 100%.
    """
    if not history:
        return 0.0
    recent = history[-WINDOW:]
    score = 0.0
    for i, correct in enumerate(reversed(recent)):
        if correct:
            score += MASTERY_WEIGHTS[i]
    return score
