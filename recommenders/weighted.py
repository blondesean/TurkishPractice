import random
from datetime import datetime

from .base import Recommender


class WeightedRecommender(Recommender):
    """Selects words weighted by error rate (primary) and time since last review (secondary).

    - Words the user gets wrong more often are selected more frequently.
    - Among correctly-answered words, those not reviewed recently get a boost.
    - Unseen words are given moderate priority so new vocabulary gets introduced.
    """

    ERROR_WEIGHT = 5.0      # how much incorrectness matters
    TIME_WEIGHT = 2.0       # how much staleness matters
    UNSEEN_WEIGHT = 3.0     # weight for never-seen words
    TIME_CAP_HOURS = 168.0  # 1 week — beyond this, time factor maxes out
    BASE_WEIGHT = 0.1       # minimum weight so every word has a chance

    def select_questions(self, vocab, stats, module, direction, n):
        n = min(n, len(vocab))
        weights = []

        now = datetime.now()

        for i, (eng, tur) in enumerate(vocab):
            key = f"{module}|{eng}|{tur}"
            word_stats = stats.get("words", {}).get(key)

            if not word_stats or word_stats[direction]["seen"] == 0:
                # Never seen in this direction — introduce it
                weights.append(self.UNSEEN_WEIGHT)
                continue

            d = word_stats[direction]
            accuracy = d["correct"] / d["seen"]
            error_rate = 1.0 - accuracy

            # Time since last review
            last_seen = word_stats.get("last_seen")
            if last_seen:
                hours_ago = (now - datetime.fromisoformat(last_seen)).total_seconds() / 3600
                time_factor = min(hours_ago / self.TIME_CAP_HOURS, 1.0)
            else:
                time_factor = 1.0

            weight = (
                self.BASE_WEIGHT
                + error_rate * self.ERROR_WEIGHT
                + time_factor * self.TIME_WEIGHT
            )
            weights.append(weight)

        # Weighted sampling without replacement
        indices = list(range(len(vocab)))
        selected = []
        for _ in range(n):
            if not indices:
                break
            total = sum(weights[i] for i in indices)
            r = random.uniform(0, total)
            cumulative = 0
            for idx in indices:
                cumulative += weights[idx]
                if cumulative >= r:
                    selected.append(idx)
                    indices.remove(idx)
                    break

        return selected
