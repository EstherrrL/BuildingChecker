"""规则引擎基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.models import BuildingModel, Issue


class Rule(ABC):
    """所有检查规则的抽象基类。"""

    rule_id: str = "R0-Base"
    description: str = ""

    @abstractmethod
    def check(self, model: BuildingModel) -> List[Issue]:
        """对给定的建筑模型执行检查，返回发现的问题列表（无问题则返回空列表）。"""
        raise NotImplementedError
