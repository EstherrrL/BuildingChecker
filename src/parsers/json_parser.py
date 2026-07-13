"""从简化 JSON 模型文件解析为统一的 BuildingModel。"""

import json
from pathlib import Path

from src.models import BuildingModel, Door, Corridor


def parse_json_model(path: str | Path) -> BuildingModel:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    doors = [
        Door(
            id=d.get("id", "UNKNOWN"),
            name=d.get("name", ""),
            overall_width=d.get("overall_width"),
            fire_rating=d.get("fire_rating"),
            is_escape_door=bool(d.get("is_escape_door", False)),
        )
        for d in raw.get("doors", [])
    ]

    corridors = [
        Corridor(
            id=c.get("id", "UNKNOWN"),
            name=c.get("name", ""),
            width=c.get("width"),
            is_escape_route=bool(c.get("is_escape_route", False)),
        )
        for c in raw.get("corridors", [])
    ]

    return BuildingModel(
        project=raw.get("project", "Untitled Project"),
        doors=doors,
        corridors=corridors,
    )
