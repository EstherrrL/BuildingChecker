"""
规则 1：疏散门 / 疏散走道 净宽度检查。

依据：《建筑设计防火规范》GB 50016 等相关消防规范，疏散门、疏散走道
净宽有最低限值要求。本 Agent 中采用可配置的示例阈值，实际项目请以
所在地现行规范、建筑类型、疏散人数计算结果为准。

判断逻辑：
  - 对每个标记为 is_escape_door=True 的门，若 overall_width < door_min_width，判定不合规。
  - 对每个标记为 is_escape_route=True 的走道，若 width < corridor_min_width，判定不合规。
  - 缺失宽度数据（None）时，标记为需要人工核实，而不是直接判定违规（避免误报）。
"""

from __future__ import annotations

from typing import List

from src.models import BuildingModel, Issue
from src.rules.base import Rule


class EscapeWidthRule(Rule):
    rule_id = "R1-EscapeWidth"
    description = "疏散门/疏散走道净宽度检查"

    def __init__(self, door_min_width: float = 0.9, corridor_min_width: float = 1.2):
        self.door_min_width = door_min_width
        self.corridor_min_width = corridor_min_width

    def check(self, model: BuildingModel) -> List[Issue]:
        issues: List[Issue] = []

        for door in model.doors:
            if not door.is_escape_door:
                continue
            if door.overall_width is None:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        severity="low",
                        element_id=door.id,
                        element_name=door.name or door.id,
                        message="疏散门缺少净宽数据，无法自动判断是否合规",
                        threshold=self.door_min_width,
                        suggestion="请补充该门的 OverallWidth 属性后重新检查",
                    )
                )
                continue
            if door.overall_width < self.door_min_width:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        severity="high",
                        element_id=door.id,
                        element_name=door.name or door.id,
                        message=(
                            f"疏散门净宽 {door.overall_width:.2f}m 低于规范要求 "
                            f"{self.door_min_width:.2f}m"
                        ),
                        measured_value=door.overall_width,
                        threshold=self.door_min_width,
                        suggestion="建议调整门洞尺寸或更换为满足净宽要求的疏散门",
                    )
                )

        for corridor in model.corridors:
            if not corridor.is_escape_route:
                continue
            if corridor.width is None:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        severity="low",
                        element_id=corridor.id,
                        element_name=corridor.name or corridor.id,
                        message="疏散走道缺少宽度数据，无法自动判断是否合规",
                        threshold=self.corridor_min_width,
                        suggestion="请补充该走道的宽度属性后重新检查",
                    )
                )
                continue
            if corridor.width < self.corridor_min_width:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        severity="high",
                        element_id=corridor.id,
                        element_name=corridor.name or corridor.id,
                        message=(
                            f"疏散走道净宽 {corridor.width:.2f}m 低于规范要求 "
                            f"{self.corridor_min_width:.2f}m"
                        ),
                        measured_value=corridor.width,
                        threshold=self.corridor_min_width,
                        suggestion="建议调整走道布局或墙体位置以满足疏散净宽要求",
                    )
                )

        return issues
