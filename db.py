"""Simple database for map statistics."""

from __future__ import annotations

import ast
import datetime
import sqlite3
from pathlib import Path
from typing import List
from typing import Optional

import pandas as pd

from mapstats import MapStats

MAP_STATS_TABLE = "mapstats"
CONN: Optional[sqlite3.Connection] = None


def get_conn() -> sqlite3.Connection:
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
        conn.execute("begin")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MAP_STATS_TABLE} (
                name TEXT,
                players INTEGER,
                winning_team TEXT,
                time_remaining INTEGER,
                teams_swapped INTEGER,
                axis_reinforcements INTEGER,
                allies_reinforcements INTEGER,
                win_condition TEXT,
                axis_team_score INTEGER,
                allies_team_score INTEGER,
                active_objectives TEXT,  -- This is dirty.
                match_datetime TEXT PRIMARY KEY
            )
            """
        )

    CONN = conn


# noinspection SqlNoDataSourceInspection
def insert_map_stats(map_stats: List[MapStats]):
    conn = get_conn()
    sql = f"""
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
        active_objectives,
        match_datetime
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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
            repr(m.active_objectives),
            m.match_datetime.isoformat(timespec="seconds"),
        )
        for m in map_stats
    ]

    with conn:
        conn.execute("begin")
        conn.executemany(sql, prepared_stats)


# noinspection SqlNoDataSourceInspection
def generate_report(thresh: int, days: int,
                    webhook: Optional[str] = None):
    conn = get_conn()
    days = int(abs(days))
    thresh = int(abs(thresh))

    now = datetime.datetime.now()
    adjusted_date = now - datetime.timedelta(days=days)

    sql = f"""
    SELECT * FROM {MAP_STATS_TABLE}
    WHERE DATETIME(match_datetime) >= DATETIME(?)
    AND players >= ?
    """

    params = (adjusted_date.isoformat(), thresh)

    with conn:
        df = pd.read_sql_query(sql, conn, params=params)
        # Evaluate our dirty column back to Python object.
        df["active_objectives"] = df["active_objectives"].apply(
            lambda x: ast.literal_eval(x))

    # Per-map statistics.
    grouped = df.groupby("name")
    for name, group in grouped:
        print(group)

        games_played = group.shape[0]
        axis_won = group.loc[group["winning_team"] == "Axis"]
        axis_won_count = axis_won.shape[0]
        allies_won = group.loc[group["winning_team"] == "Allies"]
        allies_won_count = allies_won.shape[0]

        print(name, games_played)
        print("Allies won", allies_won_count, f"{round(allies_won_count / games_played, 3):.1%}")
        print("Axis won", axis_won_count, f"{round(axis_won_count / games_played, 3):.1%}")

        # Ignore Supremacy maps.
        if not name[2:].lower().startswith("su"):
            nlargest = group["active_objectives"].value_counts().nlargest(3)
            for objs, _ in nlargest.iteritems():
                for obj in objs:
                    obj_num = obj[0]
                    obj_name = obj[1]
                    obj_holder = obj[2]
                    print(obj_num, obj_name, obj_holder)
                print("*" * 20)

    return df
