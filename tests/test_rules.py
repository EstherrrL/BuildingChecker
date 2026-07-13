""" 单元测试：验证两条规则在构造用例上的判断是否正确。 """

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import BuildingModel, Door, Corridor
from src.rules.rule_escape_width import EscapeWidthRule
from src.rules.rule_property_completeness import PropertyCompletenessRule
from src.parsers.json_parser import parse_json_model


def test_escape_width_flags_narrow_door():
    model = BuildingModel(
        project="test",
        doors=[Door(id="D1", name="门1", overall_width=0.85, is_escape_door=True)],
    )
    issues = EscapeWidthRule().check(model)
    assert len(issues) == 1
    assert issues[0].severity == "high"
    assert issues[0].element_id == "D1"


def test_escape_width_passes_wide_door():
    model = BuildingModel(
        project="test",
        doors=[Door(id="D2", name="门2", overall_width=1.0, is_escape_door=True)],
    )
    issues = EscapeWidthRule().check(model)
    assert len(issues) == 0


def test_escape_width_ignores_non_escape_door():
    model = BuildingModel(
        project="test",
        doors=[Door(id="D3", name="门3", overall_width=0.5, is_escape_door=False)],
    )
    issues = EscapeWidthRule().check(model)
    assert len(issues) == 0


def test_escape_width_boundary_value_is_compliant():
    model = BuildingModel(
        project="test",
        doors=[Door(id="D4", name="门4", overall_width=0.9, is_escape_door=True)],
    )
    issues = EscapeWidthRule().check(model)
    assert len(issues) == 0  # 恰好等于阈值，视为合规


def test_escape_width_missing_data_is_low_severity():
    model = BuildingModel(
        project="test",
        corridors=[Corridor(id="C1", name="走道1", width=None, is_escape_route=True)],
    )
    issues = EscapeWidthRule().check(model)
    assert len(issues) == 1
    assert issues[0].severity == "low"


def test_property_completeness_flags_missing_fire_rating_on_escape_door():
    model = BuildingModel(
        project="test",
        doors=[Door(id="D5", name="疏散门", overall_width=1.0, fire_rating="", is_escape_door=True)],
    )
    issues = PropertyCompletenessRule().check(model)
    assert len(issues) == 1
    assert issues[0].severity == "high"
    assert "FireRating" in issues[0].message


def test_property_completeness_ignores_missing_fire_rating_on_normal_door():
    model = BuildingModel(
        project="test",
        doors=[Door(id="D6", name="普通门", overall_width=0.9, fire_rating="", is_escape_door=False)],
    )
    issues = PropertyCompletenessRule().check(model)
    assert len(issues) == 0


def test_property_completeness_flags_missing_name():
    model = BuildingModel(
        project="test",
        doors=[Door(id="D7", name="", overall_width=0.9, fire_rating="A1.0h", is_escape_door=False)],
    )
    issues = PropertyCompletenessRule().check(model)
    assert len(issues) == 1
    assert "Name" in issues[0].message


def test_sample_model_json_produces_expected_issue_count():
    model = parse_json_model(Path(__file__).resolve().parent.parent / "data" / "sample_model.json")
    issues = EscapeWidthRule().check(model) + PropertyCompletenessRule().check(model)
    assert len(issues) > 0


def test_compliant_sample_model_has_no_issues():
    model = parse_json_model(
        Path(__file__).resolve().parent.parent / "data" / "sample_model_compliant.json"
    )
    issues = EscapeWidthRule().check(model) + PropertyCompletenessRule().check(model)
    assert len(issues) == 0
