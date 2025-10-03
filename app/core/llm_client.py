from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from loguru import logger


class LLMClient:
    """
    LLM客户端连接模块
    """
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.0):
        """
        初始化LLM客户端
        
        Args:
            model_name (str): 模型名称
            temperature (float): 采样温度
        """
        # 从环境变量获取API密钥和基础URL
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # 初始化模型
        self.model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key,
            openai_api_base=base_url
        )
        self.model_name = model_name
        logger.info(f"Initialized LLM client with model: {model_name}")

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
            if system_message:
                messages = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=prompt)
                ]
            else:
                messages = [HumanMessage(content=prompt)]
                
            response = self.model.invoke(messages)
            logger.debug(f"Generated text with {len(response.content)} characters")
            return response.content
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
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
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.model | StrOutputParser()
            response = chain.invoke(kwargs)
            logger.debug(f"Generated text with template, response length: {len(response)}")
            return response
        except Exception as e:
            logger.error(f"Failed to generate text with template: {e}")
            raise