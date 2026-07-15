#!/usr/bin/env python3
"""
CLI 入口：建筑模型合规检查 Agent

用法：
    python check.py --input data/sample_model.json
    python check.py --input data/sample_model.json --html report.html
    python check.py --input data/sample.ifc
    python check.py --input data/sample_model.json --region US --building-type hospital
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
    parser.add_argument("--region", default=None, help="地区代码，如 CN / US（不填则用默认阈值）")
    parser.add_argument(
        "--building-type", default=None, help="建筑类型代码，如 office / hospital / residential_high_rise"
    )
    args = parser.parse_args()

    model, issues, summary = check_model(args.input, region=args.region, building_type=args.building_type)

    print_terminal_report(model, issues, summary)

    if args.html:
        out = generate_html_report(model, issues, args.html, summary)
        print(f"\nHTML 报告已生成：{out.resolve()}")


if __name__ == "__main__":
    main()
