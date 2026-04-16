import time
from hw2.players.BingoPlayerAgent import BaseBingoPlayer


class SearchTimeout(Exception):
    pass


class PlayerAgent_20250135(BaseBingoPlayer):
    def __init__(self, strPlayerName, max_depth=10, max_search_seconds=1.5):
        super().__init__(strPlayerName)
        self.max_depth = max_depth
        self.max_search_seconds = max_search_seconds
        self._eval_params_key = None
        self._eval_params_cache = None

    def get_feasible_moves(self, grid):
        height, width = grid.shape
        moves = []
        for x in range(width):
            for y in range(height - 1, -1, -1):
                if grid[y][x] == 0:
                    moves.append((y, x))
                    break
        return moves

    def _is_win_from(self, grid, r, c, turn, win_n):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        height, width = grid.shape

        for dr, dc in directions:
            count = 1
            for step in range(1, win_n):
                nr, nc = r + dr * step, c + dc * step
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == turn:
                    count += 1
                else:
                    break
            for step in range(1, win_n):
                nr, nc = r - dr * step, c - dc * step
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == turn:
                    count += 1
                else:
                    break
            if count >= win_n:
                return True
        return False

    def _count_windows(self, height, width, win_n):
        horizontal = height * max(0, width - win_n + 1)
        vertical = width * max(0, height - win_n + 1)
        diagonal = 2 * max(0, height - win_n + 1) * max(0, width - win_n + 1)
        return horizontal + vertical + diagonal

    def _get_eval_params(self, height, width, win_n):
        key = (height, width, win_n)
        if self._eval_params_key == key and self._eval_params_cache is not None:
            return self._eval_params_cache

        attack_base = win_n + 1
        defense_base = attack_base + 1
        my_threat_bonus = attack_base ** max(1, win_n - 1)
        opp_threat_bonus = (defense_base ** max(1, win_n - 1)) * 2
        center_weight = max(1, attack_base // 2)

        total_windows = self._count_windows(height, width, win_n)
        max_nonterminal_window = max(
            attack_base ** max(1, win_n - 1) + my_threat_bonus,
            defense_base ** max(1, win_n - 1) + opp_threat_bonus,
        )
        nonterminal_bound = total_windows * max_nonterminal_window + (center_weight * height)

        terminal_score = nonterminal_bound + 1
        root_win_score = terminal_score + nonterminal_bound + 1
        move_order_win_bonus = center_weight * width + 100

        params = {
            "attack_base": attack_base,
            "defense_base": defense_base,
            "my_threat_bonus": my_threat_bonus,
            "opp_threat_bonus": opp_threat_bonus,
            "center_weight": center_weight,
            "terminal_score": terminal_score,
            "root_win_score": root_win_score,
            "move_order_win_bonus": move_order_win_bonus,
        }
        self._eval_params_key = key
        self._eval_params_cache = params
        return params

    def _score_window(self, window, my_turn, opp_turn, win_n, params):
        my_cnt = 0
        opp_cnt = 0
        empty_cnt = 0
        for value in window:
            if value == my_turn:
                my_cnt += 1
            elif value == opp_turn:
                opp_cnt += 1
            else:
                empty_cnt += 1

        if my_cnt > 0 and opp_cnt > 0:
            return 0
        if my_cnt == win_n:
            return params["terminal_score"]
        if opp_cnt == win_n:
            return -params["terminal_score"]

        score = 0
        if my_cnt > 0:
            score += params["attack_base"] ** my_cnt
            if my_cnt == win_n - 1 and empty_cnt == 1:
                score += params["my_threat_bonus"]
        if opp_cnt > 0:
            score -= params["defense_base"] ** opp_cnt
            if opp_cnt == win_n - 1 and empty_cnt == 1:
                score -= params["opp_threat_bonus"]
        return score

    def evaluate(self, grid, my_turn, win_n):
        opp_turn = 2 if my_turn == 1 else 1
        height, width = grid.shape
        params = self._get_eval_params(height, width, win_n)
        score = 0

        center_x = width // 2
        center_bonus = 0
        for y in range(height):
            if grid[y][center_x] == my_turn:
                center_bonus += 1
            elif grid[y][center_x] == opp_turn:
                center_bonus -= 1
        score += params["center_weight"] * center_bonus

        for r in range(height):
            for c in range(width - win_n + 1):
                window = [grid[r][c + i] for i in range(win_n)]
                score += self._score_window(window, my_turn, opp_turn, win_n, params)

        for r in range(height - win_n + 1):
            for c in range(width):
                window = [grid[r + i][c] for i in range(win_n)]
                score += self._score_window(window, my_turn, opp_turn, win_n, params)

        for r in range(height - win_n + 1):
            for c in range(width - win_n + 1):
                window = [grid[r + i][c + i] for i in range(win_n)]
                score += self._score_window(window, my_turn, opp_turn, win_n, params)

        for r in range(height - win_n + 1):
            for c in range(win_n - 1, width):
                window = [grid[r + i][c - i] for i in range(win_n)]
                score += self._score_window(window, my_turn, opp_turn, win_n, params)

        return score

    def _ordered_moves(self, grid, moves, turn, win_n, params):
        center = (grid.shape[1] - 1) / 2.0
        scored = []
        for y, x in moves:
            priority = -abs(x - center)
            grid[y][x] = turn
            if self._is_win_from(grid, y, x, turn, win_n):
                priority += params["move_order_win_bonus"]
            grid[y][x] = 0
            scored.append((priority, (y, x)))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [move for _, move in scored]

    def _ensure_time(self, deadline):
        if time.perf_counter() >= deadline:
            raise SearchTimeout

    def _terminal_score(self, grid, last_move, last_turn, my_turn, win_n, depth, params):
        if last_move is None:
            return None
        y, x = last_move
        if not self._is_win_from(grid, y, x, last_turn, win_n):
            return None
        if last_turn == my_turn:
            return params["terminal_score"] + depth
        return -params["terminal_score"] - depth

    def minimax(
        self,
        grid,
        depth,
        alpha,
        beta,
        turn_to_move,
        my_turn,
        win_n,
        deadline,
        last_move,
        last_turn,
        params,
    ):
        self._ensure_time(deadline)

        terminal = self._terminal_score(grid, last_move, last_turn, my_turn, win_n, depth, params)
        if terminal is not None:
            return terminal

        moves = self.get_feasible_moves(grid)
        if depth == 0 or not moves:
            return self.evaluate(grid, my_turn, win_n)

        moves = self._ordered_moves(grid, moves, turn_to_move, win_n, params)
        maximizing = (turn_to_move == my_turn)
        next_turn = 2 if turn_to_move == 1 else 1

        if maximizing:
            best = -float("inf")
            for y, x in moves:
                self._ensure_time(deadline)
                grid[y][x] = turn_to_move
                value = self.minimax(
                    grid,
                    depth - 1,
                    alpha,
                    beta,
                    next_turn,
                    my_turn,
                    win_n,
                    deadline,
                    (y, x),
                    turn_to_move,
                    params,
                )
                grid[y][x] = 0

                if value > best:
                    best = value
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best

        best = float("inf")
        for y, x in moves:
            self._ensure_time(deadline)
            grid[y][x] = turn_to_move
            value = self.minimax(
                grid,
                depth - 1,
                alpha,
                beta,
                next_turn,
                my_turn,
                win_n,
                deadline,
                (y, x),
                turn_to_move,
                params,
            )
            grid[y][x] = 0

            if value < best:
                best = value
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best

    def _search_root(self, grid, depth, my_turn, win_n, deadline, params):
        moves = self.get_feasible_moves(grid)
        if not moves:
            return (None, None), 0

        moves = self._ordered_moves(grid, moves, my_turn, win_n, params)
        opp_turn = 2 if my_turn == 1 else 1
        best_move = moves[0]
        best_score = -float("inf")
        alpha = -float("inf")
        beta = float("inf")

        for y, x in moves:
            self._ensure_time(deadline)
            grid[y][x] = my_turn
            if self._is_win_from(grid, y, x, my_turn, win_n):
                score = params["root_win_score"] + depth
            else:
                score = self.minimax(
                    grid,
                    depth - 1,
                    alpha,
                    beta,
                    opp_turn,
                    my_turn,
                    win_n,
                    deadline,
                    (y, x),
                    my_turn,
                    params,
                )
            grid[y][x] = 0

            if score > best_score:
                best_score = score
                best_move = (y, x)
            if best_score > alpha:
                alpha = best_score

        return best_move, best_score

    def decision(self, matGrid):
        if self.objGameEngine is None:
            return (None, None)

        my_turn = self.objGameEngine.intCurrentTurn
        opp_turn = 2 if my_turn == 1 else 1
        win_n = self.objGameEngine.intConsecutive
        time_limit = float(getattr(self.objGameEngine, "floatTimeLimit", 5.0))

        working_grid = matGrid.copy()
        height, width = working_grid.shape
        params = self._get_eval_params(height, width, win_n)
        moves = self.get_feasible_moves(working_grid)
        if not moves:
            return (None, None)

        for y, x in moves:
            working_grid[y][x] = my_turn
            is_win = self._is_win_from(working_grid, y, x, my_turn, win_n)
            working_grid[y][x] = 0
            if is_win:
                return (y, x)

        for y, x in moves:
            working_grid[y][x] = opp_turn
            opp_wins = self._is_win_from(working_grid, y, x, opp_turn, win_n)
            working_grid[y][x] = 0
            if opp_wins:
                return (y, x)

        safe_budget = self.max_search_seconds
        deadline = time.perf_counter() + safe_budget

        ordered = self._ordered_moves(working_grid, moves, my_turn, win_n, params)
        best_move = ordered[0]

        for depth in range(1, self.max_depth + 1):
            try:
                candidate, _ = self._search_root(working_grid, depth, my_turn, win_n, deadline, params)
                if candidate != (None, None):
                    best_move = candidate
            except SearchTimeout:
                break

        return best_move
