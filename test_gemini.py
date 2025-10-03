#!/usr/bin/env python3
"""
简单测试脚本，验证Gemini集成是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.gemini_client import GeminiClient
from app.core.gemini_query_parser import GeminiQueryParser
from app.core.gemini_extractor import GeminiMetadataExtractor


def test_gemini_connection():
    """测试Gemini连接"""
    print("🔗 测试Gemini连接...")
    
    try:
        client = GeminiClient()
        response = client.generate_text("请回答：1+1等于几？")
        print(f"✅ Gemini连接成功")
        print(f"   回应: {response}")
        return True
    except Exception as e:
        print(f"❌ Gemini连接失败: {e}")
        return False


def test_query_parsing():
    """测试查询解析"""
    print("\n🔍 测试查询解析...")
    
    try:
        client = GeminiClient()
        parser = GeminiQueryParser(client)
        
        test_query = "需要5年以上Python经验的后端工程师，本科学历，薪资20-30K"
        metadata = parser.parse_query(test_query)
        
        print(f"✅ 查询解析成功")
        print(f"   原查询: {test_query}")
        print(f"   关键词: {metadata.keywords}")
        print(f"   必需技能: {metadata.required_skills}")
        print(f"   经验要求: {metadata.min_experience_years}年")
        print(f"   学历要求: {metadata.required_education}")
        print(f"   薪资范围: {metadata.salary_range}")
        return True
    except Exception as e:
        print(f"❌ 查询解析失败: {e}")
        return False


def test_metadata_extraction():
    """测试元数据提取"""
    print("\n📄 测试元数据提取...")
    
    sample_resume = """
张三
高级Python开发工程师

联系方式：
邮箱: zhangsan@example.com
电话: 13800138000

工作经历：
2020-01 至 2024-01  ABC科技有限公司  高级Python开发工程师
- 负责后端系统开发
- 使用Python、Django、MySQL

教育背景：
2016-09 至 2020-06  清华大学  计算机科学与技术  本科

技能：
Python, Django, MySQL, Redis, Docker

期望薪资: 25K-35K
期望工作地点: 北京, 上海
"""
    
    try:
        client = GeminiClient()
        extractor = GeminiMetadataExtractor(client)
        
        metadata = extractor.extract_metadata(sample_resume)
        
        print(f"✅ 元数据提取成功")
        print(f"   姓名: {metadata.name}")
        print(f"   邮箱: {metadata.email}")
        print(f"   技能: {metadata.skills}")
        print(f"   工作经历数量: {len(metadata.work_experience)}")
        print(f"   教育背景数量: {len(metadata.education)}")
        print(f"   期望薪资: {metadata.expected_salary}")
        return True
    except Exception as e:
        print(f"❌ 元数据提取失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("🧪 Gemini集成测试")
    print("=" * 50)
    
    # 检查API密钥
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ 请设置GEMINI_API_KEY环境变量")
        print("   export GEMINI_API_KEY=your_api_key")
        return
    
    tests = [
        test_gemini_connection,
        test_query_parsing,
        test_metadata_extraction
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常使用。")
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接。")


if __name__ == "__main__":
    main()