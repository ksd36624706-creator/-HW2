from hw1.players.BaseBlackjackPlayerAgent import BaseBlackjackPlayer


class PlayerAgent_12345678(BaseBlackjackPlayer):
    def __init__(self, strPlayerName):
        super().__init__(strPlayerName)

    def _score_cards(self, cards):
        return self.objGameEngine.calculate_hand_value(cards)

    def _score_after_sequence(self, my_cards, future_cards, num_hits):
        test_hand = list(my_cards)
        for idx in range(num_hits):
            test_hand.append(future_cards[idx])
        return self._score_cards(test_hand)

    def _best_observed_plan(self, my_cards, future_cards, target):
        """Return (best_score, hits_needed) using only the currently observed future cards.
        hits_needed can be 0..len(future_cards). Scores over target are ignored.
        """
        best_score = self._score_cards(my_cards)
        best_hits = 0

        for hits in range(1, len(future_cards) + 1):
            score = self._score_after_sequence(my_cards, future_cards, hits)
            if score > target:
                break
            # Prefer higher score; on ties prefer fewer hits.
            if score > best_score:
                best_score = score
                best_hits = hits
        return best_score, best_hits

    def decision(self, lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards):
        target = self.objGameEngine.intTargetScore
        my_score = self._score_cards(lstMyCurrentCards)
        other_scores = [self._score_cards(hand) for hand in lstOtherPlayerCards] or [0]
        best_other = max(other_scores)

        # Already at target or no need to risk a bust.
        if my_score >= target:
            return False

        # If no visible future card exists, use a conservative threshold that adapts to the target.
        if not lstFutureCards:
            if my_score <= max(11, target - 10):
                return True
            if my_score < best_other and my_score <= target - 4:
                return True
            return False

        next_score = self._score_after_sequence(lstMyCurrentCards, lstFutureCards, 1)
        # Never take a visible bust.
        if next_score > target:
            return False

        best_plan_score, best_plan_hits = self._best_observed_plan(lstMyCurrentCards, lstFutureCards, target)

        # Exact target is always worth taking if visible.
        if next_score == target:
            return True

        # If standing already beats or ties the opponent comfortably, protect the lead.
        lead_margin = my_score - best_other
        if lead_margin >= 2 and my_score >= target - 4:
            return False

        # If opponent is ahead or tied above us, be more aggressive when a better observed plan exists.
        if my_score <= best_other:
            if best_plan_hits >= 1 and best_plan_score > my_score:
                return True
            return my_score <= target - 7

        # When ahead but not safe, only hit if the observed plan clearly improves the final score.
        improvement = best_plan_score - my_score
        if best_plan_hits >= 1 and improvement >= 3:
            return True

        # Low scores are too weak to stand on.
        if my_score <= max(10, target // 2):
            return True

        # Close to the target: only hit if the immediate step gives a material improvement.
        if next_score >= target - 2 and next_score > my_score:
            return True

        return False
