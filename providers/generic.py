"""
通用云平台提供者实现
"""
from typing import Dict, Any
from providers.base import BaseProvider
from config import ProviderConfig


class GenericProvider(BaseProvider):
    """通用云平台提供者，直接转发请求"""
    
    async def send_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        发送webhook请求
        
        Args:
            payload: 要发送的数据
            
        Returns:
            bool: 是否发送成功
        """
        return await self._make_request(payload)

