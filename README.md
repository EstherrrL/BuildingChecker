# Building Model Compliance Checker Agent

An intelligent agent that performs basic compliance and reasonableness checks on building design models (IFC / simplified JSON).

---

## Implemented Rules

1. **R1-EscapeWidth**: Escape door / corridor clear-width check. Thresholds are configurable per (region, building type) via `data/thresholds.json` (see `--region` / `--building-type` CLI flags and the sidebar selector in the Streamlit app); default is door ≥ 0.9m, corridor ≥ 1.2m. Values are illustrative examples, not authoritative — real projects must verify against the local fire code in force.
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

- Thresholds in `data/thresholds.json` are illustrative examples for a handful of (region, building type) combinations, not authoritative values; real projects must determine them from local codes, building type, and occupant-load calculations. We deliberately used a structured lookup table (not a vector DB / RAG) for this, since it's an exact key-value lookup problem where a similarity-search-based approach risks returning a plausible-but-wrong threshold.
- Geometric clash detection (walls/beams/pipes) is not implemented, as it is computationally heavier; left as future work.
- IFC corridor parsing uses a simplified heuristic (identifying `IfcSpace` by name keywords); production use should customize the logic per the project's BIM modeling standard.
- Rules are currently hard-coded; a future extension could move them into configurable YAML/JSON rule files so rules can be added/removed without code changes.
- Not using LangChain/LangGraph for now, since the current flow is a single-pass, deterministic pipeline (rules → LLM summary) with no multi-step reasoning. These frameworks would be worth introducing if we add multi-turn Q&A, RAG over real code documents, or multi-agent orchestration.
- **On "is this really an agent?"**: strictly speaking, this project has no autonomous tool-calling — the two rules always run unconditionally (deliberately, since under-checking is far more costly than over-checking in a compliance context), and the LLM is only invoked once, to write a natural-language summary of already-finalized, deterministic results. We explored giving the LLM decision-making power (e.g., "let the LLM decide which rules to run", or "let the LLM decide whether to invoke an extra tool based on severity"), but rejected both: the first would reduce checking coverage for no real benefit, and the second turned out to be a decision fully determined by already-structured data (i.e., a disguised if-statement, not genuine judgment). We'd rather be upfront about this than dress up an if-else chain as "agentic". A defensible way to add real autonomy later would be tool-calling over genuinely ambiguous, cross-rule semantic reasoning (e.g., "do these two independent findings on the same element indicate one underlying root cause?") — but we judged the added complexity wasn't justified for this submission's scope.

---
---

# 建筑模型合规检查 Agent

一个用于对建筑设计模型（IFC / 简化 JSON）进行基础合规与合理性检查的智能 Agent。

---

## 已实现的检查规则

1. **R1-EscapeWidth**：疏散门 / 疏散走道净宽度检查。阈值支持按 (地区, 建筑类型) 从 `data/thresholds.json` 中动态查询（对应 CLI 的 `--region` / `--building-type` 参数，或 Streamlit 界面侧边栏的下拉选择器），默认值为门 ≥ 0.9m、走道 ≥ 1.2m。这些数值仅为示例，不具备权威性，实际项目应以当地现行消防规范核实。
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

- `data/thresholds.json` 中的阈值仅是几组 (地区, 建筑类型) 组合的示例数据，不具备权威性，实际项目需按当地规范、建筑类型、疏散人数计算确定。这里刻意选择"结构化查表"而非向量数据库/RAG检索，因为这是可精确匹配的键值查找问题，检索式方案存在"语义相近但适用条件不同"从而返回错误阈值的风险。
- 未实现几何碰撞检测（墙/梁/管道），该功能计算复杂度较高，作为后续扩展方向。
- IFC 走道解析为简化启发式处理（通过名称关键字识别 `IfcSpace`），生产环境建议按项目 BIM 建模规范定制识别逻辑。
- 规则目前硬编码在代码中，后续可扩展为可配置的 YAML/JSON 规则文件，无需改代码即可增删规则。
- 暂未使用 LangChain/LangGraph：当前流程是单次线性调用（规则判断 → LLM 总结），无需多步推理。若后续支持多轮追问、检索真实规范条文（RAG）或多智能体协作，再引入会更合适。
- **关于"这算不算真正的 Agent"**：严格来说，本项目没有自主工具调用能力——两条规则始终无条件全部执行（这是刻意设计，因为在合规检查场景下"漏检"的代价远高于"多检查一点"），LLM 仅在最后被调用一次，为已经确定的结构化结果生成自然语言总结。我们也评估过赋予 LLM 决策权的方案（例如"让 LLM 自主决定跑哪些规则"，或"让 LLM 根据严重程度决定是否调用增强工具"），但都被否决了：前者会在没有实质收益的情况下降低检查覆盖率；后者的决策依据其实是已经结构化好的字段（严重程度），本质上是一个可以用 if 语句完成的判断，并不是真正需要语言理解能力的判断，属于"伪装成智能体"的功能。我们认为坦诚说明这一点，比把 if-else 包装成"agentic"更有价值。未来若要引入真正站得住脚的自主性，一个合理方向是：针对"同一构件被多条规则命中时，这些发现是否指向同一个根因"这类需要语义综合判断（而非查表）的场景做工具调用——但经评估，这超出了本次提交的合理范围，故未实现。
