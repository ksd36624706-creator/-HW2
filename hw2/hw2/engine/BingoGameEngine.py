import time
import random
import numpy as np
from gameengine.GameEngine import GameEngine

class BingoGameEngine(GameEngine):

    def __init__(self, game_id, lstPlayers, width, height, intConsecutive, floatTimeLimit=5.0,
                 lstTurn = None, lstMove = None):
        super().__init__(game_id, lstPlayers)

        self.width = width
        self.height = height
        self.intConsecutive = intConsecutive
        # 의사결정 시간 제한 (기본 0.5초)
        self.floatTimeLimit = floatTimeLimit
        self.matGrid = np.zeros((height, width), dtype=int)

        self.lstTurn = lstTurn if lstTurn is not None else []
        self.lstMove = lstMove if lstMove is not None else []
        self.intCurrentTurn = 1

    def getState(self,x,y):
        return self.matGrid[y][x]

    def setState(self, x, y):
        if self.isFeasiblePosition(x, y) == False:
            return False

        self.matGrid[y][x] = self.intCurrentTurn
        self.lstTurn.append(self.intCurrentTurn)
        self.lstMove.append((x, y))
        return True

    def isFeasiblePosition(self,x,y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        if self.matGrid[y][x] != 0:
            return False
        if y == self.height - 1 or self.matGrid[y+1][x] != 0:
            return True
        return False

    def isState(self, x, y, intTurn):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return self.matGrid[y][x] == intTurn

    def checkWin(self):
        if self.checkEndState(1) == True:
            return 1
        if self.checkEndState(2) == True:
            return 2
        return 0

    def checkEndState(self, intTurn):
        if self.checkState(intTurn, self.intConsecutive) > 0:
            return True
        return False

    def checkState(self, intTurn, intConsecutive):
        intCnt = 0
        # 4방향만 정의: 우, 하, 우하향 대각선, 좌하향 대각선
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for y in range(self.height):
            for x in range(self.width):
                # 1. 조기 종료: 현재 위치가 해당 플레이어의 돌이 아니면 스킵
                if self.matGrid[y][x] != intTurn:
                    continue

                # 2. 4방향 탐색
                for dx, dy in directions:
                    blnCheck = True
                    for k in range(1, intConsecutive):  # 현재 위치는 이미 확인했으므로 1부터 시작
                        nx, ny = x + dx * k, y + dy * k
                        if not self.isState(nx, ny, intTurn):
                            blnCheck = False
                            break

                    if blnCheck:
                        intCnt += 1

        return intCnt

    def checkFeasiblePosition(self):
        blnFeasible = False
        for i in range(self.height):
            for j in range(self.width):
                if self.isFeasiblePosition(j,i) == True:
                    blnFeasible = True
                    return blnFeasible
        return blnFeasible

    def startGame(self):
        intTurn = 1
        strWinPlayer = None

        lstPlayerTime = [0 for _ in range(len(self.lstPlayers))]
        # 실격 여부를 추적하기 위한 리스트
        lstPlayerDisqualified = [False for _ in range(len(self.lstPlayers))]

        lstLog = []

        isFeasible = True
        while True:
            for i in range(len(self.lstPlayers)):
                self.intCurrentTurn = i + 1
                start_time = time.time()
                try:
                    y,x = self.lstPlayers[i].decision(self.matGrid)
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    strWinPlayer = self.lstPlayers[1-i].strPlayerName
                    lstPlayerDisqualified[i] = True
                    lstLog.append({
                        "game_id": self.game_id,  # ID 각인
                        "player_name": self.lstPlayers[i].strPlayerName,
                        "error": error_msg,
                        "time": 0
                    })
                    break

                end_time = time.time()
                decision_time = end_time - start_time
                lstPlayerTime[i] += decision_time

                # 1. 시간 제한 검토 부분
                if decision_time > self.floatTimeLimit:
                    lstPlayerDisqualified[i] = True
                    strWinPlayer = self.lstPlayers[1 - i].strPlayerName
                    lstLog.append({
                        "game_id": self.game_id,  # ID 각인
                        "player_name": self.lstPlayers[i].strPlayerName,
                        "error": f"Timeout: {decision_time:.4f}s > {self.floatTimeLimit}s",
                        "time": decision_time  # 측정된 시간을 로그에 추가합니다.
                    })
                    break

                if not isinstance(y, int) or not isinstance(x, int):
                    lstPlayerDisqualified[i] = True
                    strWinPlayer = self.lstPlayers[1 - i].strPlayerName
                    lstLog.append({
                        "game_id": self.game_id,  # ID 각인
                        "player_name": self.lstPlayers[i].strPlayerName,
                        "error": f"Invalid return type: {type(y),type(x)}",
                        "time": decision_time  # 측정된 시간을 로그에 추가합니다.
                    })
                    break

                blnFeasible = self.setState(x, y)

                if blnFeasible == False:
                    lstPlayerDisqualified[i] = True
                    strWinPlayer = self.lstPlayers[1 - i].strPlayerName
                    lstLog.append({
                        "game_id": self.game_id,  # ID 각인
                        "player_name": self.lstPlayers[i].strPlayerName,
                        "error": f"Invalid decision type: ({y},{x})",
                        "time": decision_time  # 측정된 시간을 로그에 추가합니다.
                    })
                    break

                # 정상 로그 기록
                lstLog.append({
                    "game_id": self.game_id,  # ID 각인
                    "player_name": self.lstPlayers[i].strPlayerName,
                    "time": decision_time,
                    "decision y,x": (y,x),
                    "grid": str(self.matGrid)
                })

                if self.checkEndState(i+1) == True:
                    strWinPlayer = self.lstPlayers[i].strPlayerName
                    break

                if self.checkFeasiblePosition() == False:
                    isFeasible = False
                    break

            if any(lstPlayerDisqualified):
                break
            if strWinPlayer is not None:
                break
            if isFeasible == False:
                break

        lstFinalScores = []
        for i in range(len(self.lstPlayers)):
            # 모든 플레이어 인스턴스에 현재 게임의 전체 로그(lstLog) 저장
            self.lstPlayers[i].setGameLog(lstLog)
            if strWinPlayer == self.lstPlayers[i].strPlayerName:
                lstFinalScores.append(1)
            else:
                lstFinalScores.append(0)


        return strWinPlayer, lstFinalScores, lstPlayerTime