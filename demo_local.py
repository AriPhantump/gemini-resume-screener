#!/usr/bin/env python3
"""
本地简历筛选器演示脚本

这个脚本演示如何使用LocalResumeScreener进行简历筛选
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.local_resume_screener import LocalResumeScreener
from loguru import logger


def demo_resume_screening():
    """演示简历筛选流程"""
    
    print("🚀 本地简历筛选器演示")
    print("=" * 50)
    
    # 检查API密钥
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ 请设置GEMINI_API_KEY环境变量")
        print("   export GEMINI_API_KEY=your_api_key")
        return
    
    # 设置简历文件夹路径
    resume_dirs = [
        "./data",  # 假设简历存放在data目录
        "./resumes",  # 或者resumes目录
    ]
    
    # 过滤存在的目录
    existing_dirs = [d for d in resume_dirs if os.path.exists(d)]
    
    if not existing_dirs:
        print("❌ 没有找到简历文件夹")
        print("   请将简历文件放在以下目录之一:")
        for d in resume_dirs:
            print(f"   - {d}")
        
        # 创建示例目录结构
        print("\n📁 创建示例目录结构...")
        os.makedirs("./resumes", exist_ok=True)
        print("   已创建 ./resumes 目录")
        print("   请将PDF或DOCX简历文件放入该目录")
        return
    
    print(f"📂 使用简历目录: {existing_dirs}")
    
    try:
        # 初始化筛选器
        print("\n🔧 初始化筛选器...")
        screener = LocalResumeScreener(resume_directories=existing_dirs)
        
        # 扫描和处理简历
        print("\n📄 扫描和处理简历文件...")
        stats = screener.scan_and_process_resumes()
        
        print(f"📊 处理结果:")
        print(f"   总文件数: {stats['total']}")
        print(f"   成功处理: {stats['processed']}")
        print(f"   处理失败: {stats['failed']}")
        print(f"   成功率: {stats['success_rate']:.2%}")
        
        if stats['processed'] == 0:
            print("❌ 没有成功处理任何简历文件")
            print("   请检查文件格式是否为PDF或DOCX")
            return
        
        # 演示查询解析
        print("\n🔍 演示查询解析...")
        test_queries = [
            "需要5年以上Python开发经验的后端工程师",
            "招聘前端开发，熟悉React和Vue，本科以上学历",
            "Java后端架构师，8年经验，薪资面议",
        ]
        
        for query in test_queries[:1]:  # 只演示第一个查询
            print(f"\n查询: {query}")
            query_metadata = screener.query_parser.parse_query(query)
            
            print(f"  解析结果:")
            print(f"    关键词: {query_metadata.keywords}")
            print(f"    必需技能: {query_metadata.required_skills}")
            print(f"    最少经验: {query_metadata.min_experience_years}年")
            print(f"    学历要求: {query_metadata.required_education}")
            
            # 执行筛选
            print(f"\n🎯 执行筛选...")
            results = screener.screen_resumes(query, top_k=5)
            
            print(f"筛选结果:")
            print(f"  找到候选人: {results['total_candidates']} 人")
            
            # 显示候选人
            if results['total_candidates'] > 0:
                print(f"\n👥 候选人列表:")
                for i, candidate in enumerate(results['candidates'][:3], 1):
                    name = candidate.get('name', '未知')
                    score = candidate.get('scores', {}).get('overall_score', 0)
                    skills = candidate.get('basic_info', {}).get('skills', [])
                    file_name = candidate.get('file_name', '未知文件')
                    
                    print(f"  {i}. {name} (得分: {score:.2f})")
                    print(f"     技能: {', '.join(skills[:3])}")
                    print(f"     文件: {file_name}")
                    
                    # 显示简要分析
                    analysis = candidate.get('analysis', '')
                    if analysis:
                        analysis_lines = analysis.split('\n')[:2]  # 只显示前两行
                        for line in analysis_lines:
                            if line.strip():
                                print(f"     分析: {line.strip()}")
                                break
                    print()
            else:
                print("   ❌ 没有找到匹配的候选人")
        
        # 显示统计信息
        print("\n📈 处理统计:")
        processing_stats = screener.get_processing_stats()
        print(f"  文件类型分布: {processing_stats['file_types']}")
        print(f"  平均文件大小: {processing_stats['avg_size']:.1f} 字节")
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        print(f"❌ 错误: {e}")


def create_sample_resumes():
    """创建示例简历文件（文本格式，用于测试）"""
    sample_dir = "./resumes"
    os.makedirs(sample_dir, exist_ok=True)
    
    sample_resume = """
张三
高级Python开发工程师

联系方式:
邮箱: zhangsan@example.com
电话: 13800138000
地址: 北京市朝阳区

工作经历:
2020-01 至 2024-01  ABC科技有限公司  高级Python开发工程师
- 负责公司核心业务系统的后端开发
- 使用Python、Django、MySQL等技术栈
- 优化系统性能，提升处理效率50%

2018-06 至 2019-12  DEF互联网公司  Python开发工程师  
- 参与电商平台的开发和维护
- 熟练使用Redis、Docker等技术

教育背景:
2014-09 至 2018-06  清华大学  计算机科学与技术  本科

技能:
Python, Django, Flask, MySQL, Redis, Docker, Git, Linux

项目经历:
电商平台后端系统 (2020-03 至 2020-09)
- 设计和实现了高并发的订单处理系统
- 使用微服务架构，支持日处理订单10万+

个人简介:
具有6年Python开发经验，熟悉Web开发和后端架构设计，
有大型项目经验，能够独立承担核心模块开发。

期望薪资: 25K-35K
期望工作地点: 北京, 上海
"""
    
    # 保存为文本文件（实际使用中应该是PDF或DOCX）
    with open(f"{sample_dir}/张三_Python工程师.txt", "w", encoding="utf-8") as f:
        f.write(sample_resume)
    
    print(f"📝 已创建示例简历: {sample_dir}/张三_Python工程师.txt")
    print("   注意: 实际使用时请使用PDF或DOCX格式的简历")


if __name__ == "__main__":
    # 设置日志
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print("🎯 选择演示模式:")
    print("1. 运行完整演示")
    print("2. 创建示例简历文件")
    
    choice = input("请输入选择 (1 或 2): ").strip()
    
    if choice == "1":
        demo_resume_screening()
    elif choice == "2":
        create_sample_resumes()
    else:
        print("无效选择")