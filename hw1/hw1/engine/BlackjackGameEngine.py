import time
import random
from hw1.players.BaseBlackjackPlayerAgent import BaseBlackjackPlayer


class BlackjackGame:

    def __init__(self, game_id, lstPlayers, intFutureCardObs=3, intInitialCardDealNum=1, intTargetScore=21, floatTimeLimit=0.5):
        self.lstPlayers = lstPlayers
        self.game_id = game_id  # 생성 시 고유 ID 저장

        for player in self.lstPlayers:
            player.setGameEngine(self)

        self.intFutureCardObs = intFutureCardObs
        self.intInitialCardDealNum = intInitialCardDealNum
        self.intTargetScore = intTargetScore
        # 의사결정 시간 제한 (기본 0.5초)
        self.floatTimeLimit = floatTimeLimit

        self.lstCardDeck = []
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['Spades', 'Hearts', 'Diamonds', 'Clubs']

        for suit in suits:
            for rank in ranks:
                if rank in ['J', 'Q', 'K']:
                    value = 10
                elif rank == 'A':
                    value = 11
                else:
                    value = int(rank)
                self.lstCardDeck.append({'rank': rank, 'suit': suit, 'value': value})

    def shuffleDeck(self):
        random.shuffle(self.lstCardDeck)

    def calculate_hand_value(self, lstCards):
        hand_value = sum(card['value'] for card in lstCards)
        num_aces = sum(1 for card in lstCards if card['rank'] == 'A')
        while hand_value > self.intTargetScore and num_aces > 0:
            hand_value -= 10
            num_aces -= 1
        return hand_value

    def startGame(self):
        self.shuffleDeck()

        lstPlayerCard = [[] for _ in range(len(self.lstPlayers))]
        lstPlayerStatus = [True for _ in range(len(self.lstPlayers))]
        lstPlayerTime = [0 for _ in range(len(self.lstPlayers))]
        # 실격 여부를 추적하기 위한 리스트
        lstPlayerDisqualified = [False for _ in range(len(self.lstPlayers))]

        lstLog = []

        for _ in range(self.intInitialCardDealNum):
            for i in range(len(self.lstPlayers)):
                lstPlayerCard[i].append(self.lstCardDeck.pop())

        while True:
            for i in range(len(self.lstPlayers)):
                if not lstPlayerStatus[i]: continue
                # 1. 현재 결정을 내려야 하는 플레이어(i)의 카드 목록
                lstMyCurrentCards = lstPlayerCard[i]

                # 2. 다른 모든 플레이어들의 카드 목록을 리스트로 수합
                lstOtherPlayerCards = [lstPlayerCard[j] for j in range(len(self.lstPlayers)) if i != j]

                # 3. 덱의 맨 위에서부터 관찰 가능한 미래 카드들을 복사 (실제 덱에서 제거하지 않음)
                # self.intFutureCardObs 만큼의 카드를 뒤에서부터 역순으로 가져옴
                lstFutureCards = []
                for j in range(1, self.intFutureCardObs + 1):
                    if len(self.lstCardDeck) >= j:
                        # 리스트의 마지막 요소가 덱의 맨 위이므로 뒤에서부터 접근
                        lstFutureCards.append(self.lstCardDeck[-j])

                start_time = time.time()
                try:
                    is_hit = self.lstPlayers[i].decision(lstMyCurrentCards, lstOtherPlayerCards, lstFutureCards)
                except Exception as e:
                    is_hit = f"Error: {str(e)}"

                end_time = time.time()
                decision_time = end_time - start_time
                lstPlayerTime[i] += decision_time

                # 1. 시간 제한 검토 부분
                if decision_time > self.floatTimeLimit:
                    lstPlayerStatus[i] = False
                    lstPlayerDisqualified[i] = True
                    lstLog.append({
                        "game_id": self.game_id,  # ID 각인
                        "player_name": self.lstPlayers[i].strPlayerName,
                        "error": f"Timeout: {decision_time:.4f}s > {self.floatTimeLimit}s",
                        "time": decision_time  # 측정된 시간을 로그에 추가합니다.
                    })
                    continue

                # 2. 반환 값 형식 검토 부분
                if not isinstance(is_hit, bool):
                    lstPlayerStatus[i] = False
                    lstPlayerDisqualified[i] = True
                    lstLog.append({
                        "game_id": self.game_id,  # ID 각인
                        "player_name": self.lstPlayers[i].strPlayerName,
                        "error": f"Invalid return type: {type(is_hit)}",
                        "time": decision_time  # 측정된 시간을 로그에 추가합니다.
                    })
                    continue

                # 정상 로그 기록
                lstLog.append({
                    "game_id": self.game_id,  # ID 각인
                    "player_name": self.lstPlayers[i].strPlayerName,
                    "decision": "Hit" if is_hit else "Stand",
                    "time": decision_time,
                    "hand_value_before_decision": self.calculate_hand_value(lstMyCurrentCards),
                    "hand_card": lstMyCurrentCards.copy(),
                    "others_card": [other_hand.copy() for other_hand in lstOtherPlayerCards],
                    "future_card": lstFutureCards.copy()
                })

                if is_hit:
                    new_card = self.lstCardDeck.pop()
                    lstPlayerCard[i].append(new_card)
                    if self.calculate_hand_value(lstPlayerCard[i]) > self.intTargetScore:
                        lstPlayerStatus[i] = False
                else:
                    lstPlayerStatus[i] = False

            if not any(lstPlayerStatus):
                break

        # 최종 스코어 계산
        lstFinalScores = []
        for i in range(len(self.lstPlayers)):
            score = self.calculate_hand_value(lstPlayerCard[i])
            if score > self.intTargetScore or lstPlayerDisqualified[i]:
                lstFinalScores.append(0)
            else:
                lstFinalScores.append(score)
            # 모든 플레이어 인스턴스에 현재 게임의 전체 로그(lstLog) 저장
            self.lstPlayers[i].setGameLog(lstLog)

        max_score = max(lstFinalScores)
        if max_score == 0:
            return None, lstFinalScores, lstPlayerTime

        winner_idx = lstFinalScores.index(max_score)
        return self.lstPlayers[winner_idx].strPlayerName, lstFinalScores, lstPlayerTime