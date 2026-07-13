#!/usr/bin/env python3
"""
CLI 入口：建筑模型合规检查 Agent

用法：
    python check.py --input data/sample_model.json
    python check.py --input data/sample_model.json --html report.html
    python check.py --input data/sample.ifc
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.agent import check_model
from src.report import print_terminal_report, generate_html_report


def main():
    parser = argparse.ArgumentParser(description="建筑模型合规与合理性检查 Agent")
    parser.add_argument("--input", "-i", required=True, help="输入模型文件路径 (.json 或 .ifc)")
    parser.add_argument("--html", "-o", default=None, help="输出 HTML 报告的路径（可选）")
    args = parser.parse_args()

    model, issues, summary = check_model(args.input)

    print_terminal_report(model, issues, summary)

    if args.html:
        out = generate_html_report(model, issues, args.html, summary)
        print(f"\nHTML 报告已生成：{out.resolve()}")


if __name__ == "__main__":
    main()
