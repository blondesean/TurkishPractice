import random

from .base import Recommender
from mastery import compute_mastery


class WeightedRecommender(Recommender):
    """Selects words with probability proportional to (1 - mastery).

    Untested words have mastery 0 and so are selected most often. Fully-mastered
    words still get a small chance via MIN_WEIGHT so they reappear for review.
    """

    MIN_WEIGHT = 0.005  # 0.5% floor so 100%-mastered words still surface occasionally

    def select_questions(self, vocab, stats, module, direction, n):
        n = min(n, len(vocab))
        weights = []
        for eng, tur in vocab:
            key = f"{module}|{eng}|{tur}"
            w = stats.get("words", {}).get(key)
            history = w[direction].get("history", []) if w else []
            mastery = compute_mastery(history)
            weights.append(max(1.0 - mastery, self.MIN_WEIGHT))

        indices = list(range(len(vocab)))
        selected = []
        for _ in range(n):
            if not indices:
                break
            total = sum(weights[i] for i in indices)
            r = random.uniform(0, total)
            cumulative = 0.0
            for idx in indices:
                cumulative += weights[idx]
                if cumulative >= r:
                    selected.append(idx)
                    indices.remove(idx)
                    break
        return selected
