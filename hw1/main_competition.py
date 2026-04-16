import os
import importlib
import pkgutil
import time
import pandas as pd
import hw1
from hw1.engine.BlackjackGameEngine import BlackjackGame


def discover_student_players():
    """
    Scans the 'hw1' package directory for subfolders starting with 'hw_'.
    Dynamically imports the PlayerAgent class from each student's directory.
    """
    lstPlayers = []
    # Identify the physical path of the hw1 package
    pkg_path = os.path.dirname(hw1.__file__)

    print("Searching for student submissions...")

    # Iterate through all modules/packages inside hw1
    for loader, module_name, is_pkg in pkgutil.iter_modules([pkg_path]):
        # Filter for student folders following the 'hw_???????' pattern
        if is_pkg and module_name.startswith("hw_"):
            student_id = module_name.split("_")[1]
            # Construct the full module path: hw1.hw_ID.PlayerAgent_ID
            sub_pkg_name = f"hw1.{module_name}.PlayerAgent_{student_id}"

            try:
                # Dynamically import the student's module
                module = importlib.import_module(sub_pkg_name)
                # Fetch the class attribute named PlayerAgent_???????
                class_name = f"PlayerAgent_{student_id}"
                player_class = getattr(module, class_name)

                # Instantiate the player and add to the list
                player_instance = player_class(strPlayerName=f"Student_{student_id}")
                lstPlayers.append(player_instance)
                print(f"  [Success] Loaded {class_name}")
            except Exception as e:
                print(f"  [Error] Could not load student {student_id}: {e}")

    return lstPlayers


def run_league_competition(strGameID, lstPlayers, intReplication=1000,
                           intFutureCardObs=3, intInitialCardDealNum=1, intTargetScore=31):
    """
    Conducts a 1-on-1 league where every player competes against every other player.
    Saves a win-loss matrix and average decision time statistics to an Excel file.
    """
    player_names = [p.strPlayerName for p in lstPlayers]
    num_players = len(lstPlayers)

    # Initialize data structures for results
    win_matrix = pd.DataFrame(0, index=player_names, columns=player_names)
    time_stats = {name: {"total_time": 0.0, "decision_count": 0} for name in player_names}

    print(f"\nStarting League Tournament ({num_players} players, {intReplication} reps per order)")

    # 1-on-1 Round Robin: Player i vs Player j
    for i in range(num_players):
        for j in range(num_players):
            if i == j: continue  # Skip matches against self

            p1, p2 = lstPlayers[i], lstPlayers[j]

            for rep in range(intReplication):
                # Initialize game with custom settings
                # Settings based on main_play_with_human configuration
                game = BlackjackGame(strGameID, lstPlayers=[p1, p2],
                                     intFutureCardObs=intFutureCardObs,
                                     intInitialCardDealNum=intInitialCardDealNum,
                                     intTargetScore=intTargetScore)

                winner_name, scores, match_times = game.startGame()

                # Log win result
                lstGameLogs = p1.lstGameLogs
                if winner_name == p1.strPlayerName:
                    loser_name = p2.strPlayerName
                else:
                    loser_name = p1.strPlayerName

                if winner_name == None:
                    continue
                win_matrix.loc[winner_name,loser_name] += 1

                for dicLogLine in lstGameLogs:
                    time_stats[dicLogLine['player_name']]["total_time"] += dicLogLine['time']
                    time_stats[dicLogLine['player_name']]["decision_count"] += 1

    # Process and Save results
    avg_times = []
    for name, data in time_stats.items():
        avg = data["total_time"] / data["decision_count"] if data["decision_count"] > 0 else 0
        avg_times.append({"Player": name, "Avg_Decision_Time_Sec": avg})

    output_file = "competition_results.xlsx"
    with pd.ExcelWriter(output_file) as writer:
        win_matrix.to_excel(writer, sheet_name="Win_Comparison_Matrix")
        pd.DataFrame(avg_times).to_excel(writer, sheet_name="Avg_Decision_Time", index=False)

    print(f"\nTournament Complete! Results saved to '{output_file}'.")


if __name__ == "__main__":
    # 1. Discover all students from the hw1 directory
    student_list = discover_student_players()

    if not student_list:
        print("No student agents found. Check folder structure.")
    else:
        # 2. Run the league competition
        run_league_competition('local test competition', student_list, intReplication=1000)