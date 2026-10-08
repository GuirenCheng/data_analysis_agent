"""数据分析智能体 CLI 入口 — 对任意 CSV/Excel 文件执行自然语言驱动的数据分析。"""

import argparse
import sys

# 修复 Windows 控制台 GBK 编码无法输出 emoji 的问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data_analysis_agent import DataAnalysisAgent
from config.llm_config import LLMConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="数据分析智能体 — 用自然语言描述分析需求，自动生成代码并执行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py -f sales.csv -q "分析近五年营收趋势并生成图表"
  python main.py --file data1.csv --file data2.csv --query "对比两份数据的统计特征"
  python main.py -f data.csv -q "数据清洗和描述性统计" --max-rounds 10 --output-dir ./results
        """,
    )
    parser.add_argument(
        "-f", "--file",
        action="append",
        dest="files",
        required=True,
        help="数据文件路径，可多次指定（支持 CSV / Excel / JSON / Parquet）",
    )
    parser.add_argument(
        "-q", "--query",
        required=True,
        help="自然语言分析需求，例如：'分析销售数据的趋势和异常值'",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=20,
        help="最大分析轮次（默认 20）",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="输出目录（默认 outputs）",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    llm_config = LLMConfig()
    agent = DataAnalysisAgent(llm_config, output_dir=args.output_dir, max_rounds=args.max_rounds)

    report = agent.analyze(user_input=args.query, files=args.files)

    # 输出最终报告路径
    report_path = report.get("report_file_path", "")
    if report_path:
        print(f"\n📄 报告已保存至: {report_path}")

    return report


if __name__ == "__main__":
    main()
