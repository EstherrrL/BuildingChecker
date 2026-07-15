"""
阈值配置表加载工具。

将疏散门/走道净宽度的阈值从代码中抽离到 data/thresholds.json，
支持按 (region, building_type) 组合查询，体现"规范因地区/建筑类型而异"
这一工程认知，同时保持数值判断的确定性（查表，而非LLM/检索猜测）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

THRESHOLDS_PATH = Path(__file__).resolve().parent.parent / "data" / "thresholds.json"


def load_thresholds() -> dict:
    with THRESHOLDS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_regions(thresholds: Optional[dict] = None) -> list[tuple[str, str]]:
    """返回 [(region_code, region_label), ...]"""
    thresholds = thresholds or load_thresholds()
    return [(code, info["label"]) for code, info in thresholds["regions"].items()]


def list_building_types(region: str, thresholds: Optional[dict] = None) -> list[tuple[str, str]]:
    """返回指定地区下 [(type_code, type_label), ...]"""
    thresholds = thresholds or load_thresholds()
    types = thresholds["regions"][region]["building_types"]
    return [(code, info["label"]) for code, info in types.items()]


def get_thresholds(region: str, building_type: str, thresholds: Optional[dict] = None) -> dict:
    """
    查询指定地区+建筑类型对应的阈值。
    返回：{"door_min_width": float, "corridor_min_width": float, "reference_code": str}
    """
    thresholds = thresholds or load_thresholds()
    region_info = thresholds["regions"][region]
    type_info = region_info["building_types"][building_type]
    return {
        "door_min_width": type_info["door_min_width"],
        "corridor_min_width": type_info["corridor_min_width"],
        "reference_code": region_info.get("reference_code", ""),
    }
