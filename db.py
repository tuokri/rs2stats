from __future__ import annotations

import sqlite3
from pathlib import Path

MAP_STATS_TABLE = "mapstats"


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path.absolute()))
    with conn:
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
                active_objectives TEXT,
                match_datetime TEXT
            )
            """
        )
    return conn
