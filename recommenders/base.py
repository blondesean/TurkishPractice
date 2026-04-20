from abc import ABC, abstractmethod


class Recommender(ABC):
    """Base class for word recommendation algorithms.

    To create a new recommender, subclass this and implement select_questions().
    Then update recommenders/__init__.py to point ActiveRecommender at your class.
    """

    @abstractmethod
    def select_questions(self, vocab, stats, module, direction, n):
        """Select n word indices from vocab to quiz the user on.

        Args:
            vocab: list of (english, turkish) tuples
            stats: the full stats dict (see stats.json)
            module: current module name (e.g. "animals")
            direction: "en_to_tr" or "tr_to_en"
            n: number of questions to select

        Returns:
            list of indices into vocab
        """
        pass
