from hw1.players.BaseBlackjackPlayerAgent import BaseBlackjackPlayer

class PlayerAgent_99328162(BaseBlackjackPlayer):
    def __init__(self, strPlayerName):
        super().__init__(strPlayerName)

    def decision(self, lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards):
        target = self.objGameEngine.intTargetScore
        current_score = self.objGameEngine.calculate_hand_value(lstMyCurrentCards)

        # Immediate exit for safety
        if current_score >= target:
            return False

        max_lookahead_depth = 2

        return self._pure_recursive_thinker(current_score, 0, lstFutureCards, target, max_lookahead_depth)

    def _pure_recursive_thinker(self, score, future_idx, future_cards, target, depth):
        if future_idx >= len(future_cards) or depth <= 0:
            return False  # Default to 'Stand' when uncertain

        if score >= target - 3:
            return False

        # --- Recursive Step: Simulate Hitting ---
        next_card = future_cards[future_idx]
        card_val = next_card['value']

        new_score = score + card_val
        if next_card['rank'] == 'A' and new_score > target:
            new_score -= 10

        # If this single hit busts, the decision is definitely False (Stand)
        if new_score > target:
            return False

        self._pure_recursive_thinker(new_score, future_idx + 1, future_cards, target, depth - 1)
        return True