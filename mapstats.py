from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List
from typing import Optional
from typing import Tuple


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
    server_id: Optional[str] = None
    match_datetime: Optional[datetime.datetime] = None
