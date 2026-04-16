import random
from hw2.players.BingoPlayerAgent import BaseBingoPlayer


class RandomPlayer(BaseBingoPlayer):
    def __init__(self, strPlayerName):
        super().__init__(strPlayerName)

    def decision(self, matGrid):
        """
        Connect 4 규칙(중력)에 맞는 유효한 좌표 (y, x)를 찾아 무작위로 반환합니다.
        """
        # matGrid의 크기 확인 (height, width)
        height, width = matGrid.shape
        feasible_moves = []

        # 1. 각 열(x)을 순회하며 돌을 놓을 수 있는 가장 낮은 행(y)을 탐색
        for x in range(width):
            # 바닥(height-1)부터 위로 올라가며 빈 칸(0) 확인
            for y in range(height - 1, -1, -1):
                if matGrid[y][x] == 0:
                    # 해당 칸이 비어있으면 그 아래는 이미 차 있거나 바닥이므로 유효함
                    feasible_moves.append((y, x))
                    break  # 해당 열에서는 가장 아래 빈 칸만 유효하므로 중단

        # 2. 유효한 수가 있다면 무작위로 하나 선택하여 (y, x) 튜플 반환
        if feasible_moves:
            return random.choice(feasible_moves)

        # 3. 만약 판이 꽉 찼다면 (이론상 엔진에서 먼저 걸러짐) 예외 반환
        return (None, None)

