"""
云平台提供者基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from config import ProviderConfig


class BaseProvider(ABC):
    """云平台提供者基类"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)
    
    @property
    def name(self) -> str:
        """提供者名称"""
        return self.config.name
    
    @property
    def is_available(self) -> bool:
        """检查是否可用（是否有剩余免费额度）"""
        if not self.config.enabled:
            return False
        return self.config.used_quota < self.config.free_quota
    
    @abstractmethod
    async def send_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        发送webhook请求
        
        Args:
            payload: 要发送的数据
            
        Returns:
            bool: 是否发送成功
        """
        pass
    
    async def _make_request(self, payload: Dict[str, Any]) -> bool:
        """
        执行HTTP请求
        
        Args:
            payload: 要发送的数据（Grafana webhook 原始格式，完全保持不变）
            
        Returns:
            bool: 是否请求成功
        """
        try:
            # 确保 Content-Type 为 application/json（如果配置中没有指定）
            headers = self.config.headers.copy()
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
            
            # 直接转发原始 payload，不做任何修改
            response = await self.client.post(
                self.config.endpoint,
                json=payload,  # 完全保持 Grafana 原始格式
                headers=headers
            )
            response.raise_for_status()
            
            # 更新已使用额度
            self.config.used_quota += 1
            return True
        except Exception as e:
            print(f"Provider {self.name} 发送失败: {e}")
            return False
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

