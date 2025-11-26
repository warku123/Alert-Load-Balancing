"""
Webhook报警接收服务主入口
"""
from fastapi import FastAPI
from typing import Dict, Any
import uvicorn
import logging
import json
from datetime import datetime
from pathlib import Path
from config import AppConfig, ProviderConfig, DEFAULT_PROVIDERS
from providers import Provider
from load_balancer import create_load_balancer, BaseLoadBalancer

app = FastAPI(title="Webhook报警接收服务", version="1.0.0")

# 日志记录器
alert_logger = None

# 负载均衡器实例
load_balancer: BaseLoadBalancer = None


def setup_logging():
    """配置日志记录"""
    global alert_logger
    
    # 创建logs目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建报警日志记录器
    alert_logger = logging.getLogger("alert_logger")
    alert_logger.setLevel(logging.INFO)
    
    # 文件处理器 - 按日期滚动
    log_file = log_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    alert_logger.addHandler(file_handler)
    
    # 防止日志传播到根记录器
    alert_logger.propagate = False
    
    return alert_logger


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化日志和负载均衡器"""
    global alert_logger, load_balancer
    
    # 初始化日志
    alert_logger = setup_logging()
    alert_logger.info("=" * 50)
    alert_logger.info("Webhook报警接收服务启动")
    
    # 加载配置
    config = AppConfig()
    
    # 初始化 Provider 列表
    providers = []
    
    # 检查配置文件是否存在
    providers_config_file = Path("providers_config.py")
    if not providers_config_file.exists():
        alert_logger.warning(f"未找到 providers_config.py 文件，请从 providers_config.py.example 复制并配置")
    
    # 如果没有配置提供者，使用默认配置
    if not config.providers:
        if DEFAULT_PROVIDERS:
            config.providers = [ProviderConfig(**p) for p in DEFAULT_PROVIDERS]
            alert_logger.info("使用默认 Provider 配置")
        else:
            alert_logger.warning("未找到任何 Provider 配置（providers_config.py 为空或不存在）")
    else:
        alert_logger.info(f"从配置文件加载了 {len(config.providers)} 个 Provider 配置")
    
    # 创建 Provider 实例
    for provider_config in config.providers:
        if provider_config.enabled:
            provider = Provider(provider_config)
            providers.append(provider)
            alert_logger.info(f"已加载 Provider: {provider.name} (端点: {provider_config.endpoint})")
        else:
            alert_logger.info(f"跳过禁用的 Provider: {provider_config.name}")
    
    # 初始化负载均衡器
    if providers:
        try:
            strategy = config.load_balancer_strategy
            load_balancer = create_load_balancer(strategy, providers)
            alert_logger.info(f"负载均衡器已启动: {strategy} 策略, 共 {len(providers)} 个 Provider")
        except ValueError as e:
            alert_logger.error(f"负载均衡器初始化失败: {e}")
            # 初始化失败，默认在本地记录
            load_balancer = None
            alert_logger.info(f"初始化负载均衡器失败，将在本地记录报警")
    else:
        load_balancer = None
        alert_logger.info("服务模式: 仅本地记录（未配置云平台提供者，不转发到外部服务）")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global load_balancer
    
    # 关闭所有 Provider 的连接
    if load_balancer:
        for provider in load_balancer.providers:
            try:
                await provider.close()
            except Exception as e:
                if alert_logger:
                    alert_logger.error(f"关闭 Provider {provider.name} 连接失败: {e}")
    
    if alert_logger:
        alert_logger.info("服务已关闭")


@app.post("/webhook")
async def webhook_handler(payload: Dict[str, Any]):
    """
    接收webhook请求并记录到本地日志
    
    FastAPI 会自动将 JSON 请求体解析为 Python 字典。
    无需手动解析，payload 参数已包含完整的 Grafana webhook 数据。
    
    Args:
        payload: webhook请求体（FastAPI 自动从 JSON 解析为 Dict[str, Any]）
                包含完整的 Grafana 格式：receiver, status, alerts, title 等所有字段
        
    Returns:
        Dict[str, Any]: 接收结果
    """
    if alert_logger is None:
        return {
            "status": "error",
            "message": "Local alert logger not initialized"
        }
    
    # 记录接收到的报警信息（保持原始 Grafana 格式，不做修改）
    try:
        # 提取 Grafana payload 中的关键信息用于日志
        status = payload.get("status", "unknown")
        alert_count = len(payload.get("alerts", []))
        title = payload.get("title", "")
        receiver = payload.get("receiver", "")
        alert_logger.info(f"收到报警 [接收者={receiver}, 状态={status}, 数量={alert_count}, 标题={title}]")
        # 记录完整的 payload（完全保持 Grafana 原始格式，包含所有字段如 timestamp、alerts 等）
        alert_logger.info(f"完整报警数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    except Exception as e:
        alert_logger.error(f"记录报警日志失败: {e}")
        return {
            "status": "error",
            "message": f"Failed to record alert: {str(e)}"
        }
    
    # 如果有负载均衡器，尝试转发到云平台
    forward_success = False
    if load_balancer:
        try:
            forward_result = await load_balancer.send(payload)
            forward_success = forward_result.get("success", False)
            
            # 记录转发结果
            if forward_success:
                provider_name = forward_result.get("provider", "unknown")
                alert_logger.info(f"报警转发成功 [提供者={provider_name}]")
            else:
                error_msg = forward_result.get("error", "未知错误")
                provider_name = forward_result.get("provider", "unknown")
                alert_logger.warning(f"报警转发失败 [提供者={provider_name}, 错误={error_msg}]")
        except Exception as e:
            alert_logger.error(f"转发报警时发生异常: {e}")
            forward_success = False
    
    # 返回响应（固定格式，200状态码）
    # 即使转发失败，也返回成功，因为已经记录在本地日志
    if forward_success:
        return {
            "status": "success",
            "message": f"Alert received and forwarded to {provider_name}"
        }
    else:
        return {
            "status": "success",
            "message": "Alert received and recorded in local log only"
        }


@app.get("/status")
async def get_status():
    """
    获取服务状态
    
    Returns:
        Dict[str, Any]: 服务状态信息
    """
    status = {
        "service": "webhook-alert-receiver",
        "status": "running",
        "log_enabled": alert_logger is not None,
        "load_balancer": None
    }
    
    # 如果有负载均衡器，添加 Provider 状态信息
    if load_balancer:
        load_balancer_status = load_balancer.get_status()
        status["load_balancer"] = load_balancer_status
        # 根据是否有可用的 Provider 设置模式
        if load_balancer_status["available"] > 0:
            status["mode"] = "load-balanced"
        else:
            status["mode"] = "local-only"
    
    return status


@app.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        Dict[str, str]: 健康状态
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    config = AppConfig()
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True
    )

