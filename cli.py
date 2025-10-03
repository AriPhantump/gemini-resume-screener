#!/usr/bin/env python3
"""
本地简历筛选器命令行接口

使用示例:
python cli.py scan /path/to/resumes
python cli.py query "需要5年以上Python经验的后端工程师"
python cli.py screen /path/to/resumes "Python后端工程师，3年经验" --top_k 5
"""

import argparse
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.local_resume_screener import LocalResumeScreener


def setup_logging(level: str = "INFO"):
    """设置日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )


def scan_command(args):
    """扫描简历文件"""
    print(f"🔍 扫描简历文件夹: {args.directories}")
    
    screener = LocalResumeScreener(
        resume_directories=args.directories,
        gemini_api_key=args.gemini_api_key
    )
    
    stats = screener.scan_and_process_resumes(args.directories, args.recursive)
    
    print(f"\n📊 扫描结果:")
    print(f"  总文件数: {stats['total']}")
    print(f"  成功处理: {stats['processed']}")
    print(f"  处理失败: {stats['failed']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    
    if args.export:
        export_stats(stats, args.export)


def query_command(args):
    """解析查询"""
    print(f"🔍 解析查询: {args.query}")
    
    screener = LocalResumeScreener(gemini_api_key=args.gemini_api_key)
    query_metadata = screener.query_parser.parse_query(args.query)
    
    print(f"\n📋 解析结果:")
    print(f"  关键词: {query_metadata.keywords}")
    print(f"  必需技能: {query_metadata.required_skills}")
    print(f"  优先技能: {query_metadata.preferred_skills}")
    print(f"  最少经验: {query_metadata.min_experience_years}年")
    print(f"  学历要求: {query_metadata.required_education}")
    print(f"  薪资范围: {query_metadata.salary_range}")
    print(f"  工作地点: {query_metadata.locations}")
    
    if args.export:
        export_query_metadata(query_metadata, args.export)


def screen_command(args):
    """筛选简历"""
    print(f"🎯 开始筛选简历...")
    print(f"  简历文件夹: {args.directories}")
    print(f"  查询条件: {args.query}")
    print(f"  返回数量: {args.top_k}")
    
    screener = LocalResumeScreener(
        resume_directories=args.directories,
        gemini_api_key=args.gemini_api_key
    )
    
    # 先扫描处理简历
    if not args.skip_scan:
        print("\n📂 扫描简历文件...")
        scan_stats = screener.scan_and_process_resumes(args.directories, args.recursive)
        print(f"  处理了 {scan_stats['processed']} 份简历")
    
    # 执行筛选
    print(f"\n🔍 执行筛选...")
    results = screener.screen_resumes(args.query, args.top_k)
    
    # 显示结果
    print_screening_results(results)
    
    # 导出结果
    if args.export:
        export_path = args.export
        if not export_path.endswith('.json'):
            export_path += '.json'
        screener.export_results(results, export_path, 'json')
        print(f"\n💾 结果已导出到: {export_path}")


def print_screening_results(results):
    """打印筛选结果"""
    print(f"\n🎉 筛选完成!")
    print(f"  查询: {results['query']}")
    print(f"  找到候选人: {results['total_candidates']} 人")
    
    if results['total_candidates'] == 0:
        print("  ❌ 没有找到匹配的候选人")
        return
    
    print(f"\n👥 候选人列表:")
    print("-" * 80)
    
    for i, candidate in enumerate(results['candidates'][:10], 1):  # 只显示前10个
        print(f"\n{i}. {candidate.get('name', '未知姓名')} (排名: {candidate.get('rank', 'N/A')})")
        print(f"   📧 邮箱: {candidate.get('contact_info', {}).get('email', '未知')}")
        print(f"   📱 电话: {candidate.get('contact_info', {}).get('phone', '未知')}")
        print(f"   🎯 综合得分: {candidate.get('scores', {}).get('overall_score', 0):.2f}")
        print(f"   💼 技能: {', '.join(candidate.get('basic_info', {}).get('skills', [])[:5])}")
        print(f"   💰 期望薪资: {candidate.get('basic_info', {}).get('expected_salary', '未知')}")
        print(f"   📍 期望地点: {', '.join(candidate.get('basic_info', {}).get('preferred_locations', []))}")
        
        if candidate.get('file_path'):
            print(f"   📄 文件: {candidate['file_path']}")
        
        # 显示分析摘要（前200字符）
        analysis = candidate.get('analysis', '')
        if analysis:
            analysis_preview = analysis[:200] + "..." if len(analysis) > 200 else analysis
            print(f"   📝 分析: {analysis_preview}")


def export_stats(stats, export_path):
    """导出统计信息"""
    if not export_path.endswith('.json'):
        export_path += '.json'
    
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"📊 统计信息已导出到: {export_path}")


def export_query_metadata(query_metadata, export_path):
    """导出查询元数据"""
    if not export_path.endswith('.json'):
        export_path += '.json'
    
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(query_metadata.dict(), f, ensure_ascii=False, indent=2)
    
    print(f"📋 查询解析结果已导出到: {export_path}")


def main():
    parser = argparse.ArgumentParser(description="本地简历筛选器")
    parser.add_argument("--gemini-api-key", type=str, help="Gemini API密钥")
    parser.add_argument("--log-level", type=str, default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="日志级别")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # scan 命令
    scan_parser = subparsers.add_parser("scan", help="扫描简历文件")
    scan_parser.add_argument("directories", nargs="+", help="简历文件夹路径")
    scan_parser.add_argument("--recursive", action="store_true", default=True,
                           help="递归扫描子目录")
    scan_parser.add_argument("--export", type=str, help="导出统计信息到文件")
    
    # query 命令
    query_parser = subparsers.add_parser("query", help="解析查询条件")
    query_parser.add_argument("query", type=str, help="自然语言查询")
    query_parser.add_argument("--export", type=str, help="导出解析结果到文件")
    
    # screen 命令
    screen_parser = subparsers.add_parser("screen", help="筛选简历")
    screen_parser.add_argument("directories", nargs="+", help="简历文件夹路径")
    screen_parser.add_argument("query", type=str, help="筛选条件")
    screen_parser.add_argument("--top-k", type=int, default=10, help="返回候选人数量")
    screen_parser.add_argument("--recursive", action="store_true", default=True,
                             help="递归扫描子目录")
    screen_parser.add_argument("--skip-scan", action="store_true",
                             help="跳过文件扫描（假设已经处理过）")
    screen_parser.add_argument("--export", type=str, help="导出结果到文件")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 检查Gemini API密钥
    if not args.gemini_api_key and not os.getenv("GEMINI_API_KEY"):
        print("❌ 错误: 请设置GEMINI_API_KEY环境变量或使用--gemini-api-key参数")
        sys.exit(1)
    
    # 执行命令
    if args.command == "scan":
        scan_command(args)
    elif args.command == "query":
        query_command(args)
    elif args.command == "screen":
        screen_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()