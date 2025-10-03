from typing import List, Dict, Any, Optional
from app.core.gemini_client import GeminiClient
from app.models.metadata import QueryMetadata
from loguru import logger
import json


class GeminiQueryParser:
    """
    基于Gemini的查询解析器，用于解析HR的自然语言查询
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        初始化查询解析器
        
        Args:
            gemini_client (GeminiClient): Gemini客户端实例
        """
        self.gemini_client = gemini_client
        logger.info("Initialized GeminiQueryParser")

    def parse_query(self, query_text: str) -> QueryMetadata:
        """
        解析自然语言查询为结构化查询元数据
        
        Args:
            query_text (str): HR的自然语言查询
            
        Returns:
            QueryMetadata: 结构化的查询元数据对象
        """
        try:
            # 构造提示词
            prompt = self._create_parsing_prompt(query_text)
            
            # 使用Gemini生成解析结果
            response = self.gemini_client.generate_text(prompt)
            
            # 解析响应为JSON
            query_dict = self._parse_response(response)
            
            # 验证和清理数据
            query_dict = self._validate_and_clean_query(query_dict)
            
            # 创建QueryMetadata对象
            query_metadata = QueryMetadata(**query_dict)
            
            logger.info(f"Parsed query: {query_metadata}")
            return query_metadata
            
        except Exception as e:
            logger.error(f"Failed to parse query: {e}")
            raise

    def _create_parsing_prompt(self, query_text: str) -> str:
        """
        创建查询解析提示词
        
        Args:
            query_text (str): HR的自然语言查询
            
        Returns:
            str: 构造的提示词
        """
        prompt = f"""
你是一位专业的HR助手，擅长理解招聘需求。请仔细分析以下HR的自然语言查询，并提取结构化的招聘要求。

HR查询:
{query_text}

请提取以下字段，并以JSON格式返回结果：

1. keywords: 关键词列表（从查询中提取的重要关键词）
2. required_skills: 必需技能列表（明确要求必须具备的技能）
3. preferred_skills: 优先技能列表（优先考虑但非必需的技能）
4. min_experience_years: 最少经验年限（整数，如果没有明确要求则为null）
5. required_education: 最低学历要求（如：大专、本科、硕士、博士，没有要求则为null）
6. required_industries: 必需行业经验列表（必须有相关行业经验）
7. preferred_industries: 优先行业经验列表（有相关行业经验更好）
8. salary_range: 薪资范围对象，包含min和max字段（如：{{"min": "15K", "max": "25K"}}）
9. locations: 工作地点列表（如：["北京", "上海"]）
10. required_languages: 语言要求列表（必须掌握的语言）
11. required_certifications: 证书要求列表（必须具备的证书）
12. custom_conditions: 其他自定义条件（不在上述分类中的特殊要求）

解析规则：
- 仔细区分"必需"和"优先"要求
- 从"X年以上经验"、"X年工作经验"等表述中提取经验年限
- 从"本科以上"、"硕士学历"等表述中提取学历要求
- 从"月薪X-Y"、"年薪X万"等表述中提取薪资范围
- 识别城市名称和地区要求
- 提取编程语言、技术栈、工具等技能要求
- 识别行业相关词汇

请严格按照以下JSON格式返回结果，不要包含其他文本：

{{
  "keywords": ["关键词1", "关键词2"],
  "required_skills": ["必需技能1", "必需技能2"],
  "preferred_skills": ["优先技能1", "优先技能2"],
  "min_experience_years": 3,
  "required_education": "本科",
  "required_industries": ["互联网", "金融"],
  "preferred_industries": ["电商", "科技"],
  "salary_range": {{"min": "15K", "max": "25K"}},
  "locations": ["北京", "上海"],
  "required_languages": ["中文", "英语"],
  "required_certifications": ["PMP", "软考"],
  "custom_conditions": "其他特殊要求"
}}

注意：如果某个字段没有明确信息，请设为null或空列表[]。
"""
        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析Gemini响应
        
        Args:
            response (str): Gemini生成的响应
            
        Returns:
            Dict[str, Any]: 解析后的查询元数据字典
            
        Raises:
            ValueError: 如果响应不是有效的JSON格式
        """
        try:
            # 使用Gemini客户端的JSON提取方法
            return self.gemini_client.extract_json_from_response(response)
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise ValueError(f"Failed to parse response as JSON: {response}")

    def _validate_and_clean_query(self, query_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和清理查询数据
        
        Args:
            query_dict (Dict[str, Any]): 原始查询字典
            
        Returns:
            Dict[str, Any]: 清理后的查询字典
        """
        # 确保列表字段是列表类型
        list_fields = ['keywords', 'required_skills', 'preferred_skills', 
                      'required_industries', 'preferred_industries', 
                      'locations', 'required_languages', 'required_certifications']
        
        for field in list_fields:
            if field not in query_dict or query_dict[field] is None:
                query_dict[field] = []
            elif not isinstance(query_dict[field], list):
                # 如果不是列表，尝试转换
                if isinstance(query_dict[field], str):
                    query_dict[field] = [query_dict[field]]
                else:
                    query_dict[field] = []
        
        # 验证经验年限
        if 'min_experience_years' in query_dict:
            if query_dict['min_experience_years'] is not None:
                try:
                    query_dict['min_experience_years'] = int(query_dict['min_experience_years'])
                except (ValueError, TypeError):
                    query_dict['min_experience_years'] = None
        
        # 验证薪资范围
        if 'salary_range' in query_dict and query_dict['salary_range']:
            if isinstance(query_dict['salary_range'], dict):
                # 确保有min和max字段
                if 'min' not in query_dict['salary_range']:
                    query_dict['salary_range']['min'] = None
                if 'max' not in query_dict['salary_range']:
                    query_dict['salary_range']['max'] = None
            else:
                query_dict['salary_range'] = None
        
        # 确保字符串字段
        string_fields = ['required_education', 'custom_conditions']
        for field in string_fields:
            if field not in query_dict:
                query_dict[field] = None
            elif query_dict[field] == "":
                query_dict[field] = None
        
        return query_dict

    def parse_multiple_queries(self, query_texts: List[str]) -> List[QueryMetadata]:
        """
        批量解析多个查询
        
        Args:
            query_texts (List[str]): 查询文本列表
            
        Returns:
            List[QueryMetadata]: 查询元数据列表
        """
        results = []
        for i, query_text in enumerate(query_texts):
            try:
                query_metadata = self.parse_query(query_text)
                results.append(query_metadata)
                logger.info(f"Successfully parsed query {i+1}/{len(query_texts)}")
            except Exception as e:
                logger.error(f"Failed to parse query {i+1}: {e}")
                # 创建一个默认的查询对象
                default_query = QueryMetadata(keywords=[f"查询_{i+1}_解析失败"])
                results.append(default_query)
        
        return results

    def enhance_query_with_context(self, query_text: str, context: Dict[str, Any]) -> QueryMetadata:
        """
        使用上下文信息增强查询解析
        
        Args:
            query_text (str): 原始查询文本
            context (Dict[str, Any]): 上下文信息（如公司信息、部门信息等）
            
        Returns:
            QueryMetadata: 增强后的查询元数据
        """
        enhanced_prompt = f"""
以下是HR的招聘查询，请结合提供的上下文信息进行更准确的解析：

查询文本: {query_text}

上下文信息:
{json.dumps(context, ensure_ascii=False, indent=2)}

请根据上下文信息更好地理解查询意图，并提取结构化的招聘要求。
"""
        
        try:
            response = self.gemini_client.generate_text(enhanced_prompt)
            query_dict = self._parse_response(response)
            query_dict = self._validate_and_clean_query(query_dict)
            return QueryMetadata(**query_dict)
        except Exception as e:
            logger.error(f"Failed to enhance query with context: {e}")
            # 如果增强失败，回退到基本解析
            return self.parse_query(query_text)