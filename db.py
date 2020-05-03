"""Simple database for map statistics."""

from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path
from typing import List
from typing import Optional

import pandas as pd

from mapstats import MapStats

MAP_STATS_TABLE = "mapstats"
MAP_END_OBJECTIVES_TABLE = "map_end_objectives"
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
                obj_name TEXT NOT NULL,
                holder TEXT,
                match_datetime TEXT NOT NULL REFERENCES 
                    {MAP_STATS_TABLE} (match_datetime),
                server_id TEXT NOT NULL REFERENCES 
                    {MAP_STATS_TABLE} (server_id),
                map_name TEXT NOT NULL REFERENCES 
                    {MAP_STATS_TABLE} (name),
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

    # Per-map statistics.
    grouped = objs_stats_df.groupby("name")

    for name, group in grouped:
        games_played = group.shape[0]
        axis_won = group.loc[group["winning_team"] == "Axis"]
        axis_won_count = axis_won.shape[0]
        allies_won = group.loc[group["winning_team"] == "Allies"]
        allies_won_count = allies_won.shape[0]

        print(name, games_played, "games played")
        print("Allies won", allies_won_count, f"{round(allies_won_count / games_played, 3):.1%}")
        print("Axis won", axis_won_count, f"{round(axis_won_count / games_played, 3):.1%}")

        # Ignore Supremacy maps for objective statistics.
        if not name[2:].lower().startswith("su"):
            nlargest_objs = group["obj_name"].value_counts().nlargest(3)
            print(nlargest_objs.to_dict())

            nlargest_df = group.loc[group["obj_name"].isin(nlargest_objs.index)]
            print(nlargest_df)

            print("----")

            nlargest_grouped = nlargest_df.groupby(["match_datetime", "server_id"])
            for nname, ngroup in nlargest_grouped:
                print(nname)
                print(ngroup)

            print("*" * 100)

    return map_stats_df
