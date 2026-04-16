from hw1.players.BaseBlackjackPlayerAgent import BaseBlackjackPlayer

class PlayerAgent_20250135(BaseBlackjackPlayer):
    def __init__(self, strPlayerName):
        super().__init__(strPlayerName)

        # Tuned heuristic parameters
        self.NF_FLOOR = 7          # no-future fallback minimum threshold
        self.NF_MARGIN = 7         # hit when score <= target - NF_MARGIN
        self.NF_CHASE_GAP = 5      # if behind, keep hitting until target - gap

        self.PROTECT_LEAD = 2      # protect lead if ahead by this many points
        self.PROTECT_GAP = 2       # and already close to target

        self.BEHIND_GAP = 4        # if behind and no clear plan, hit until target - gap
        self.AHEAD_IMPROVE = 1     # base improve threshold when ahead

        self.LOW_FLOOR = 8         # absolute low-score threshold
        self.LOW_DIV = 2           # relative low-score threshold: target // LOW_DIV
        self.CLOSE_GAP = 3         # near-target immediate-hit window

    def _score_cards(self, cards):
        return self.objGameEngine.calculate_hand_value(cards)

    def _score_after_sequence(self, my_cards, future_cards, num_hits):
        test_hand = list(my_cards)
        for idx in range(num_hits):
            test_hand.append(future_cards[idx])
        return self._score_cards(test_hand)

    def _best_observed_plan(self, my_cards, future_cards, target):
        best_score = self._score_cards(my_cards)
        best_hits = 0

        for hits in range(1, len(future_cards) + 1):
            score = self._score_after_sequence(my_cards, future_cards, hits)
            if score > target:
                break
            if score > best_score:
                best_score = score
                best_hits = hits
        return best_score, best_hits

    #made by AI
    def _first_surpass_plan(self, my_cards, future_cards, target, opponent_score):
        for hits in range(1, len(future_cards) + 1):
            score = self._score_after_sequence(my_cards, future_cards, hits)
            if score > target:
                break
            if score > opponent_score:
                return score, hits
        return self._score_cards(my_cards), 0

    #made by AI
    def _best_safe_score(self, my_cards, future_cards, target):
        best_score = self._score_cards(my_cards)
        for hits in range(1, len(future_cards) + 1):
            score = self._score_after_sequence(my_cards, future_cards, hits)
            if score > target:
                break
            best_score = max(best_score, score)
        return best_score

    def decision(self, lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards):
        target = self.objGameEngine.intTargetScore
        my_score = self._score_cards(lstMyCurrentCards)
        other_scores = [self._score_cards(hand) for hand in lstOtherPlayerCards] or [0]
        best_other = max(other_scores)

        if my_score >= target:
            return False

        # Fallback when no future cards are visible.
        if not lstFutureCards:
            if my_score < best_other and my_score <= target - self.NF_CHASE_GAP:
                return True
            if my_score <= max(self.NF_FLOOR, target - self.NF_MARGIN) and my_score <= best_other:
                return True
            return False

        next_score = self._score_after_sequence(lstMyCurrentCards, lstFutureCards, 1)

        # Never take a visible bust.
        if next_score > target:
            return False

        best_plan_score, best_plan_hits = self._best_observed_plan(
            lstMyCurrentCards, lstFutureCards, target
        )

        #made by AI
        surpass_score, surpass_hits = self._first_surpass_plan(
            lstMyCurrentCards, lstFutureCards, target, best_other
        )

        # Exact target is always worth taking.
        if next_score == target:
            return True

        lead_margin = my_score - best_other

        # If already in a strong leading position, protect it.
        if lead_margin >= self.PROTECT_LEAD and my_score >= target - self.PROTECT_GAP:
            return False

        # If tied or behind, prioritize plans that actually surpass the opponent.(made by AI)
        if my_score <= best_other:
            if surpass_hits >= 1:
                return True
            if best_plan_hits >= 1 and best_plan_score > my_score and my_score <= target - self.BEHIND_GAP:
                return True
            return False

        # When ahead, be selective: small improvements are usually not worth the risk.(made by AI)
        improvement = best_plan_score - my_score
        if (
            best_plan_hits >= 1
            and improvement >= max(2, self.AHEAD_IMPROVE)
            and best_plan_score >= best_other + 2
        ):
            return True

        # Low scores are too weak only when we are not already safely ahead.(made by AI)
        if my_score <= max(self.LOW_FLOOR, target // self.LOW_DIV) and my_score <= best_other:
            return True

        # Near the target, hit only if it also improves over the opponent.
        if next_score >= target - self.CLOSE_GAP and next_score > max(my_score, best_other):
            return True

        return False