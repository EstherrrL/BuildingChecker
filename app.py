"""
Streamlit 交互式 Web 前端：建筑模型合规检查 Agent

运行方式：
    streamlit run app.py

功能：
  - 上传 / 选择示例模型文件（.json 或 .ifc）
  - 一键运行检查
  - 实时展示：统计卡片、违规明细表、AI 总结
  - 可下载 HTML 报告
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

from src.agent import load_model, run_rules, generate_summary, build_rules
from src.report import HTML_TEMPLATE
from src.thresholds import load_thresholds, list_regions, list_building_types, get_thresholds

ROOT = Path(__file__).resolve().parent
SAMPLE_FILES = {
    "示例1：含违规问题的模型 (sample_model.json)": ROOT / "data" / "sample_model.json",
    "示例2：完全合规的模型 (sample_model_compliant.json)": ROOT / "data" / "sample_model_compliant.json",
}

st.set_page_config(page_title="建筑合规检查 Agent", layout="wide")

st.title("建筑合规检查 Agent")
st.caption("对建筑设计模型（IFC / 简化 JSON）进行疏散宽度与关键属性完整性检查")

# ---------------- 侧边栏：LLM 配置状态 + 地区/建筑类型阈值 ----------------
with st.sidebar:
    st.header("设置")

    has_ark = bool(os.environ.get("ARK_API_KEY") and os.environ.get("ARK_ENDPOINT_ID"))
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))

    if has_ark:
        st.success("已检测到火山方舟 (Ark) API Key，AI 总结将由豆包模型生成")
    elif has_openai:
        st.success("已检测到 OpenAI API Key，AI 总结将由 GPT 生成")
    else:
        st.info("未检测到 API Key，AI 总结将使用本地模板兜底（仍可完整运行）")

    st.divider()
    st.subheader("已实现规则")
    st.markdown(
        "- **R1-EscapeWidth**：疏散门 / 疏散走道净宽度检查\n"
        "- **R2-PropertyCompleteness**：名称 / 防火门 FireRating 是否填写"
    )

    st.divider()
    st.subheader("疏散宽度阈值（按地区/建筑类型）")
    st.caption("阈值来自 data/thresholds.json，示例数据，非官方权威数值，实际请以当地现行规范为准。")

    thresholds_data = load_thresholds()
    region_options = list_regions(thresholds_data)
    region_labels = [f"{label} ({code})" for code, label in region_options]
    region_idx = st.selectbox("地区", range(len(region_options)), format_func=lambda i: region_labels[i])
    selected_region = region_options[region_idx][0]

    type_options = list_building_types(selected_region, thresholds_data)
    type_labels = [f"{label} ({code})" for code, label in type_options]
    type_idx = st.selectbox("建筑类型", range(len(type_options)), format_func=lambda i: type_labels[i])
    selected_building_type = type_options[type_idx][0]

    current_thresholds = get_thresholds(selected_region, selected_building_type, thresholds_data)
    st.markdown(
        f"- 疏散门净宽 ≥ **{current_thresholds['door_min_width']:.2f}m**\n"
        f"- 疏散走道净宽 ≥ **{current_thresholds['corridor_min_width']:.2f}m**\n"
        f"- 参考依据：{current_thresholds['reference_code']}"
    )

# ---------------- 主区域：选择/上传模型 ----------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1. 选择模型文件")
    mode = st.radio("输入方式", ["使用示例模型", "上传自己的模型文件"], horizontal=True)

    input_path = None
    if mode == "使用示例模型":
        choice = st.selectbox("选择示例", list(SAMPLE_FILES.keys()))
        input_path = SAMPLE_FILES[choice]
        st.code(input_path.read_text(encoding="utf-8"), language="json", line_numbers=True)
    else:
        uploaded = st.file_uploader("上传 .json 或 .ifc 文件", type=["json", "ifc"])
        if uploaded is not None:
            suffix = Path(uploaded.name).suffix
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(uploaded.read())
            tmp.close()
            input_path = Path(tmp.name)

    run_btn = st.button("运行检查", type="primary", use_container_width=True, disabled=input_path is None)

with col_right:
    st.subheader("2. 检查结果")

    if run_btn and input_path is not None:
        with st.spinner("正在解析模型并运行规则检查..."):
            model = load_model(input_path)
            rules = build_rules(selected_region, selected_building_type)
            issues = run_rules(model, rules)

        st.caption(
            f"本次使用阈值：地区={selected_region}，建筑类型={selected_building_type}，"
            f"疏散门≥{current_thresholds['door_min_width']:.2f}m，"
            f"疏散走道≥{current_thresholds['corridor_min_width']:.2f}m"
        )

        total = len(issues)
        high = sum(1 for i in issues if i.severity == "high")
        medium = sum(1 for i in issues if i.severity == "medium")
        low = sum(1 for i in issues if i.severity == "low")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("问题总数", total)
        c2.metric("高优先级", high, delta=None)
        c3.metric("中优先级", medium)
        c4.metric("低优先级", low)

        if issues:
            table_rows = [
                {
                    "严重程度": i.severity,
                    "规则": i.rule_id,
                    "构件": f"{i.element_name} ({i.element_id})",
                    "问题描述": i.message,
                    "建议": i.suggestion,
                }
                for i in sorted(issues, key=lambda i: {"high": 0, "medium": 1, "low": 2}.get(i.severity, 9))
            ]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
        else:
            st.success("未发现问题，模型符合已实现的检查规则。")

        with st.spinner("正在生成 AI 总结（若未配置 API Key 将使用本地模板）..."):
            summary = generate_summary(model, issues)

        st.subheader("AI 总结与整改建议")
        st.markdown(summary)

        # 生成可下载的 HTML 报告
        from jinja2 import Template

        template = Template(HTML_TEMPLATE)
        sorted_issues = sorted(issues, key=lambda i: {"high": 0, "medium": 1, "low": 2}.get(i.severity, 9))
        html = template.render(
            project=model.project,
            issues=sorted_issues,
            total=total,
            high=high,
            medium=medium,
            low=low,
            summary=summary,
        )
        st.download_button(
            "下载 HTML 报告",
            data=html,
            file_name="compliance_report.html",
            mime="text/html",
            use_container_width=True,
        )
    else:
        st.info("请先在左侧选择模型文件，然后点击「运行检查」。")
