from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Tuple

from hw1.players.BaseBlackjackPlayerAgent import BaseBlackjackPlayer


class PlayerAgent_99328166(BaseBlackjackPlayer):
    """
    Expected-value based blackjack agent.

    Core idea
    - Uses the observed future cards deterministically when available.
    - After the observed cards are exhausted, models the next card as a random draw
      from the remaining unseen deck.
    - Recursively compares the expected utility of Stand vs Hit and returns the action
      with larger expected utility.

    Utility design
    - Bust => 0
    - Otherwise start with normalized final score (score / target)
    - Add a bonus for currently beating the opponent's visible best score
      so the policy prefers standing on strong winning positions.

    This is not a perfect game-theoretic solver because the opponent's future actions
    are unknown, but it is a principled expected-value strategy that uses the visible
    information and the remaining deck composition.
    """

    # Utility weights tuned to remain stable across changing targets.
    WIN_BONUS = 0.65
    TIE_BONUS = 0.18
    IMPROVE_MARGIN = 1e-9

    def __init__(self, strPlayerName: str):
        super().__init__(strPlayerName)

    # ------------------------- public decision entry ------------------------- #
    def decision(
        self,
        lstMyCurrentCards: List[dict],
        lstOtherPlayerCards: List[List[dict]],
        lstFutureCards: List[dict],
    ) -> bool:
        target = self.objGameEngine.intTargetScore
        opp_best = 0
        if lstOtherPlayerCards:
            opp_best = max(self.objGameEngine.calculate_hand_value(hand) for hand in lstOtherPlayerCards)

        total, soft_aces = self._hand_state_from_cards(lstMyCurrentCards, target)
        if total >= target:
            return False

        observed = tuple(card["rank"] for card in lstFutureCards)
        hidden_counts = self._remaining_rank_counts(lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards)
        counts_tuple = self._counts_to_tuple(hidden_counts)

        stand_value = self._ev_stand(total, target, opp_best)
        hit_value = self._ev_hit(total, soft_aces, observed, counts_tuple, target, opp_best)
        return hit_value > stand_value + self.IMPROVE_MARGIN

    # ------------------------------ EV solver ------------------------------ #
    @lru_cache(maxsize=None)
    def _best_ev(
        self,
        total: int,
        soft_aces: int,
        observed: Tuple[str, ...],
        counts_tuple: Tuple[int, ...],
        target: int,
        opp_best: int,
    ) -> float:
        if total > target:
            return 0.0

        stand_value = self._ev_stand(total, target, opp_best)
        hit_value = self._ev_hit(total, soft_aces, observed, counts_tuple, target, opp_best)
        return max(stand_value, hit_value)

    def _ev_hit(
        self,
        total: int,
        soft_aces: int,
        observed: Tuple[str, ...],
        counts_tuple: Tuple[int, ...],
        target: int,
        opp_best: int,
    ) -> float:
        if total > target:
            return 0.0

        # If observed future cards are available, the next draw is deterministic.
        if observed:
            next_rank = observed[0]
            next_total, next_soft_aces = self._add_rank(total, soft_aces, next_rank, target)
            return self._best_ev(next_total, next_soft_aces, observed[1:], counts_tuple, target, opp_best)

        # Otherwise use expected value over the unseen remaining deck.
        total_hidden = sum(counts_tuple)
        if total_hidden <= 0:
            return self._ev_stand(total, target, opp_best)

        expectation = 0.0
        counts = list(counts_tuple)
        for idx, cnt in enumerate(counts):
            if cnt <= 0:
                continue
            rank = self.RANK_ORDER[idx]
            prob = cnt / total_hidden
            counts[idx] -= 1
            next_total, next_soft_aces = self._add_rank(total, soft_aces, rank, target)
            expectation += prob * self._best_ev(
                next_total,
                next_soft_aces,
                tuple(),
                tuple(counts),
                target,
                opp_best,
            )
            counts[idx] += 1
        return expectation

    def _ev_stand(self, total: int, target: int, opp_best: int) -> float:
        if total > target:
            return 0.0
        utility = total / max(1, target)
        if total > opp_best:
            utility += self.WIN_BONUS
        elif total == opp_best:
            utility += self.TIE_BONUS
        return utility

    # ---------------------------- card utilities --------------------------- #
    RANK_ORDER = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
    RANK_TO_VALUE = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "J": 10,
        "Q": 10,
        "K": 10,
        "A": 11,
    }

    def _hand_state_from_cards(self, cards: Iterable[dict], target: int) -> Tuple[int, int]:
        total = 0
        soft_aces = 0
        for card in cards:
            total, soft_aces = self._add_rank(total, soft_aces, card["rank"], target)
        return total, soft_aces

    def _add_rank(self, total: int, soft_aces: int, rank: str, target: int) -> Tuple[int, int]:
        total += self.RANK_TO_VALUE[rank]
        if rank == "A":
            soft_aces += 1
        while total > target and soft_aces > 0:
            total -= 10
            soft_aces -= 1
        return total, soft_aces

    def _remaining_rank_counts(
        self,
        my_cards: List[dict],
        other_cards: List[List[dict]],
        future_cards: List[dict],
    ) -> Dict[str, int]:
        counts = {rank: 4 for rank in self.RANK_ORDER}

        for card in my_cards:
            counts[card["rank"]] -= 1
        for hand in other_cards:
            for card in hand:
                counts[card["rank"]] -= 1
        for card in future_cards:
            counts[card["rank"]] -= 1

        # Defensive guard against any unexpected negative counts.
        for rank in counts:
            if counts[rank] < 0:
                counts[rank] = 0
        return counts

    def _counts_to_tuple(self, counts: Dict[str, int]) -> Tuple[int, ...]:
        return tuple(counts[rank] for rank in self.RANK_ORDER)
