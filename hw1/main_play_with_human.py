# main script to play with sample player agent and human player agent
from hw1.engine.BlackjackGameEngine import BlackjackGame
from hw1.players.SamplePlayerAgent import AlgorithmicPlayerAgent
from hw1.hw_99328161.PlayerAgent_99328161 import PlayerAgent_99328161
from hw1.players.HumanPlayerAgent import HumanPlayerAgent

if __name__ == "__main__":
    # 1. Initialize Players
    # Human player to interact via console
    human = HumanPlayerAgent(strPlayerName="User")
    # A simple AI player that always hits
    # you can change the player as you want if you have new players over the hw implementation - icmoon
    # ai_bot = StupidHitPlayer(strPlayerName="StupidBot")
    ai_bot = PlayerAgent_99328161(strPlayerName="AlgorithmicBot")

    # 2. Setup the Game Engine
    # intFutureCardObs=1 means the human can see the next 1 card in the deck (cheating/observation)
    players = [human, ai_bot]
    game = BlackjackGame("Local Test with Human",
                         lstPlayers=players, intFutureCardObs=3, intInitialCardDealNum=1, intTargetScore=31,
                         floatTimeLimit=500000)

    print("Starting Blackjack Game: Human vs AI")

    # 3. Run the Game
    winner_name, final_scores, player_times = game.startGame()

    # 4. Display Results
    print("\n" + "#" * 40)
    print("GAME OVER")
    print("#" * 40)

    for i, player in enumerate(players):
        status = "BUSTED" if final_scores[i] == 0 else f"Score: {final_scores[i]}"
        print(f"{player.strPlayerName}: {status} | Total Decision Time: {player_times[i]:.4f}s")

    if winner_name:
        print(f"\nWINNER: {winner_name}!")
    else:
        print("\nRESULT: No winner (Everyone busted).")

    for i in range(len(human.lstGameLogs)):
        print(i, human.lstGameLogs[i])
