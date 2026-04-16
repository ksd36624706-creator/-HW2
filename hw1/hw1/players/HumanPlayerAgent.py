from hw1.players.BaseBlackjackPlayerAgent import BaseBlackjackPlayer

class HumanPlayerAgent(BaseBlackjackPlayer):
    def __init__(self, strPlayerName):
        super().__init__(strPlayerName)

    def decision(self, lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards):
        """
        Receives input from the user via the console to decide whether to Hit or Stand.
        """
        print(f"\n" + "=" * 40)
        print(f"[{self.strPlayerName}'s DECISION TURN]")

        # 1. Display My Hand
        my_score = self.objGameEngine.calculate_hand_value(lstMyCurrentCards)

        my_hand = [f"{c['rank']} of {c['suit']}" for c in lstMyCurrentCards]
        print(f"Your Cards: {', '.join(my_hand)} | Current Score: {my_score}")

        # 2. Display Other Players' Hands
        for idx, other_hand in enumerate(lstOtherPlayerCards):
            others = [f"{c['rank']} of {c['suit']}" for c in other_hand]
            other_score = self.objGameEngine.calculate_hand_value(lstOtherPlayerCards[idx])
            print(f"Player {idx + 1}'s Cards: {', '.join(others)} | Current Score: {other_score}")

        # 3. Display Future Cards (Cheating/Observation feature)
        if lstFutureCards:
            future = [f"{c['rank']} of {c['suit']}" for c in lstFutureCards]
            print(f"Next Cards in Deck: {', '.join(future)}")

        # 4. Input Loop
        while True:
            choice = input("\nChoose your action (1: Hit, 0: Stand): ").strip()
            if choice == '1':
                return True
            elif choice == '0':
                return False
            else:
                print("Invalid input. Please enter '1' for Hit or '0' for Stand.")