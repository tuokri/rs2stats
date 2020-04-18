import argparse
import concurrent.futures as futures
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List
from typing import Tuple

NUM_PLAYERS_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\s([\w\-'_?`´.,]+)\s\|\s.*([0-9]+)\splayers playing.*$"
)
WINNING_TEAM_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\sWinningTeam=([\w]+)\sTeams\sSwapped=\s([\w]+)$"
)
TIME_REMAINING_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\sTimeRemaining=([0-9]+).*$"
)
REINFORCEMENTS_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\sAxisReinforcements=([\-0-9]+)\sAlliesReinforcements=([\-0-9]+).*$"
)
ACTIVE_OBJECTIVES_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\s+.*ActiveObjectives\s([0-9]+)\s=\s([\w \-.'?´`]+)\sStatus=([\w]+)$"
)
WIN_CONDITION_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\sWin\sCondition\s([-.\w]+)\s.*$"
)
MATCH_STOP_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\s+.*AxisTeamScore=([0-9.]+)\s+AlliesTeamScore=([0-9.]+)$"
)

CANDIDATES = [
    WINNING_TEAM_PAT,
    TIME_REMAINING_PAT,
    REINFORCEMENTS_PAT,
    ACTIVE_OBJECTIVES_PAT,
    WIN_CONDITION_PAT,
]


@dataclass
class MapStats:
    name: str
    players: int
    winning_team: str
    time_remaining: int
    teams_swapped: bool
    axis_reinforcements: int
    allies_reinforcements: int
    win_condition: str
    axis_team_score: int
    allies_team_score: int


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "log",
        nargs="+",
        help="server log file to parse",
    )
    ap.add_argument(
        "-p",
        "--player-threshold",
        type=int,
        default=0,
        help="minimum number of players required to "
             "include round in statistics (default=%(default)s)"
    )

    return ap.parse_args()


def parse_match_stack(stack: List[Tuple[re.Pattern, re.Match]]) -> MapStats:
    name = ""
    players = 0
    winning_team = ""
    time_remaining = 0
    teams_swapped = False
    axis_reinforcements = 0
    allies_reinforcements = 0
    win_condition = ""
    axis_team_score = 0
    allies_team_score = 0
    map_stats = None

    while len(stack) > 0:
        pat, match = stack.pop()

        if pat == NUM_PLAYERS_PAT:
            name = match.group(1)
            players = int(match.group(2))
        elif pat == WINNING_TEAM_PAT:
            winning_team = match.group(1)
            teams_swapped = bool(match.group(2))
        # elif pat == TIME_REMAINING_PAT:
        #    time_remaining =

        map_stats = MapStats(
            name=name,
            players=players,
            winning_team=winning_team,
            time_remaining=time_remaining,
            teams_swapped=teams_swapped,
            axis_reinforcements=axis_reinforcements,
            allies_reinforcements=allies_reinforcements,
            win_condition=win_condition,
            axis_team_score=axis_team_score,
            allies_team_score=allies_team_score,
        )

    return map_stats


def parse_stats(log: Path) -> List[MapStats]:
    ret = []
    stack = []
    flag = False
    try:
        with log.open("r") as f:
            for line in f:
                if not flag:
                    m = NUM_PLAYERS_PAT.match(line)
                    if m:
                        # Found beginning of balance stats sequence.
                        flag = True
                        stack.append((NUM_PLAYERS_PAT, m))
                else:
                    m = MATCH_STOP_PAT.match(line)
                    if m:
                        # Found end of balance stats sequence.
                        flag = False
                        stack.append((MATCH_STOP_PAT, m))
                        ret.append(parse_match_stack(stack))
                    else:
                        for candidate in CANDIDATES:
                            mc = candidate.match(line)
                            if mc:
                                stack.append((candidate, mc))
    except EnvironmentError as e:
        print(f"error reading '{log.absolute()}': {repr(e)}",
              file=sys.stderr)
    return ret


def main():
    args = parse_args()
    logs = [Path(log) for log in args.log]

    futs = []
    with ProcessPoolExecutor() as executor:
        for log in logs:
            futs.append(executor.submit(parse_stats, log))

    stats = []
    for fut in futures.as_completed(futs):
        result = fut.result()
        if result:
            stats.extend(result)

    print(stats)


if __name__ == "__main__":
    main()
