"""Simple database for map statistics."""

from __future__ import annotations

import datetime
import sqlite3
import sys
from pathlib import Path
from pprint import pprint
from typing import List
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
import seaborn as sns

from mapstats import MapStats

sns.set()

MAP_STATS_TABLE = "mapstats"
MAP_END_OBJECTIVES_TABLE = "map_end_objectives"
CONN: Optional[sqlite3.Connection] = None


def get_conn() -> sqlite3.Connection:
    global CONN
    if not CONN:
        raise RuntimeError("database not initialized")
    return CONN


# noinspection SqlNoDataSourceInspection
def init_db(db_path: Path):
    """Return connection to database and
    create tables if needed.
    """
    global CONN

    conn = sqlite3.connect(str(db_path.absolute()))

    with conn:
        conn.execute("PRAGMA foreign_keys = ON")

    with conn:
        conn.execute("begin")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MAP_STATS_TABLE} (
                name TEXT NOT NULL,
                players INTEGER,
                winning_team TEXT,
                time_remaining INTEGER,
                teams_swapped INTEGER,
                axis_reinforcements INTEGER,
                allies_reinforcements INTEGER,
                win_condition TEXT,
                axis_team_score INTEGER,
                allies_team_score INTEGER,
                match_datetime TEXT NOT NULL,
                server_id TEXT NOT NULL,
                PRIMARY KEY (name, match_datetime, server_id)
            )
            """
        )

    with conn:
        conn.execute("begin")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MAP_END_OBJECTIVES_TABLE} (
                obj_index INTEGER,
                obj_name TEXT,
                holder TEXT,
                match_datetime TEXT NOT NULL,
                server_id TEXT NOT NULL,
                map_name TEXT NOT NULL,
                FOREIGN KEY (match_datetime, server_id, map_name)
                REFERENCES {MAP_STATS_TABLE} (match_datetime, server_id, name)
                PRIMARY KEY (match_datetime, server_id, map_name, obj_name)
            )
            """
        )

    CONN = conn


