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
        print(f"信息: providers_config.py 文件不存在，将使用默认配置")
        return []
    
    try:
        # 动态导入配置文件
        import importlib.util
        spec = importlib.util.spec_from_file_location("providers_config", config_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "PROVIDERS"):
                providers = module.PROVIDERS
                if providers and isinstance(providers, list) and len(providers) > 0:
                    print(f"信息: 成功从 providers_config.py 加载 {len(providers)} 个 Provider 配置")
                    return providers
                else:
                    print(f"警告: providers_config.py 中的 PROVIDERS 列表为空或格式不正确")
                    return []
            else:
                print(f"警告: providers_config.py 中未找到 PROVIDERS 变量")
                return []
        else:
            print(f"错误: 无法创建 providers_config.py 模块规范")
            return []
    except Exception as e:
        print(f"错误: 加载 providers_config.py 失败: {e}")
        import traceback
        traceback.print_exc()
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
                    print(f"信息: 成功从 providers_config.py 解析 {len(self.providers)} 个 Provider 配置")
                except (TypeError, ValueError) as e:
                    error_msg = f"解析 providers_config.py 中的配置失败: {e}"
                    print(f"错误: {error_msg}")
                    raise ValueError(error_msg)


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

