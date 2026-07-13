"""
Agent 主流程：解析模型 -> 运行规则 -> (可选) LLM 总结 -> 返回结果。

LLM 总结部分做成可插拔：
  - 若环境变量 OPENAI_API_KEY 存在，则调用 OpenAI 接口生成自然语言总结；
  - 否则使用本地的简单模板生成"伪总结"（保证 Demo 在无网络/无 API Key 时也能完整跑通）。
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

DEFAULT_RULES = [EscapeWidthRule(), PropertyCompletenessRule()]


def load_model(input_path: str | Path) -> BuildingModel:
    input_path = Path(input_path)
    if input_path.suffix.lower() == ".ifc":
        from src.parsers.ifc_parser import parse_ifc_model

        return parse_ifc_model(input_path)
    return parse_json_model(input_path)


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


def generate_summary(model: BuildingModel, issues: List[Issue]) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return _fallback_summary(model, issues)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "report_summary_prompt.md"
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:  # noqa: BLE001
        return _fallback_summary(model, issues) + f"\n（提示：调用 LLM 总结失败，已使用本地模板兜底：{e}）"


def check_model(input_path: str | Path):
    model = load_model(input_path)
    issues = run_rules(model)
    summary = generate_summary(model, issues)
    return model, issues, summary
