from hw1.players.BaseBlackjackPlayerAgent import BaseBlackjackPlayer


class PlayerAgent_99328161(BaseBlackjackPlayer):
    def __init__(self, strPlayerName):
        super().__init__(strPlayerName)

        # Tuned heuristic parameters
        self.NF_FLOOR = 7
        self.NF_MARGIN = 7
        self.NF_CHASE_GAP = 5

        self.PROTECT_LEAD = 2
        self.PROTECT_GAP = 2

        self.BEHIND_GAP = 4
        self.AHEAD_IMPROVE = 2

        self.LOW_FLOOR = 8
        self.LOW_DIV = 2
        self.CLOSE_GAP = 3

        # Shared-future heuristic controls
        self.OPP_LOW_FLOOR = 8
        self.OPP_LOW_DIV = 2
        self.OPP_PROTECT_LEAD = 2
        self.OPP_PROTECT_GAP = 2
        self.MAX_SHARED_LOOKAHEAD = 12

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

    def _first_surpass_plan(self, my_cards, future_cards, target, opponent_score):
        for hits in range(1, len(future_cards) + 1):
            score = self._score_after_sequence(my_cards, future_cards, hits)
            if score > target:
                break
            if score > opponent_score:
                return score, hits
        return self._score_cards(my_cards), 0

    def _best_safe_score(self, my_cards, future_cards, target):
        best_score = self._score_cards(my_cards)
        for hits in range(1, len(future_cards) + 1):
            score = self._score_after_sequence(my_cards, future_cards, hits)
            if score > target:
                break
            best_score = max(best_score, score)
        return best_score

    # -----------------------------
    # Shared-future helper methods
    # -----------------------------

    def _should_hit_no_future(self, my_score, opp_score, target):
        if my_score >= target:
            return False
        if my_score < opp_score and my_score <= target - self.NF_CHASE_GAP:
            return True
        if my_score <= max(self.NF_FLOOR, target - self.NF_MARGIN) and my_score <= opp_score:
            return True
        return False

    def _opp_should_hit(self, opp_score, my_score, target):
        """
        Heuristic model of opponent behavior when consuming shared future cards.
        This is not EV; it is a simple aggressive-then-protect policy.
        """
        if opp_score >= target:
            return False

        lead_margin = opp_score - my_score

        if lead_margin >= self.OPP_PROTECT_LEAD and opp_score >= target - self.OPP_PROTECT_GAP:
            return False

        if opp_score <= my_score:
            if opp_score <= target - self.BEHIND_GAP:
                return True
            return False

        if opp_score <= max(self.OPP_LOW_FLOOR, target // self.OPP_LOW_DIV):
            return True

        return False

    def _simulate_shared_future_once(self, my_score, opp_score, future_cards, target, my_first_action_hit):
        """
        Simulate future cards as a shared queue.
        Turn order:
          - my decision first
          - opponent decision second
          - then alternate
        This uses simple heuristics for both sides.
        """
        my_stood = False
        opp_stood = False
        idx = 0
        my_turn = True

        if not my_first_action_hit:
            my_stood = True
        else:
            if idx >= len(future_cards):
                return my_score, opp_score
            my_score = self._score_cards([{"rank": "X", "suit": "X", "value": 0}])  # dummy init overwrite below
            # safer direct append-free scoring using existing helper on pseudo list is awkward,
            # so compute by appending one actual card to a temp abstract score via list-based score.
            # since we only have scores here, use temp list-free approximation through card values is not enough for Ace.
            # therefore this function should not be called before converting to hands.
            return None

        steps = 0
        max_steps = min(len(future_cards), self.MAX_SHARED_LOOKAHEAD)

        while steps < max_steps:
            if my_score >= target or opp_score >= target:
                break
            if my_stood and opp_stood:
                break
            if idx >= len(future_cards):
                break

            if my_turn:
                if my_stood:
                    my_turn = False
                    continue

                take_hit = self._should_hit_no_future(my_score, opp_score, target)
                if take_hit:
                    next_score = self._score_after_sequence_from_score(my_score, future_cards[idx], target)
                    if next_score is None or next_score > target:
                        my_stood = True
                    else:
                        my_score = next_score
                        idx += 1
                else:
                    my_stood = True

                my_turn = False
            else:
                if opp_stood:
                    my_turn = True
                    continue

                take_hit = self._opp_should_hit(opp_score, my_score, target)
                if take_hit:
                    next_score = self._score_after_sequence_from_score(opp_score, future_cards[idx], target)
                    if next_score is None or next_score > target:
                        opp_stood = True
                    else:
                        opp_score = next_score
                        idx += 1
                else:
                    opp_stood = True

                my_turn = True

            steps += 1

        return my_score, opp_score

    def _card_value_for_running_total(self, running_total, card, target):
        """
        Approximate one-card update from score only.
        Ace is handled greedily as 11 unless bust, then 1.
        This is a heuristic, not an exact hand reconstruction.
        """
        rank = card["rank"]
        if rank == "A":
            if running_total + 11 <= target:
                return 11
            return 1
        return card["value"]

    def _score_after_sequence_from_score(self, running_total, card, target):
        return running_total + self._card_value_for_running_total(running_total, card, target)

    def _shared_future_outcome(self, lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards, target, first_action_hit):
        """
        Higher-level shared-future simulation using actual hand scoring for the first phase.
        """
        my_hand = list(lstMyCurrentCards)
        opp_hand = list(lstOtherPlayerCards[0]) if lstOtherPlayerCards else []

        my_stood = not first_action_hit
        opp_stood = False
        idx = 0
        my_turn = False if first_action_hit else False  # after my decision, opponent moves next

        if first_action_hit:
            if idx >= len(lstFutureCards):
                return self._score_cards(my_hand), self._score_cards(opp_hand)
            my_hand.append(lstFutureCards[idx])
            idx += 1

        steps = 0
        max_steps = min(len(lstFutureCards), self.MAX_SHARED_LOOKAHEAD)

        while steps < max_steps:
            my_score = self._score_cards(my_hand)
            opp_score = self._score_cards(opp_hand)

            if my_score >= target or opp_score >= target:
                break
            if my_stood and opp_stood:
                break
            if idx >= len(lstFutureCards):
                break

            if my_turn:
                if my_stood:
                    my_turn = False
                    continue

                take_hit = self._should_hit_no_future(my_score, opp_score, target)
                if take_hit:
                    test_score = self._score_cards(my_hand + [lstFutureCards[idx]])
                    if test_score > target:
                        my_stood = True
                    else:
                        my_hand.append(lstFutureCards[idx])
                        idx += 1
                else:
                    my_stood = True

                my_turn = False
            else:
                if opp_stood:
                    my_turn = True
                    continue

                take_hit = self._opp_should_hit(opp_score, my_score, target)
                if take_hit:
                    test_score = self._score_cards(opp_hand + [lstFutureCards[idx]])
                    if test_score > target:
                        opp_stood = True
                    else:
                        opp_hand.append(lstFutureCards[idx])
                        idx += 1
                else:
                    opp_stood = True

                my_turn = True

            steps += 1

        return self._score_cards(my_hand), self._score_cards(opp_hand)

    def _shared_future_value(self, my_final, opp_final, target):
        if my_final > target and opp_final > target:
            return -0.5
        if my_final > target:
            return -1.0
        if opp_final > target:
            return 1.0
        if my_final > opp_final:
            return 1.0 + 0.03 * (my_final - opp_final)
        if my_final < opp_final:
            return -1.0 - 0.03 * (opp_final - my_final)
        return 0.0

    # -----------------------------
    # Main decision
    # -----------------------------

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

        surpass_score, surpass_hits = self._first_surpass_plan(
            lstMyCurrentCards, lstFutureCards, target, best_other
        )

        best_safe_score = self._best_safe_score(
            lstMyCurrentCards, lstFutureCards, target
        )

        # Exact target is always worth taking.
        if next_score == target:
            return True

        lead_margin = my_score - best_other

        # If already in a strong leading position, protect it.
        if lead_margin >= self.PROTECT_LEAD and my_score >= target - self.PROTECT_GAP:
            return False

        # Shared-future simulation values:
        # compare "I stand now" vs "I hit now", while future cards are consumed by both players.
        stand_my, stand_opp = self._shared_future_outcome(
            lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards, target, first_action_hit=False
        )
        hit_my, hit_opp = self._shared_future_outcome(
            lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards, target, first_action_hit=True
        )

        stand_value = self._shared_future_value(stand_my, stand_opp, target)
        hit_value = self._shared_future_value(hit_my, hit_opp, target)

        # If tied or behind, prioritize plans that actually surpass the opponent.
        if my_score <= best_other:
            if surpass_hits >= 1 and hit_value >= stand_value:
                return True
            if best_safe_score <= best_other and hit_value < stand_value:
                return False
            if my_score <= target - self.BEHIND_GAP and hit_value >= stand_value:
                return True
            return hit_value > stand_value

        # When ahead, be selective: small improvements are usually not worth the risk.
        improvement = best_plan_score - my_score
        if (
            best_plan_hits >= 1
            and improvement >= max(2, self.AHEAD_IMPROVE)
            and best_plan_score >= best_other + 2
            and hit_value >= stand_value
        ):
            return True

        # Low scores are too weak only when we are not already safely ahead.
        if my_score <= max(self.LOW_FLOOR, target // self.LOW_DIV) and my_score <= best_other:
            return True

        # Near the target, hit only if it also improves over the opponent.
        if next_score >= target - self.CLOSE_GAP and next_score > max(my_score, best_other):
            return True

        return hit_value > stand_value