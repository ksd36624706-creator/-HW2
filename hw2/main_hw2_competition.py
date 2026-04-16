import os
import importlib
import pkgutil
import time
import pandas as pd
import hw2  # 패키지명을 hw2로 변경
from hw2.engine.BingoGameEngine import BingoGameEngine  # Bingo 엔진 임포트


def discover_student_players():
    """
    'hw2' 패키지 디렉토리를 스캔하여 학생들의 PlayerAgent 클래스를 동적으로 로드합니다.

    """
    lstPlayers = []
    pkg_path = os.path.dirname(hw2.__file__)

    print("Searching for student Bingo agents in hw2...")

    for loader, module_name, is_pkg in pkgutil.iter_modules([pkg_path]):
        if is_pkg and module_name.startswith("hw_"):
            student_id = module_name.split("_")[1]
            # 예: hw2.hw_99328161.PlayerAgent_99328161
            sub_pkg_name = f"hw2.{module_name}.PlayerAgent_{student_id}"

            try:
                module = importlib.import_module(sub_pkg_name)
                class_name = f"PlayerAgent_{student_id}"
                player_class = getattr(module, class_name)

                # 학생 인스턴스 생성
                player_instance = player_class(strPlayerName=f"Student_{student_id}")
                lstPlayers.append(player_instance)
                print(f"  [Success] Loaded {class_name}")
            except Exception as e:
                print(f"  [Error] Could not load student {student_id}: {e}")

    return lstPlayers


def run_bingo_league(lstPlayers, intReplication=10, width=11, height=9, intConsecutive=4, floatTimeLimit=5.0):
    """
    모든 플레이어 간의 1대1 리그를 진행합니다.

    """
    player_names = [p.strPlayerName for p in lstPlayers]
    num_players = len(lstPlayers)

    # 결과 저장을 위한 데이터프레임 초기화
    win_matrix = pd.DataFrame(0, index=player_names, columns=player_names)
    time_stats = {name: {"total_time": 0.0, "decision_count": 0} for name in player_names}

    print(f"\nStarting Bingo League ({num_players} players, {intReplication} reps per matchup)")
    print(f"Board: {width}x{height}, Target: {intConsecutive} in a row")

    for i in range(num_players):
        for j in range(num_players):
            if i == j: continue

            p1, p2 = lstPlayers[i], lstPlayers[j]
            print(f"  Match: {p1.strPlayerName} (Green) vs {p2.strPlayerName} (Red)")

            for rep in range(intReplication):
                # BingoGameEngine 인스턴스 생성
                game = BingoGameEngine(game_id=f"Match_{i}_{j}_Rep_{rep}",
                                       lstPlayers=[p1, p2],
                                       width=width,
                                       height=height,
                                       intConsecutive=intConsecutive,
                                       floatTimeLimit=floatTimeLimit)

                winner_name, scores, match_times = game.startGame()  #
                print(winner_name)
                # 승리 기록
                if winner_name:
                    # winner_name이 p1인지 p2인지 확인하여 행렬에 기록
                    loser_name = p2.strPlayerName if winner_name == p1.strPlayerName else p1.strPlayerName
                    win_matrix.loc[winner_name, loser_name] += 1

                # 시간 통계 수집 (모든 플레이어의 로그는 p1의 lstGameLogs에 통합되어 저장됨)
                #
                for log_entry in p1.lstGameLogs:
                    p_name = log_entry['player_name']
                    if 'time' in log_entry:
                        time_stats[p_name]["total_time"] += log_entry['time']
                        time_stats[p_name]["decision_count"] += 1

    # 평균 결정 시간 계산
    avg_times = []
    for name, data in time_stats.items():
        avg = data["total_time"] / data["decision_count"] if data["decision_count"] > 0 else 0
        avg_times.append({"Player": name, "Avg_Decision_Time_Sec": avg})

    # 엑셀 저장
    output_file = "bingo_league_results.xlsx"
    with pd.ExcelWriter(output_file) as writer:
        win_matrix.to_excel(writer, sheet_name="Win_Matrix")
        pd.DataFrame(avg_times).to_excel(writer, sheet_name="Decision_Time", index=False)

    print(f"\nLeague Complete! Results saved to '{output_file}'.")


if __name__ == "__main__":
    # 1. 학생 에이전트 로드
    student_list = discover_student_players()

    if not student_list:
        print("No student agents found in hw2. Check folder structure.")
    else:
        # 2. 빙고 리그 실행 (11x9 보드, 4목 규칙)
        run_bingo_league(student_list, intReplication=5, width=11, height=9, intConsecutive=4)