import re

MATCH_START_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:.*Match Start on:\s+([\w-'_?`´.,]+)\s+.*$"
)
NUM_PLAYERS_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\s([\w-'_?`´.,]+).*"
    r"([0-9]+)\splayers playing.*$"
)
WINNING_TEAM_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\sWinningTeam="
    r"([\w]+)\sTeams\sSwapped=\s([\w]+)$"
)
TIME_REMAINING_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\sTimeRemaining=([0-9]+).*$"
)
REINFORCEMENTS_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\sAxisReinforcements="
    r"([0-9]+)\sAlliesReinforcements=([0-9]+).*$"
)
WIN_CONDITION_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\sWin\sCondition\s([-.\w]+)\s.*$"
)
MATCH_STOP_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\s+.*AxisTeamScore=([0-9.]+)\s+"
    r"AlliesTeamScore=([0-9.]+)$"
)


def main():
    pass


if __name__ == "__main__":
    main()
