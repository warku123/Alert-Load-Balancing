"""
负载均衡器模块
支持多种负载均衡策略
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from providers import Provider


class BaseLoadBalancer(ABC):
    """负载均衡器基类"""
    
    def __init__(self, providers: List[Provider]):
        """
        初始化负载均衡器
        
        Args:
            providers: Provider 列表
        """
        self.providers: List[Provider] = providers
    
    @abstractmethod
    async def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 webhook 请求
        
        Args:
            payload: 要发送的数据（Grafana webhook 原始格式）
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        获取所有 Provider 的状态
        
        Returns:
            Dict[str, Any]: Provider 状态信息
        """
        pass


class RoundRobinLoadBalancer(BaseLoadBalancer):
    """轮询负载均衡器（Round Robin）"""
    
    """轮询负载均衡器（Round Robin）"""
    
    def __init__(self, providers: List[Provider]):
        """
        初始化负载均衡器
        
        Args:
            providers: Provider 列表
        """
        super().__init__(providers)
        self.current_index = 0
    
    def get_next_provider(self) -> Optional[Provider]:
        """
        获取下一个可用的 Provider（轮询策略）
        
        Returns:
            Optional[Provider]: 可用的 Provider，如果没有则返回 None
        """
        if not self.providers:
            return None
        
        # 尝试找到可用的 Provider
        attempts = 0
        max_attempts = len(self.providers)
        
        while attempts < max_attempts:
            provider = self.providers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.providers)
            
            if provider.is_available:
                return provider
            
            attempts += 1
        
        # 所有 Provider 都不可用
        return None
    
    async def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 webhook 请求（使用轮询策略）
        
        Args:
            payload: 要发送的数据（Grafana webhook 原始格式）
            
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
        获取所有 Provider 的状态
        
        Returns:
            Dict[str, Any]: Provider 状态信息
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
                "endpoint": provider.config.endpoint
            }
            status["providers"].append(provider_status)
            if provider.is_available:
                status["available"] += 1
        
        return status


class WeightedRoundRobinLoadBalancer(BaseLoadBalancer):
    """加权轮询负载均衡器（暂未实现，使用轮询策略代替）"""
    
    def __init__(self, providers: List[Provider]):
        super().__init__(providers)
        # TODO: 实现加权轮询逻辑
        # 暂时使用轮询策略
        self.current_index = 0
    
    async def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: 实现加权轮询发送逻辑
        # 暂时使用轮询策略
        if not self.providers:
            return {
                "success": False,
                "error": "没有可用的云平台提供者",
                "provider": None
            }
        
        attempts = 0
        max_attempts = len(self.providers)
        while attempts < max_attempts:
            provider = self.providers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.providers)
            if provider.is_available:
                success = await provider.send_webhook(payload)
                return {
                    "success": success,
                    "provider": provider.name,
                    "error": None if success else "发送失败"
                }
            attempts += 1
        
        return {
            "success": False,
            "error": "没有可用的云平台提供者",
            "provider": None
        }
    
    def get_status(self) -> Dict[str, Any]:
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
                "endpoint": provider.config.endpoint
            }
            status["providers"].append(provider_status)
            if provider.is_available:
                status["available"] += 1
        return status


class LeastConnectionsLoadBalancer(BaseLoadBalancer):
    """最少连接负载均衡器（暂未实现，使用轮询策略代替）"""
    
    def __init__(self, providers: List[Provider]):
        super().__init__(providers)
        # TODO: 实现最少连接逻辑
        # 暂时使用轮询策略
        self.current_index = 0
    
    async def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: 实现最少连接发送逻辑
        # 暂时使用轮询策略
        if not self.providers:
            return {
                "success": False,
                "error": "没有可用的云平台提供者",
                "provider": None
            }
        
        attempts = 0
        max_attempts = len(self.providers)
        while attempts < max_attempts:
            provider = self.providers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.providers)
            if provider.is_available:
                success = await provider.send_webhook(payload)
                return {
                    "success": success,
                    "provider": provider.name,
                    "error": None if success else "发送失败"
                }
            attempts += 1
        
        return {
            "success": False,
            "error": "没有可用的云平台提供者",
            "provider": None
        }
    
    def get_status(self) -> Dict[str, Any]:
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
                "endpoint": provider.config.endpoint
            }
            status["providers"].append(provider_status)
            if provider.is_available:
                status["available"] += 1
        return status


def create_load_balancer(strategy: str, providers: List[Provider]) -> BaseLoadBalancer:
    """
    根据策略创建负载均衡器实例
    
    Args:
        strategy: 负载均衡策略名称（"round_robin", "weighted_round_robin", "least_connections"）
        providers: Provider 列表
        
    Returns:
        BaseLoadBalancer: 负载均衡器实例
        
    Raises:
        ValueError: 如果策略名称无效
    """
    strategy_map = {
        "round_robin": RoundRobinLoadBalancer,
        "weighted_round_robin": WeightedRoundRobinLoadBalancer,
        "least_connections": LeastConnectionsLoadBalancer,
    }
    
    balancer_class = strategy_map.get(strategy.lower())
    if balancer_class is None:
        raise ValueError(f"无效的负载均衡策略: {strategy}. 可用策略: {', '.join(strategy_map.keys())}")
    
    return balancer_class(providers)