# noinspection SqlNoDataSourceInspection
def insert_map_stats(map_stats: List[MapStats]):
    conn = get_conn()
    sql_map_stats = f"""
    INSERT OR IGNORE INTO {MAP_STATS_TABLE} (
        name,
        players,
        winning_team,
        time_remaining,
        teams_swapped,
        axis_reinforcements,
        allies_reinforcements,
        win_condition,
        axis_team_score,
        allies_team_score,
        match_datetime,
        server_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    sql_active_objs = f"""
    INSERT OR IGNORE INTO {MAP_END_OBJECTIVES_TABLE} (
        obj_index,
        obj_name,
        holder,
        match_datetime,
        server_id,
        map_name
    ) VALUES (
        ?,
        ?,
        ?,
        (SELECT match_datetime from {MAP_STATS_TABLE} 
         WHERE {MAP_STATS_TABLE}.match_datetime=?),
        (SELECT server_id FROM {MAP_STATS_TABLE} 
         WHERE {MAP_STATS_TABLE}.server_id=?),
        (SELECT name FROM {MAP_STATS_TABLE} 
         WHERE {MAP_STATS_TABLE}.name=?)
    )
    """

    prepared_stats = [
        (
            m.name,
            m.players,
            m.winning_team,
            m.time_remaining,
            m.teams_swapped,
            m.axis_reinforcements,
            m.allies_reinforcements,
            m.win_condition,
            m.axis_team_score,
            m.allies_team_score,
            m.match_datetime.isoformat(),
            m.server_id,
        )
        for m in map_stats
    ]

    active_objs = []
    for m in map_stats:
        for ao in m.active_objectives:
            active_objs.append((
                *ao,
                m.match_datetime.isoformat(),
                m.server_id,
                m.name,
            ))

    with conn:
        conn.execute("begin")
        conn.executemany(sql_map_stats, prepared_stats)
    with conn:
        conn.execute("begin")
        conn.executemany(sql_active_objs, active_objs)


# noinspection SqlNoDataSourceInspection
def generate_report(thresh: int, days: int,
                    webhook: Optional[str] = None):
    conn = get_conn()
    days = int(abs(days))
    thresh = int(abs(thresh))

    now = datetime.datetime.now()
    adjusted_date = now - datetime.timedelta(days=days)

    sql_map_stats = f"""
    SELECT * FROM {MAP_STATS_TABLE}
    WHERE DATETIME(match_datetime) >= DATETIME(?)
    AND players >= ?
    """

    sql_objectives = f"""
    SELECT * FROM {MAP_END_OBJECTIVES_TABLE}
    WHERE DATETIME(match_datetime) >= DATETIME(?)
    """

    map_stats_params = (adjusted_date.isoformat(), thresh)
    objectives_params = (adjusted_date.isoformat(),)

    with conn:
        map_stats_df = pd.read_sql_query(
            sql_map_stats, conn, params=map_stats_params)
        objectives_df = pd.read_sql_query(
            sql_objectives, conn, params=objectives_params)

    objs_stats_df = map_stats_df.merge(
        objectives_df,
        on=["match_datetime", "server_id"],
    )

    map_stats_df["match_datetime"] = pd.to_datetime(
        map_stats_df["match_datetime"])

    map_stats_df["axis_win"] = map_stats_df.loc[:, "winning_team"] == "Axis"
    map_stats_df["allies_win"] = map_stats_df.loc[:, "winning_team"] == "Allies"

    # map_stats_df.value_counts().plot.pie(y="name")
    # plt.show()

    def _fmt(pct, allvals):
        absolute = int(pct / 100. * np.sum(allvals))
        return "{:.1f}%\n({:d})".format(pct, absolute)

    _, ax = plt.subplots(figsize=(10, 10))

    map_value_counts = map_stats_df["name"].value_counts()

    mvc_top5 = map_value_counts.iloc[:5]
    mvc_others = map_value_counts.iloc[5:]

    mvc_top5["others"] = mvc_others.sum()
    mvc_top5.sort_values(ascending=False)

    wedges, texts, _ = ax.pie(
        mvc_top5,
        autopct=lambda pct: _fmt(pct, mvc_top5),
        textprops={"color": "white"},
        pctdistance=0.75,
    )

    plt.legend(
        wedges,
        mvc_top5.index,
        title="Map name",
        loc="center right",
        bbox_to_anchor=(1.2, -0.1),
        # bbox_transform=plt.gcf().transFigure,
    )

    start_dt = map_stats_df["match_datetime"].min().strftime("%d.%m.%Y")
    stop_dt = map_stats_df["match_datetime"].max().strftime("%d.%m.%Y")
    plt.title(f"Played rounds ({start_dt} - {stop_dt})")
    plt.show()

    # Remove duplicate columns.
    objs_stats_df = objs_stats_df.loc[:, ~objs_stats_df.columns.duplicated()]

    # Per-map statistics.
    map_stats_grouped = map_stats_df.groupby("name")

    for name, group in map_stats_grouped:
        games_played = group.shape[0]
        axis_won = group.loc[group["winning_team"] == "Axis"]
        axis_won_count = axis_won.shape[0]
        allies_won = group.loc[group["winning_team"] == "Allies"]
        allies_won_count = allies_won.shape[0]

        print(name, games_played, "games played")
        print("Allies won", allies_won_count,
              f"({round(allies_won_count / games_played, 3):.1%})")
        print("Axis won", axis_won_count,
              f"({round(axis_won_count / games_played, 3):.1%})")

        print("---")
        print("Axis reinforcements on round end:")
        axis_rein = group["axis_reinforcements"].describe().astype(int).to_dict()
        del axis_rein["count"]
        pprint(axis_rein)

        print("---")
        print("Allies reinforcements on round end:")
        allies_rein = group["allies_reinforcements"].describe().astype(int).to_dict()
        del allies_rein["count"]
        pprint(allies_rein)

        print("---")
        print("Top 3 win conditions:")
        pprint(group["win_condition"].value_counts().nlargest(3).to_dict())

        print("---")
        print("Top 3 hottest objectives on round end:")
        no_allcaps = objs_stats_df[
            (objs_stats_df["win_condition"] != "ROWC_AllObjectiveCaptured")
            & (objs_stats_df["name"] == name)
            ]
        pprint(no_allcaps["obj_name"].value_counts().nlargest(3).to_dict())

        # Ignore Supremacy maps for objective statistics.
        if not name[2:].lower().startswith("su"):
            with pd.option_context("display.max_rows", None,
                                   "display.max_columns", None,
                                   "display.width", 500):
                asd = objs_stats_df.loc[
                    objs_stats_df["match_datetime"].isin(group["match_datetime"])
                    & objs_stats_df["server_id"].isin(group["server_id"])
                    ]
                # print(asd)
                grouped_x = asd.groupby(["match_datetime", "server_id"])
                # for xname, xgroup in grouped_x:
                #    print(xgroup["obj_name"].value_counts())

                # print(grouped_by_match.size().droplevel(
                #     level="match_datetime").droplevel("server_id").index.value_counts())
                # print(grouped_by_match.size().index.get_level_values("obj_name"))

                # for mname, mgroup in grouped_by_match:
                #     print(mname)
                #     print(mgroup)
                #     print("*" * 10)

            # for mname, mgroup in grouped_by_match:
            #     print("-" * 20)

            # nlargest_objs = group["obj_name"].value_counts().nlargest(3)
            # print(nlargest_objs.to_dict())
            #
            # nlargest_df = group.loc[group["obj_name"].isin(nlargest_objs.index)]
            # print(nlargest_df)
            #
            # print("----")
            #
            # nlargest_grouped = nlargest_df.groupby(["match_datetime", "server_id"])
            # for nname, ngroup in nlargest_grouped:
            #     print(nname)
            #     print(ngroup)

            print("*" * 100)

        group_ts = group.set_index("match_datetime")
        group_ts_mean = group_ts.resample("1d").mean()
        time_remaining = group_ts_mean["time_remaining"]
        ax = sns.lineplot(marker="*", data=time_remaining)
        ax.set_title(name)
        ax.set_ylabel("mean time remaining (s)")

        plt.gcf().autofmt_xdate()
        plt.show()

    # Win ratio plots.
    for name, group in map_stats_grouped:
        print(f"plotting win ratio for: {name}")
        group_ts = group.set_index("match_datetime")
        group_ts_sum = group_ts.resample("1d").sum()

        group_ts_sum["axis_win"] = group_ts_sum["axis_win"].astype(int)
        group_ts_sum["allies_win"] = group_ts_sum["allies_win"].astype(int)
        games_played = (group_ts_sum["axis_win"]
                        + group_ts_sum["allies_win"]).astype(int)
        print(games_played)

        axis_win_ratio = (group_ts_sum["axis_win"] / games_played) * 100

        ax = sns.lineplot(axis_win_ratio.index, axis_win_ratio, marker="*",
                          color="blue")
        ax.set_ylabel("Axis win ratio (%)", color="blue")

        ax2 = ax.twinx()
        ax2.plot(games_played.index, games_played, marker=".",
                 color="green")
        ax2.set_ylabel("rounds played", color="green")

        locator = matplotlib.ticker.MultipleLocator(1)
        ax2.yaxis.set_major_locator(locator)
        ax2.grid(None)

        plt.title(name)
        plt.gcf().autofmt_xdate()
        plt.show()

    return map_stats_df
