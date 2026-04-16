import random
import numpy as np
from hw2.players.BingoPlayerAgent import BaseBingoPlayer


class PlayerAgent_99328161(BaseBingoPlayer):
    def __init__(self, strPlayerName, depth=5):  # 속도가 빨라졌으므로 기본 depth를 5로 상향
        super().__init__(strPlayerName)
        self.search_depth = depth

    def get_feasible_moves(self, grid):
        """중력 법칙을 고려하여 착수 가능한 (y, x) 리스트 반환"""
        height, width = grid.shape
        moves = []
        for x in range(width):
            for y in range(height - 1, -1, -1):
                if grid[y][x] == 0:
                    moves.append((y, x))
                    break
        return moves

    def _check_win_at(self, grid, r, c, turn, win_n):
        """특정 좌표 (r, c)에 돌을 두었을 때 승리 여부를 8방향으로 즉시 판정"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # 가로, 세로, 대각선2
        for dr, dc in directions:
            count = 1
            # 정방향 탐색
            for i in range(1, win_n):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < grid.shape[0] and 0 <= nc < grid.shape[1] and grid[nr][nc] == turn:
                    count += 1
                else:
                    break
            # 역방향 탐색
            for i in range(1, win_n):
                nr, nc = r - dr * i, c - dc * i
                if 0 <= nr < grid.shape[0] and 0 <= nc < grid.shape[1] and grid[nr][nc] == turn:
                    count += 1
                else:
                    break
            if count >= win_n: return True
        return False

    def evaluate(self, grid, my_turn, win_n):
        """보드 상태를 수치화 (승리 시 무한대, 패배 시 음의 무한대)"""
        opp_turn = 2 if my_turn == 1 else 1
        score = 0

        # 단순 승패 판정보다 가중치 중심의 빠른 평가
        # (실제 미니맥스 내부에서는 check_win_at으로 조기 종료됨)
        score += self._count_sequences(grid, my_turn, 3) * 100
        score += self._count_sequences(grid, my_turn, 2) * 10
        score -= self._count_sequences(grid, opp_turn, 3) * 50000  # 상대 3개는 매우 위험
        return score

    def _count_sequences(self, grid, turn, length):
        """격자 내 특정 길이의 연속된 돌 개수를 카운트 (평가용)"""
        cnt = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        h, w = grid.shape
        for r in range(h):
            for c in range(w):
                if grid[r][c] == turn:
                    for dr, dc in directions:
                        match = True
                        for k in range(1, length):
                            nr, nc = r + dr * k, c + dc * k
                            if not (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == turn):
                                match = False;
                                break
                        if match: cnt += 1
        return cnt

    def minimax(self, grid, depth, alpha, beta, is_maximizing, my_turn, win_n):
        opp_turn = 2 if my_turn == 1 else 1
        curr_turn = my_turn if is_maximizing else opp_turn

        # 기저 조건 처리 (최적화를 위해 간단히 구현)
        if depth == 0:
            return self.evaluate(grid, my_turn, win_n)

        moves = self.get_feasible_moves(grid)
        if not moves: return 0

        if is_maximizing:
            val = -float('inf')
            for y, x in moves:
                # 즉시 승리 확인 (가장 강력한 가지치기)
                if self._check_win_at(grid, y, x, curr_turn, win_n): return 1000000 + depth

                grid[y][x] = curr_turn  # 직접 수정
                res = self.minimax(grid, depth - 1, alpha, beta, False, my_turn, win_n)
                grid[y][x] = 0  # 원상 복구 (Backtracking)

                val = max(val, res)
                alpha = max(alpha, val)
                if beta <= alpha: break
            return val
        else:
            val = float('inf')
            for y, x in moves:
                if self._check_win_at(grid, y, x, curr_turn, win_n): return -1000000 - depth

                grid[y][x] = curr_turn
                res = self.minimax(grid, depth - 1, alpha, beta, True, my_turn, win_n)
                grid[y][x] = 0

                val = min(val, res)
                beta = min(beta, val)
                if beta <= alpha: break
            return val

    def decision(self, matGrid):
        if self.objGameEngine is None:
            return (None, None)

        win_n = self.objGameEngine.intConsecutive
        my_turn = self.objGameEngine.intCurrentTurn
        opp_turn = 2 if my_turn == 1 else 1

        working_grid = matGrid.copy()  # 원본 보존을 위해 한 번만 복사
        feasible_moves = self.get_feasible_moves(working_grid)

        # 1. 즉시 승리/방어 하드 룰 (최우선)
        for y, x in feasible_moves:
            if self._check_win_at(working_grid, y, x, my_turn, win_n):
                return (y, x)
        for y, x in feasible_moves:
            if self._check_win_at(working_grid, y, x, opp_turn, win_n):
                print(f"!!! [DEFENSE] Hard Blocked at ({y}, {x})")
                return (y, x)

        # 2. 미니맥스 탐색
        best_score = -float('inf')
        best_move = random.choice(feasible_moves) if feasible_moves else (None, None)

        for y, x in feasible_moves:
            working_grid[y][x] = my_turn
            score = self.minimax(working_grid, self.search_depth - 1, -float('inf'), float('inf'), False, my_turn,
                                 win_n)
            working_grid[y][x] = 0

            if score > best_score:
                best_score = score
                best_move = (y, x)

        return best_move