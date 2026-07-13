# Building Model Compliance Checker Agent

An intelligent agent that performs basic compliance and reasonableness checks on building design models (IFC / simplified JSON).

---

## Implemented Rules

1. **R1-EscapeWidth**: Escape door / corridor clear-width check (example thresholds: door ≥ 0.9m, corridor ≥ 1.2m; actual thresholds should follow the local fire code in force for the project).
2. **R2-PropertyCompleteness**: Key-property completeness check for door/window elements (empty name, missing FireRating on escape/fire doors).

The rule engine produces deterministic numeric judgments; the agent then calls an LLM (falling back to a local template if `OPENAI_API_KEY` is not set) to generate a natural-language summary and remediation priorities, avoiding LLM hallucination on the numeric verdicts themselves.

---

## Quick Start

```bash
# A virtual environment is recommended
pip install -r requirements.txt

# Check the constructed "problematic model" (terminal output + generate HTML report)
python check.py --input data/sample_model.json --html report.html

# Check the "fully compliant" model (verify no false positives)
python check.py --input data/sample_model_compliant.json
```

To enable LLM-based summarization, set the environment variable before running:

```bash
export OPENAI_API_KEY=sk-xxxx
python check.py --input data/sample_model.json
```

---

## Running Unit Tests

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
prompts/                   Prompt for LLM summarization
data/                      Test data (violation & compliant cases)
src/models.py               Unified data model
src/parsers/                JSON & IFC parsers
src/rules/                  Rule engine (2 rules)
src/agent.py                 Main pipeline orchestration
src/report.py                Terminal & HTML report generation
check.py                    CLI entry point
tests/                      Unit tests
```

---

## Input Data Format

Two input formats are supported:

1. **Simplified JSON model** (see `data/sample_model.json`); field meanings are defined in `src/models.py`.
2. **Real IFC files** (`.ifc`), parsed via `ifcopenshell` (requires an extra `pip install ifcopenshell`). See the header comment of `src/parsers/ifc_parser.py` for the field mapping.

Both input types are converted into a unified `BuildingModel`; the rule engine is agnostic to the original data format.

---

## Limitations & Future Work

- Thresholds are illustrative only; real projects must determine them from local codes, building type, and occupant-load calculations.
- Geometric clash detection (walls/beams/pipes) is not implemented, as it is computationally heavier; left as future work.
- IFC corridor parsing uses a simplified heuristic (identifying `IfcSpace` by name keywords); production use should customize the logic per the project's BIM modeling standard.
- Rules are currently hard-coded; a future extension could move them into configurable YAML/JSON rule files so rules can be added/removed without code changes.

---
---

# 建筑模型合规检查 Agent

一个用于对建筑设计模型（IFC / 简化 JSON）进行基础合规与合理性检查的智能 Agent。

---

## 已实现的检查规则

1. **R1-EscapeWidth**：疏散门 / 疏散走道净宽度检查（示例阈值：门 ≥ 0.9m，走道 ≥ 1.2m，实际应按项目所在地现行消防规范核实）。
2. **R2-PropertyCompleteness**：门窗类构件关键属性完整性检查（名称是否为空、疏散门/防火门是否缺少 FireRating 耐火等级）。

规则引擎给出确定性的数值判断，Agent 再调用 LLM（若配置了 `OPENAI_API_KEY`，否则使用本地模板兜底）对结果做自然语言总结与整改优先级建议，避免 LLM 直接产生数值幻觉。

---

## 快速开始

```bash
# 建议使用虚拟环境
pip install -r requirements.txt

# 对构造的"问题模型"进行检查（终端输出 + 生成 HTML 报告）
python check.py --input data/sample_model.json --html report.html

# 对"全部合规"的模型进行检查（验证无误报）
python check.py --input data/sample_model_compliant.json
```

如需接入 LLM 总结，设置环境变量后再运行：

```bash
export OPENAI_API_KEY=sk-xxxx
python check.py --input data/sample_model.json
```

---

## 运行单元测试

```bash
python -m pytest tests/ -v
```

---

## 目录结构

```
prompts/                   LLM 总结用的 Prompt
data/                      测试数据（含违规案例与合规案例）
src/models.py               统一数据模型
src/parsers/                JSON / IFC 解析器
src/rules/                  规则引擎（2 条规则）
src/agent.py                 主流程编排
src/report.py                终端 & HTML 报告生成
check.py                    CLI 入口
tests/                      单元测试
```

---

## 输入数据格式

支持两种输入：

1. **简化 JSON 模型**（见 `data/sample_model.json`），字段含义见 `src/models.py`。
2. **真实 IFC 文件**（`.ifc`），通过 `ifcopenshell` 解析（需要额外 `pip install ifcopenshell`）。字段映射见 `src/parsers/ifc_parser.py` 顶部注释。

两种输入最终都会转换为统一的 `BuildingModel`，规则引擎不关心原始数据格式。

---

## 局限性与后续可扩展方向

- 阈值为示例性质，实际项目需按当地规范、建筑类型、疏散人数计算确定。
- 未实现几何碰撞检测（墙/梁/管道），该功能计算复杂度较高，作为后续扩展方向。
- IFC 走道解析为简化启发式处理（通过名称关键字识别 `IfcSpace`），生产环境建议按项目 BIM 建模规范定制识别逻辑。
- 规则目前硬编码在代码中，后续可扩展为可配置的 YAML/JSON 规则文件，无需改代码即可增删规则。
