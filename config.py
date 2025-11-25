"""
配置管理模块
"""
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path


class ProviderConfig(BaseSettings):
    """云平台提供者配置"""
    name: str = Field(..., description="提供者名称")
    enabled: bool = Field(default=True, description="是否启用")
    endpoint: str = Field(..., description="webhook端点URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    timeout: int = Field(default=30, description="超时时间（秒）")


def load_providers_config():
    """
    从 providers_config.py 文件加载 Provider 配置
    
    Returns:
        List[dict]: Provider 配置列表
    """
    config_file = Path("providers_config.py")
    
    if not config_file.exists():
        return []
    
    try:
        # 动态导入配置文件
        import importlib.util
        spec = importlib.util.spec_from_file_location("providers_config", config_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "PROVIDERS"):
                return module.PROVIDERS
    except Exception as e:
        print(f"警告: 加载 providers_config.py 失败: {e}")
    
    return []


class AppConfig(BaseSettings):
    """应用配置"""
    host: str = Field(default="0.0.0.0", description="监听地址")
    port: int = Field(default=8048, description="监听端口")
    load_balancer_strategy: str = Field(default="round_robin", description="负载均衡策略 (round_robin, weighted_round_robin, least_connections)")
    providers: List[ProviderConfig] = Field(default_factory=list, description="云平台提供者列表")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果providers为空，尝试从 providers_config.py 文件加载配置
        if not self.providers:
            providers_data = load_providers_config()
            if providers_data:
                try:
                    self.providers = [ProviderConfig(**p) for p in providers_data]
                except (TypeError, ValueError) as e:
                    raise ValueError(f"解析 providers_config.py 中的配置失败: {e}")


# 默认配置示例
DEFAULT_PROVIDERS = [
    # {
    #     "name": "provider1",
    #     "enabled": True,
    #     "endpoint": "https://example.com/webhook1",
    #     "headers": {"Content-Type": "application/json"},
    #     "timeout": 30,
    # },
]

