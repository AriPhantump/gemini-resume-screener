import google.generativeai as genai
from typing import List, Dict, Any, Optional
import os
from loguru import logger
import time
import json


class GeminiClient:
    """
    Gemini 2.5 Pro 客户端连接模块
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp", temperature: float = 0.0):
        """
        初始化Gemini客户端
        
        Args:
            model_name (str): 模型名称
            temperature (float): 采样温度
        """
        # 从环境变量获取API密钥
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # 配置Gemini
        genai.configure(api_key=api_key)
        
        # 初始化模型
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        self.model_name = model_name
        logger.info(f"Initialized Gemini client with model: {model_name}")

    def generate_text(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        生成文本
        
        Args:
            prompt (str): 用户提示
            system_message (str, optional): 系统消息
            
        Returns:
            str: 生成的文本
        """
        try:
            # 如果有系统消息，将其添加到提示前面
            if system_message:
                full_prompt = f"系统指令: {system_message}\n\n用户请求: {prompt}"
            else:
                full_prompt = prompt
                
            # 生成内容
            response = self.model.generate_content(full_prompt)
            
            # 检查响应是否被阻止
            if response.prompt_feedback.block_reason:
                logger.warning(f"Content was blocked: {response.prompt_feedback.block_reason}")
                return "内容被安全过滤器阻止，请调整输入内容。"
            
            # 获取生成的文本
            if response.parts:
                generated_text = response.text
                logger.debug(f"Generated text with {len(generated_text)} characters")
                return generated_text
            else:
                logger.warning("No content generated")
                return "未生成任何内容。"
                
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            # 重试机制
            try:
                time.sleep(1)
                response = self.model.generate_content(full_prompt)
                if response.parts:
                    return response.text
                else:
                    return "生成失败，请重试。"
            except Exception as retry_e:
                logger.error(f"Retry also failed: {retry_e}")
                raise

    def generate_with_template(self, template: str, **kwargs) -> str:
        """
        使用模板生成文本
        
        Args:
            template (str): 提示模板
            **kwargs: 模板变量
            
        Returns:
            str: 生成的文本
        """
        try:
            prompt = template.format(**kwargs)
            response = self.generate_text(prompt)
            logger.debug(f"Generated text with template, response length: {len(response)}")
            return response
        except Exception as e:
            logger.error(f"Failed to generate text with template: {e}")
            raise

    def extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        从响应中提取JSON数据
        
        Args:
            response_text (str): 响应文本
            
        Returns:
            Dict[str, Any]: 提取的JSON数据
        """
        try:
            # 尝试直接解析JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从响应中提取JSON部分
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end != -1 and start < end:
                json_str = response_text[start:end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # 如果所有尝试都失败，抛出异常
            raise ValueError(f"Failed to extract JSON from response: {response_text}")

    def generate_structured_response(self, prompt: str, expected_fields: List[str]) -> Dict[str, Any]:
        """
        生成结构化响应
        
        Args:
            prompt (str): 提示
            expected_fields (List[str]): 期望的字段列表
            
        Returns:
            Dict[str, Any]: 结构化响应
        """
        structured_prompt = f"""
{prompt}

请严格按照以下JSON格式返回结果，只返回JSON，不要包含其他文本：
{{
{', '.join([f'"{field}": "相应的值"' for field in expected_fields])}
}}
"""
        
        response_text = self.generate_text(structured_prompt)
        return self.extract_json_from_response(response_text)