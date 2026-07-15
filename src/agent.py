"""
Agent 主流程：解析模型 -> 运行规则 -> (可选) LLM 总结 -> 返回结果。

LLM 总结部分做成可插拔，支持两种后端（按优先级检测环境变量）：
  1. 火山方舟 Ark（字节跳动豆包）：设置 ARK_API_KEY + ARK_ENDPOINT_ID
  2. OpenAI：设置 OPENAI_API_KEY
  若都未设置，则使用本地的简单模板生成"伪总结"（保证 Demo 在无网络/无 API Key 时也能完整跑通）。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from src.models import BuildingModel, Issue
from src.parsers.json_parser import parse_json_model
from src.rules.rule_escape_width import EscapeWidthRule
from src.rules.rule_property_completeness import PropertyCompletenessRule
from src.thresholds import get_thresholds

DEFAULT_RULES = [EscapeWidthRule(), PropertyCompletenessRule()]


def load_model(input_path: str | Path) -> BuildingModel:
    input_path = Path(input_path)
    if input_path.suffix.lower() == ".ifc":
        from src.parsers.ifc_parser import parse_ifc_model

        return parse_ifc_model(input_path)
    return parse_json_model(input_path)


def build_rules(region: str | None = None, building_type: str | None = None) -> list:
    """
    根据 (region, building_type) 从阈值配置表中查出对应数值，构建规则实例。
    未指定时使用 EscapeWidthRule 的默认值（door>=0.9m, corridor>=1.2m）。
    """
    if region and building_type:
        thresholds = get_thresholds(region, building_type)
        escape_rule = EscapeWidthRule(
            door_min_width=thresholds["door_min_width"],
            corridor_min_width=thresholds["corridor_min_width"],
        )
    else:
        escape_rule = EscapeWidthRule()
    return [escape_rule, PropertyCompletenessRule()]


def run_rules(model: BuildingModel, rules=None) -> List[Issue]:
    rules = rules or DEFAULT_RULES
    issues: List[Issue] = []
    for rule in rules:
        issues.extend(rule.check(model))
    return issues


def _fallback_summary(model: BuildingModel, issues: List[Issue]) -> str:
    """无 LLM 可用时的本地模板总结（保证离线可运行）。"""
    if not issues:
        return (
            f"在“{model.project}”模型中，未发现违反已实现规则（疏散宽度、属性完整性）的问题。"
            "注意：本次检查覆盖范围有限，建议结合专业消防/结构审查进行综合评估。"
        )

    high = [i for i in issues if i.severity == "high"]
    medium = [i for i in issues if i.severity == "medium"]
    low = [i for i in issues if i.severity == "low"]

    lines = [f"在“{model.project}”模型中共发现 {len(issues)} 项问题。"]
    if high:
        names = "、".join(sorted({i.element_id for i in high}))
        lines.append(f"高优先级问题 {len(high)} 项，涉及构件：{names}，建议优先整改。")
    if medium:
        lines.append(f"中优先级问题 {len(medium)} 项，建议在下一版提交前补全相关信息。")
    if low:
        lines.append(f"低优先级问题 {len(low)} 项，多为数据缺失导致无法自动判断，建议补充数据后重新检查。")
    lines.append("本次检查仅覆盖疏散宽度与关键属性完整性两类规则，建议结合专业审查综合评估。")
    return " ".join(lines)


def _build_llm_client():
    """
    根据环境变量选择 LLM 后端，返回 (client, model_name) 或 (None, None)。
    优先使用火山方舟 Ark（豆包），其次 OpenAI。
    """
    ark_key = os.environ.get("ARK_API_KEY")
    ark_endpoint = os.environ.get("ARK_ENDPOINT_ID")
    if ark_key and ark_endpoint:
        from openai import OpenAI

        client = OpenAI(api_key=ark_key, base_url="https://ark.cn-beijing.volces.com/api/v3")
        return client, ark_endpoint

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        from openai import OpenAI

        client = OpenAI(api_key=openai_key)
        return client, "gpt-4o-mini"

    return None, None


def generate_summary(model: BuildingModel, issues: List[Issue]) -> str:
    client, model_name = _build_llm_client()
    if client is None:
        return _fallback_summary(model, issues)

    try:
        system_prompt = (
            "你是一名建筑合规审查助手，请阅读规则引擎输出的问题列表，"
            "生成150-250字的中文总结与整改优先级建议，不要重新判断数值结论。"
        )
        user_prompt = (
            f"项目名称：{model.project}\n"
            "检查规则说明：\n"
            "- R1-EscapeWidth：疏散门/走道净宽度是否满足规范阈值\n"
            "- R2-PropertyCompleteness：门窗类构件的名称/耐火等级等关键属性是否完整\n\n"
            f"检查结果（JSON）：\n{json.dumps([i.model_dump() for i in issues], ensure_ascii=False, indent=2)}\n\n"
            "请根据上述信息生成总结与整改建议。"
        )
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:  # noqa: BLE001
        return _fallback_summary(model, issues) + f"\n（提示：调用 LLM 总结失败，已使用本地模板兜底：{e}）"


def check_model(input_path: str | Path, region: str | None = None, building_type: str | None = None):
    model = load_model(input_path)
    rules = build_rules(region, building_type)
    issues = run_rules(model, rules)
    summary = generate_summary(model, issues)
    return model, issues, summary
