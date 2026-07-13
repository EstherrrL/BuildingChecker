"""生成终端摘要与 HTML 报告。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table

from src.models import Issue, BuildingModel

SEVERITY_COLOR = {"high": "red", "medium": "yellow", "low": "cyan"}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def print_terminal_report(model: BuildingModel, issues: List[Issue], summary: str = "") -> None:
    console = Console()
    console.rule(f"[bold]建筑模型合规检查报告 - {model.project}[/bold]")

    total = len(issues)
    high = sum(1 for i in issues if i.severity == "high")
    medium = sum(1 for i in issues if i.severity == "medium")
    low = sum(1 for i in issues if i.severity == "low")

    console.print(
        f"共发现 [bold]{total}[/bold] 项问题："
        f"[red]高优先级 {high}[/red] / [yellow]中优先级 {medium}[/yellow] / [cyan]低优先级 {low}[/cyan]\n"
    )

    if issues:
        table = Table(show_lines=True)
        table.add_column("规则")
        table.add_column("严重程度")
        table.add_column("构件")
        table.add_column("问题描述")
        table.add_column("建议")

        for issue in sorted(issues, key=lambda i: SEVERITY_ORDER.get(i.severity, 9)):
            color = SEVERITY_COLOR.get(issue.severity, "white")
            table.add_row(
                issue.rule_id,
                f"[{color}]{issue.severity}[/{color}]",
                f"{issue.element_name} ({issue.element_id})",
                issue.message,
                issue.suggestion,
            )
        console.print(table)
    else:
        console.print("[green]未发现问题，模型符合已实现的检查规则。[/green]")

    if summary:
        console.rule("[bold]AI 总结与建议[/bold]")
        console.print(summary)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>建筑模型合规检查报告 - {{ project }}</title>
<style>
  body { font-family: -apple-system, "PingFang SC", Arial, sans-serif; margin: 40px; background: #f7f8fa; color: #222; }
  h1 { font-size: 22px; }
  .summary-cards { display: flex; gap: 16px; margin: 20px 0; }
  .card { flex: 1; padding: 16px; border-radius: 8px; color: white; text-align: center; }
  .card .num { font-size: 28px; font-weight: bold; }
  .card.total { background: #4b5563; }
  .card.high { background: #dc2626; }
  .card.medium { background: #d97706; }
  .card.low { background: #0891b2; }
  table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
  th, td { padding: 10px 12px; border-bottom: 1px solid #eee; text-align: left; font-size: 14px; }
  th { background: #f1f5f9; }
  .sev-high { color: #dc2626; font-weight: bold; }
  .sev-medium { color: #d97706; font-weight: bold; }
  .sev-low { color: #0891b2; font-weight: bold; }
  .ai-summary { background: white; padding: 16px 20px; border-radius: 8px; margin-top: 24px; white-space: pre-wrap; line-height: 1.6; }
  .no-issue { background: #ecfdf5; color: #059669; padding: 16px; border-radius: 8px; }
</style>
</head>
<body>
  <h1>建筑模型合规检查报告 —— {{ project }}</h1>
  <div class="summary-cards">
    <div class="card total"><div class="num">{{ total }}</div>问题总数</div>
    <div class="card high"><div class="num">{{ high }}</div>高优先级</div>
    <div class="card medium"><div class="num">{{ medium }}</div>中优先级</div>
    <div class="card low"><div class="num">{{ low }}</div>低优先级</div>
  </div>

  {% if issues %}
  <table>
    <tr><th>规则</th><th>严重程度</th><th>构件</th><th>问题描述</th><th>建议</th></tr>
    {% for issue in issues %}
    <tr>
      <td>{{ issue.rule_id }}</td>
      <td class="sev-{{ issue.severity }}">{{ issue.severity }}</td>
      <td>{{ issue.element_name }} ({{ issue.element_id }})</td>
      <td>{{ issue.message }}</td>
      <td>{{ issue.suggestion }}</td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <div class="no-issue">未发现问题，模型符合已实现的检查规则。</div>
  {% endif %}

  {% if summary %}
  <h2>AI 总结与建议</h2>
  <div class="ai-summary">{{ summary }}</div>
  {% endif %}
</body>
</html>
"""


def generate_html_report(
    model: BuildingModel, issues: List[Issue], output_path: str | Path, summary: str = ""
) -> Path:
    from jinja2 import Template

    template = Template(HTML_TEMPLATE)
    sorted_issues = sorted(issues, key=lambda i: SEVERITY_ORDER.get(i.severity, 9))
    html = template.render(
        project=model.project,
        issues=sorted_issues,
        total=len(issues),
        high=sum(1 for i in issues if i.severity == "high"),
        medium=sum(1 for i in issues if i.severity == "medium"),
        low=sum(1 for i in issues if i.severity == "low"),
        summary=summary,
    )
    output_path = Path(output_path)
    output_path.write_text(html, encoding="utf-8")
    return output_path
