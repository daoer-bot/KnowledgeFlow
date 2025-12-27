"""
LLM 客户端封装
支持 OpenAI API 调用，带重试和错误处理
"""

import os
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from openai import APIError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端封装类"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash-lite-preview-06-17-nothinking",
        max_retries: int = 3
    ):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: OpenAI API Key（默认从环境变量读取）
            model: 使用的模型名称
            max_retries: 最大重试次数
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # 获取 API Base URL
        api_base = os.getenv("OPENAI_API_BASE")
        
        self.model = model
        self.max_retries = max_retries
        
        # 初始化客户端，支持自定义 base_url 和超时设置
        client_kwargs = {
            "api_key": self.api_key,
            "timeout": 60.0,  # 增加超时时间到60秒
            "max_retries": 2
        }
        
        if api_base:
            client_kwargs["base_url"] = api_base
            logger.info(f"Using custom API base: {api_base}")
        
        self.client = AsyncOpenAI(**client_kwargs)
        
        logger.info(f"LLM client initialized with model: {model}")
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 20000,
        json_mode: bool = False
    ) -> str:
        """
        生成文本
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数（0-2）
            max_tokens: 最大token数
            json_mode: 是否使用JSON模式
            
        Returns:
            生成的文本
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            logger.debug(f"Generated {len(content)} characters")
            
            return content
            
        except Exception as e:
            logger.error(f"Error in LLM generation: {str(e)}")
            raise
    
    async def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 20000,
        json_mode: bool = False
    ) -> Optional[str]:
        """
        带重试机制的生成
        
        使用指数退避策略重试失败的请求
        
        Returns:
            生成的文本，失败返回 None
        """
        for attempt in range(self.max_retries):
            try:
                return await self.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode
                )
            
            except RateLimitError:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避：1s, 2s, 4s
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Rate limit exceeded after all retries")
                    return None
            
            except APIConnectionError:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Connection error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Connection failed after all retries")
                    return None
            
            except APIError as e:
                logger.error(f"API error: {str(e)}")
                return None
            
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                return None
        
        return None
    
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 20000
    ) -> Optional[Dict[str, Any]]:
        """
        生成 JSON 格式的响应
        
        Returns:
            解析后的 JSON 对象，失败返回 None
        """
        response_text = await self.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True
        )
        
        if not response_text:
            return None
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}")
            return None
    
    async def stream_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 20000
    ):
        """
        流式生成（用于长文本）
        
        Yields:
            生成的文本片段
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in stream generation: {str(e)}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数量（粗略估计）
        
        实际应该使用 tiktoken 库，这里简化为字符数/4
        """
        # 简单估算：中文约1字符=1token，英文约4字符=1token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        return chinese_chars + (other_chars // 4)
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        截断文本到指定 token 数量
        
        Args:
            text: 原文本
            max_tokens: 最大 token 数
            
        Returns:
            截断后的文本
        """
        estimated = self.estimate_tokens(text)
        
        if estimated <= max_tokens:
            return text
        
        # 粗略按比例截断
        ratio = max_tokens / estimated
        target_length = int(len(text) * ratio * 0.9)  # 留10%余量
        
        return text[:target_length] + "\n\n[内容已截断...]"


# 全局 LLM 客户端实例
_llm_instance = None


def get_llm_client(model: str = "gemini-2.5-flash-lite-nothinking") -> LLMClient:
    """
    获取全局 LLM 客户端实例
    
    Args:
        model: 模型名称
        
    Returns:
        LLM 客户端实例
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient(model=model)
    return _llm_instance