"""
规则 2：构件关键属性完整性检查。

依据：BIM 交付标准（如 COBie、国内 BIM 施工图交付标准）通常要求
门窗类构件填写关键属性（名称、耐火等级等），缺失将影响后续消防审查、
算量、运维等下游流程。

判断逻辑：
  - 所有门都应有非空 Name。
  - 标记为 is_escape_door=True 的门（疏散门/防火门场景）必须填写 fire_rating，
    缺失时判定为高优先级问题（直接影响消防审查）。
  - 非疏散门缺少 fire_rating 不强制要求，不产生 Issue。
"""

from __future__ import annotations

from typing import List

from src.models import BuildingModel, Issue
from src.rules.base import Rule


class PropertyCompletenessRule(Rule):
    rule_id = "R2-PropertyCompleteness"
    description = "构件关键属性完整性检查（名称 / 耐火等级）"

    def check(self, model: BuildingModel) -> List[Issue]:
        issues: List[Issue] = []

        for door in model.doors:
            missing = []

            if not door.name or not door.name.strip():
                missing.append("Name（构件名称）")

            if door.is_escape_door and not (door.fire_rating and door.fire_rating.strip()):
                missing.append("FireRating（耐火等级）")

            if not missing:
                continue

            severity = "high" if door.is_escape_door else "medium"
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    severity=severity,
                    element_id=door.id,
                    element_name=door.name or door.id,
                    message=f"构件缺少关键属性：{ '、'.join(missing) }",
                    suggestion="请在模型中补充上述属性，避免影响消防审查/算量等下游流程",
                )
            )

        return issues
