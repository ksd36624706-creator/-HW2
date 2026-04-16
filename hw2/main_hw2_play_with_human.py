from hw2.engine.BingoGameEngine import BingoGameEngine
from hw2.players.HumanPlayerAgent import HumanPlayer
from hw2.players.SamplePlayerAgent import RandomPlayer
from hw2.hw_99328161.PlayerAgent_99328161 import PlayerAgent_99328161

if __name__ == "__main__":
    human = HumanPlayer(strPlayerName="User")
    ai_bot = PlayerAgent_99328161(strPlayerName="AlgorithmicBot")

    players = [human, ai_bot]
    game = BingoGameEngine("Local Test with Human",
                         players, 11, 9, 4,
                         floatTimeLimit=500000)

    print("Starting Bingo Game: Human vs AI")

    # 1. 게임 실행
    winner_name, final_scores, player_times = game.startGame()

    # 2. 결과 콘솔 출력
    print("\n" + "#" * 40)
    print("GAME OVER")
    print("#" * 40)

    # 3. GUI를 유지하며 최종 보드 확인 및 메시지 박스 표시
    human.show_final_result(winner_name)
