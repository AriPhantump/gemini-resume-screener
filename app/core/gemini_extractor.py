from typing import Dict, Any, List, Optional
from app.core.gemini_client import GeminiClient
from app.core.cache_manager import CacheManager
from app.models.metadata import ResumeMetadata
from loguru import logger
import json
import hashlib


class GeminiMetadataExtractor:
    """
    基于Gemini的元数据提取器
    """
    
    def __init__(self, gemini_client: GeminiClient, cache_manager: Optional[CacheManager] = None):
        """
        初始化元数据提取器
        
        Args:
            gemini_client (GeminiClient): Gemini客户端实例
            cache_manager (CacheManager, optional): 缓存管理器实例
        """
        self.gemini_client = gemini_client
        self.cache_manager = cache_manager
        logger.info("Initialized GeminiMetadataExtractor")

    def extract_metadata(self, resume_text: str) -> ResumeMetadata:
        """
        从简历文本中提取元数据
        
        Args:
            resume_text (str): 简历文本内容
            
        Returns:
            ResumeMetadata: 提取的元数据对象
            
        Raises:
            ValueError: 如果解析的JSON格式无效
            Exception: 如果提取过程失败
        """
        try:
            # 生成简历文本的哈希值作为缓存键
            cache_key = f"gemini_metadata_{hashlib.md5(resume_text.encode()).hexdigest()}"
            
            # 尝试从缓存中获取结果
            if self.cache_manager:
                cached_result = self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Retrieved metadata from cache for key: {cache_key}")
                    return ResumeMetadata(**cached_result)
            
            # 构造提示词
            prompt = self._create_extraction_prompt(resume_text)
            
            # 使用Gemini生成提取结果
            response = self.gemini_client.generate_text(prompt)
            
            # 解析响应为JSON
            metadata_dict = self._parse_response(response)
            
            # 验证和清理数据
            metadata_dict = self._validate_and_clean_metadata(metadata_dict)
            
            # 创建ResumeMetadata对象
            metadata = ResumeMetadata(**metadata_dict)
            
            # 将结果存入缓存
            if self.cache_manager:
                self.cache_manager.set(cache_key, metadata_dict, expire=3600)  # 缓存1小时
                logger.info(f"Cached metadata for key: {cache_key}")
            
            logger.info(f"Extracted metadata for candidate: {metadata.name}")
            return metadata
            
        except ValueError as e:
            logger.error(f"Invalid JSON format in Gemini response: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            raise Exception(f"Failed to extract metadata: {e}")

    def _create_extraction_prompt(self, resume_text: str) -> str:
        """
        创建元数据提取提示词
        
        Args:
            resume_text (str): 简历文本内容
            
        Returns:
            str: 构造的提示词
        """
        prompt = f"""
你是一位专业的HR助手，擅长从简历中提取结构化信息。请仔细分析以下简历文本，并提取关键信息。

简历文本:
{resume_text}

请从简历中提取以下字段，并以JSON格式返回结果：

1. name: 姓名（必填）
2. email: 邮箱地址
3. phone: 电话号码
4. address: 地址
5. work_experience: 工作经历列表，每个项目包含：
   - company: 公司名称
   - title: 职位
   - start_date: 开始时间（格式：YYYY-MM 或 YYYY）
   - end_date: 结束时间（格式：YYYY-MM 或 YYYY，如果是当前工作填"至今"）
   - description: 工作描述
6. education: 教育背景列表，每个项目包含：
   - institution: 学校名称
   - major: 专业
   - degree: 学位（如：本科、硕士、博士、大专）
   - start_date: 开始时间
   - end_date: 结束时间
7. skills: 技能列表（提取技术技能、编程语言、工具等）
8. projects: 项目经历列表，每个项目包含：
   - name: 项目名称
   - description: 项目描述
   - period: 项目时间
9. languages: 语言能力列表
10. certifications: 证书列表
11. expected_salary: 期望薪资
12. preferred_locations: 期望工作地点列表
13. summary: 个人简介/自我评价
14. additional_info: 其他信息

注意事项：
- 如果某个字段在简历中没有明确信息，请设为null或空列表[]
- 时间格式尽量统一为YYYY-MM格式
- 技能要具体，避免过于泛泛的描述
- 工作经历和教育背景按时间倒序排列

请严格按照以下JSON格式返回结果，不要包含任何其他文本：

{{
  "name": "姓名",
  "email": "邮箱@example.com",
  "phone": "手机号码",
  "address": "地址",
  "work_experience": [
    {{
      "company": "公司名称",
      "title": "职位名称",
      "start_date": "2020-01",
      "end_date": "2023-12",
      "description": "工作职责和成就"
    }}
  ],
  "education": [
    {{
      "institution": "学校名称",
      "major": "专业名称",
      "degree": "学历",
      "start_date": "2016-09",
      "end_date": "2020-06"
    }}
  ],
  "skills": ["技能1", "技能2", "技能3"],
  "projects": [
    {{
      "name": "项目名称",
      "description": "项目描述",
      "period": "2022-01 至 2022-06"
    }}
  ],
  "languages": ["中文", "英语"],
  "certifications": ["证书名称"],
  "expected_salary": "薪资期望",
  "preferred_locations": ["期望城市"],
  "summary": "个人简介",
  "additional_info": "其他信息"
}}
"""
        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析Gemini响应
        
        Args:
            response (str): Gemini生成的响应
            
        Returns:
            Dict[str, Any]: 解析后的元数据字典
            
        Raises:
            ValueError: 如果响应不是有效的JSON格式
        """
        try:
            # 使用Gemini客户端的JSON提取方法
            return self.gemini_client.extract_json_from_response(response)
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise ValueError(f"Failed to parse response as JSON: {response}")

    def _validate_and_clean_metadata(self, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和清理元数据
        
        Args:
            metadata_dict (Dict[str, Any]): 原始元数据字典
            
        Returns:
            Dict[str, Any]: 清理后的元数据字典
        """
        # 确保必填字段存在
        if not metadata_dict.get('name'):
            metadata_dict['name'] = '未知姓名'
        
        # 确保列表字段是列表类型
        list_fields = ['work_experience', 'education', 'skills', 'projects', 
                      'languages', 'certifications', 'preferred_locations']
        
        for field in list_fields:
            if field not in metadata_dict or metadata_dict[field] is None:
                metadata_dict[field] = []
            elif not isinstance(metadata_dict[field], list):
                # 如果不是列表，尝试转换
                if isinstance(metadata_dict[field], str):
                    metadata_dict[field] = [metadata_dict[field]]
                else:
                    metadata_dict[field] = []
        
        # 确保字符串字段不是None
        string_fields = ['email', 'phone', 'address', 'expected_salary', 'summary', 'additional_info']
        for field in string_fields:
            if metadata_dict.get(field) is None:
                metadata_dict[field] = None
        
        # 验证工作经历格式
        if metadata_dict.get('work_experience'):
            validated_work_exp = []
            for exp in metadata_dict['work_experience']:
                if isinstance(exp, dict):
                    validated_exp = {
                        'company': str(exp.get('company', '')),
                        'title': str(exp.get('title', '')),
                        'start_date': str(exp.get('start_date', '')),
                        'end_date': str(exp.get('end_date', '')),
                        'description': str(exp.get('description', ''))
                    }
                    validated_work_exp.append(validated_exp)
            metadata_dict['work_experience'] = validated_work_exp
        
        # 验证教育背景格式
        if metadata_dict.get('education'):
            validated_education = []
            for edu in metadata_dict['education']:
                if isinstance(edu, dict):
                    validated_edu = {
                        'institution': str(edu.get('institution', '')),
                        'major': str(edu.get('major', '')),
                        'degree': str(edu.get('degree', '')),
                        'start_date': str(edu.get('start_date', '')),
                        'end_date': str(edu.get('end_date', ''))
                    }
                    validated_education.append(validated_edu)
            metadata_dict['education'] = validated_education
        
        # 验证项目经历格式
        if metadata_dict.get('projects'):
            validated_projects = []
            for proj in metadata_dict['projects']:
                if isinstance(proj, dict):
                    validated_proj = {
                        'name': str(proj.get('name', '')),
                        'description': str(proj.get('description', '')),
                        'period': str(proj.get('period', ''))
                    }
                    validated_projects.append(validated_proj)
            metadata_dict['projects'] = validated_projects
        
        return metadata_dict

    def extract_batch_metadata(self, resume_texts: List[str]) -> List[ResumeMetadata]:
        """
        批量提取多个简历的元数据
        
        Args:
            resume_texts (List[str]): 简历文本列表
            
        Returns:
            List[ResumeMetadata]: 元数据列表
        """
        results = []
        for i, resume_text in enumerate(resume_texts):
            try:
                metadata = self.extract_metadata(resume_text)
                results.append(metadata)
                logger.info(f"Successfully extracted metadata for resume {i+1}/{len(resume_texts)}")
            except Exception as e:
                logger.error(f"Failed to extract metadata for resume {i+1}: {e}")
                # 创建一个默认的元数据对象
                default_metadata = ResumeMetadata(name=f"简历_{i+1}_解析失败")
                results.append(default_metadata)
        
        return results