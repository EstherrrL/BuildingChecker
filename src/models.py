"""
统一的内部数据模型 (Building Model)。
无论输入是 IFC 还是简化 JSON，解析器都会转换为这里定义的结构，
后续规则引擎只依赖这套模型，不关心原始数据格式。
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class Door(BaseModel):
    """门/疏散门。字段对应 IFC 中 IfcDoor + Pset_DoorCommon 的常用属性。"""

    id: str
    name: Optional[str] = ""
    overall_width: Optional[float] = Field(
        default=None, description="门净宽，单位：米。对应 IfcDoor.OverallWidth"
    )
    fire_rating: Optional[str] = Field(
        default=None, description="耐火等级，对应 Pset_DoorCommon.FireRating"
    )
    is_escape_door: bool = Field(default=False, description="是否为疏散门")


class Corridor(BaseModel):
    """走道/疏散通道。"""

    id: str
    name: Optional[str] = ""
    width: Optional[float] = Field(default=None, description="走道净宽，单位：米")
    is_escape_route: bool = Field(default=False, description="是否为疏散路径的一部分")


class BuildingModel(BaseModel):
    """一个建筑模型的简化表示，供规则引擎统一消费。"""

    project: str = "Untitled Project"
    doors: List[Door] = Field(default_factory=list)
    corridors: List[Corridor] = Field(default_factory=list)


class Issue(BaseModel):
    """规则引擎产出的单条检查结果。"""

    rule_id: str
    severity: str  # "high" | "medium" | "low"
    element_id: str
    element_name: str = ""
    message: str
    measured_value: Optional[float] = None
    threshold: Optional[float] = None
    suggestion: str = ""
