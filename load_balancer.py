"""
负载均衡器 - 轮询策略
"""
from typing import List, Optional, Dict, Any
from providers.base import BaseProvider
from providers.generic import GenericProvider
from config import ProviderConfig


class RoundRobinLoadBalancer:
    """轮询负载均衡器"""
    
    def __init__(self, providers: List[ProviderConfig]):
        """
        初始化负载均衡器
        
        Args:
            providers: 云平台提供者配置列表
        """
        self.providers: List[BaseProvider] = []
        self.current_index = 0
        
        # 初始化提供者实例
        for config in providers:
            if config.enabled:
                provider = GenericProvider(config)
                self.providers.append(provider)
    
    def get_next_provider(self) -> Optional[BaseProvider]:
        """
        获取下一个可用的提供者（轮询策略）
        
        Returns:
            Optional[BaseProvider]: 可用的提供者，如果没有则返回None
        """
        if not self.providers:
            return None
        
        # 尝试找到可用的提供者
        attempts = 0
        max_attempts = len(self.providers)
        
        while attempts < max_attempts:
            provider = self.providers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.providers)
            
            if provider.is_available:
                return provider
            
            attempts += 1
        
        # 所有提供者都不可用
        return None
    
    async def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送webhook请求（使用轮询策略）
        
        Args:
            payload: 要发送的数据
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        provider = self.get_next_provider()
        
        if provider is None:
            return {
                "success": False,
                "error": "没有可用的云平台提供者",
                "provider": None
            }
        
        success = await provider.send_webhook(payload)
        
        return {
            "success": success,
            "provider": provider.name,
            "error": None if success else "发送失败"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取所有提供者的状态
        
        Returns:
            Dict[str, Any]: 提供者状态信息
        """
        status = {
            "providers": [],
            "total": len(self.providers),
            "available": 0
        }
        
        for provider in self.providers:
            provider_status = {
                "name": provider.name,
                "enabled": provider.config.enabled,
                "available": provider.is_available,
                "quota_used": provider.config.used_quota,
                "quota_total": provider.config.free_quota,
                "quota_remaining": max(0, provider.config.free_quota - provider.config.used_quota)
            }
            status["providers"].append(provider_status)
            if provider.is_available:
                status["available"] += 1
        
        return status
    
    async def close(self):
        """关闭所有提供者的连接"""
        for provider in self.providers:
            await provider.close()

