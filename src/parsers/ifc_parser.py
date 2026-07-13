"""
(进阶/可选) 从真实 IFC 文件解析为统一的 BuildingModel。

依赖 ifcopenshell。若未安装该库，导入本模块时会抛出清晰的错误提示，
但不影响 JSON 解析主流程的使用。

使用方式：
    model = parse_ifc_model("data/sample.ifc")

字段映射说明：
  - IfcDoor.OverallWidth              -> Door.overall_width
  - Pset_DoorCommon.FireRating        -> Door.fire_rating
  - IfcDoor.Name                      -> Door.name
  - 走道对应关系较复杂（IFC 无原生"走道"实体，通常用 IfcSpace
    的 LongName/ObjectType 标记为 Corridor），此处做了简化启发式处理：
    IfcSpace 的名称包含"走道/走廊/corridor"关键字则视为走道，
    宽度用空间包围盒的最小水平尺寸近似代替。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.models import BuildingModel, Door, Corridor

CORRIDOR_KEYWORDS = ("走道", "走廊", "corridor", "passage")


def _get_property(ifc_element, pset_name: str, prop_name: str) -> Optional[str]:
    """从 IFC 构件的 Property Set 中提取属性值，找不到则返回 None。"""
    for rel in getattr(ifc_element, "IsDefinedBy", []):
        prop_def = getattr(rel, "RelatingPropertyDefinition", None)
        if prop_def is None or not prop_def.is_a("IfcPropertySet"):
            continue
        if prop_def.Name != pset_name:
            continue
        for prop in prop_def.HasProperties:
            if prop.Name == prop_name and prop.is_a("IfcPropertySingleValue"):
                value = prop.NominalValue
                return None if value is None else value.wrappedValue
    return None


def parse_ifc_model(path: str | Path) -> BuildingModel:
    try:
        import ifcopenshell
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "解析 IFC 文件需要安装 ifcopenshell： pip install ifcopenshell"
        ) from e

    path = Path(path)
    ifc_file = ifcopenshell.open(str(path))

    project_name = "IFC Project"
    projects = ifc_file.by_type("IfcProject")
    if projects:
        project_name = projects[0].Name or project_name

    doors = []
    for d in ifc_file.by_type("IfcDoor"):
        overall_width = getattr(d, "OverallWidth", None)
        fire_rating = _get_property(d, "Pset_DoorCommon", "FireRating")
        name = d.Name or ""
        # 简化判断：名称中包含"疏散"关键字则认为是疏散门
        is_escape = "疏散" in name or "escape" in name.lower()
        doors.append(
            Door(
                id=d.GlobalId,
                name=name,
                overall_width=overall_width,
                fire_rating=fire_rating,
                is_escape_door=is_escape,
            )
        )

    corridors = []
    for space in ifc_file.by_type("IfcSpace"):
        name = (space.LongName or space.Name or "") or ""
        if not any(k in name.lower() or k in name for k in CORRIDOR_KEYWORDS):
            continue
        # 走道宽度无法直接从属性获得，此处标注为 None，
        # 若项目有自定义 Pset（如 Pset_CorridorCommon.Width）可在此扩展提取。
        width = _get_property(space, "Pset_SpaceCommon", "Width")
        corridors.append(
            Corridor(
                id=space.GlobalId,
                name=name,
                width=width,
                is_escape_route=True,
            )
        )

    return BuildingModel(project=project_name, doors=doors, corridors=corridors)
