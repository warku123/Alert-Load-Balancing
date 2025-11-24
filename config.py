"""
配置管理模块
"""
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class ProviderConfig(BaseSettings):
    """云平台提供者配置"""
    name: str = Field(..., description="提供者名称")
    enabled: bool = Field(default=True, description="是否启用")
    endpoint: str = Field(..., description="webhook端点URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    timeout: int = Field(default=30, description="超时时间（秒）")
    free_quota: int = Field(default=1000, description="免费额度")
    used_quota: int = Field(default=0, description="已使用额度")


class AppConfig(BaseSettings):
    """应用配置"""
    host: str = Field(default="0.0.0.0", description="监听地址")
    port: int = Field(default=8048, description="监听端口")
    providers: List[ProviderConfig] = Field(default_factory=list, description="云平台提供者列表")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 默认配置示例
DEFAULT_PROVIDERS = [
    {
        "name": "provider1",
        "enabled": True,
        "endpoint": "https://example.com/webhook1",
        "headers": {"Content-Type": "application/json"},
        "timeout": 30,
        "free_quota": 1000,
        "used_quota": 0,
    },
    {
        "name": "provider2",
        "enabled": True,
        "endpoint": "https://example.com/webhook2",
        "headers": {"Content-Type": "application/json"},
        "timeout": 30,
        "free_quota": 500,
        "used_quota": 0,
    },
]

