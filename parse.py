import argparse
import concurrent.futures as futures
import csv
import glob
import os
import platform
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import List
from typing import Tuple

import pandas as pd

NUM_PLAYERS_PAT = re.compile(
    r"^\[([0-9.]+)\]\s+DevBalanceStats:\sBALANCE\sSTATS:\s([\w\-'_?`´.,]+)\s\|\s.*\s\|\s([0-9]+)\splayers playing.*$"
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
    active_objectives: List[Tuple[str, str, str]]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "log",
        nargs="+",
        help="server log file to parse",
    )
    ap.add_argument(
        "out",
        help="stats output file",
    )
    ap.add_argument(
        "-p",
        "--player-threshold",
        type=int,
        default=0,
        help="minimum number of players required to "
             "include round in statistics (default=%(default)s)",
    )
    ap.add_argument(
        "--analyze",
        action="store_true",
        default=False,
        help="analyze statistics",
    )

    args = ap.parse_args()

    if platform.system() == "Windows":
        expanded = []
        for _log in args.log:
            expanded.extend(glob.glob(_log))
        args.log = expanded

    return args


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
    active_objectives = []
    map_stats = None

    while len(stack) > 0:
        pat, match = stack.pop()

        if pat == NUM_PLAYERS_PAT:
            name = match.group(2)
            players = int(match.group(3))
        elif pat == WINNING_TEAM_PAT:
            winning_team = match.group(2)
            teams_swapped = bool(match.group(3))
        elif pat == TIME_REMAINING_PAT:
            time_remaining = int(match.group(2))
        elif pat == REINFORCEMENTS_PAT:
            axis_reinforcements = int(match.group(2))
            allies_reinforcements = int(match.group(3))
        elif pat == ACTIVE_OBJECTIVES_PAT:
            active_objectives.append((match.group(2), match.group(3), match.group(4)))
        elif pat == WIN_CONDITION_PAT:
            win_condition = match.group(2)
        elif pat == MATCH_STOP_PAT:
            axis_team_score = int(float(match.group(2)))
            allies_team_score = int(float(match.group(3)))
        else:
            print(f"invalid pattern: {pat}", file=sys.stderr)

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
            active_objectives=active_objectives,
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
    out = Path(args.out)
    analyze = args.analyze

    futs = []
    with ProcessPoolExecutor() as executor:
        for log in logs:
            futs.append(executor.submit(parse_stats, log))

    stats = []
    for fut in futures.as_completed(futs):
        result = fut.result()
        if result:
            stats.extend(result)

    with out.open("w", newline="") as csv_file:
        print(f"writing output to '{Path(out).absolute()}'")
        annotations = MapStats.__annotations__
        csv_file.write(f"{','.join([ann for ann in annotations])}{os.linesep}")
        writer = csv.writer(csv_file)
        for stat in stats:
            # TODO: Temporary!
            if stat.name.lower() == "wwte-mutarantakurgain":
                print(f"skipping: {stat.name}")
                continue
            elif stat.name.lower().startswith("ww"):
                attrs = [getattr(stat, ann) for ann in annotations]
                writer.writerow(attrs)
            else:
                print(f"skipping: {stat.name}")
                continue

    if analyze:
        print("analyzing statistics...")
        df = pd.read_csv(out)
        df = df[df.loc[:, "players"] >= 16]
        print(f"total entries: {len(df)}")

        print("matches played:")
        num_matches = []
        for map_name in df.loc[:, "name"].unique():
            num_matches.append((map_name, len(df[df.loc[:, 'name'] == map_name])))
        num_matches = sorted(num_matches, key=lambda x: int(x[1]), reverse=True)
        for nm in num_matches:
            print(f"\t{nm[0]}: {nm[1]}")

        print()
        print("win ratios:")
        grouped = df.groupby("name")
        for name, group in grouped:
            num_axis_win = len(group[group.loc[:, "winning_team"] == "Axis"])
            num_allies_win = len(group[group.loc[:, "winning_team"] == "Allies"])
            total_win = num_axis_win + num_allies_win
            if num_allies_win > 0:
                allies_win_rate = (num_allies_win / total_win)
            else:
                allies_win_rate = 0.0
            print(
                f"\t{name}: num_axis_win={num_axis_win}, "
                f"num_allies_win={num_allies_win}, "
                f"allies_win_rate={allies_win_rate:.1%}"
            )

        print()
        print("win conditions:")
        for name, group in grouped:
            value_counts = group.loc[:, "win_condition"].value_counts().to_dict()
            value_counts = ",".join([f"{dk}={dv}" for dk, dv in value_counts.items()])
            print(f"\t{name}: {value_counts}")

        # advanced_out = Path(f"{out.name}_advanced_details").with_suffix(".txt")
        # with advanced_out.open("w") as f:
        #     print(f"writing advanced details to file '{advanced_out.absolute}'")
        #     grouped.to_string(f)

        print()
        summary_out = Path(f"{out.stem}_summary").with_suffix(".txt")
        with summary_out.open("w") as f:
            print(f"writing summary to file '{summary_out.absolute()}'")
            grouped.describe().to_string(summary_out)


if __name__ == "__main__":
    main()
