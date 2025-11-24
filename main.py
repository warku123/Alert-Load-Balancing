"""
Webhook负载均衡服务主入口
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import uvicorn
import logging
import json
from datetime import datetime
from pathlib import Path
from config import AppConfig, DEFAULT_PROVIDERS, ProviderConfig
from load_balancer import RoundRobinLoadBalancer

app = FastAPI(title="Webhook负载均衡服务", version="1.0.0")

# 全局负载均衡器实例
load_balancer: RoundRobinLoadBalancer = None

# 日志记录器
alert_logger = None


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
    """应用启动时初始化负载均衡器"""
    global load_balancer, alert_logger
    
    # 初始化日志
    alert_logger = setup_logging()
    alert_logger.info("=" * 50)
    alert_logger.info("Webhook负载均衡服务启动")
    
    # 加载配置（这里简化处理，实际可以从环境变量或配置文件读取）
    config = AppConfig()
    
    # 如果没有配置提供者，使用默认配置
    if not config.providers:
        config.providers = [ProviderConfig(**p) for p in DEFAULT_PROVIDERS]
    
    # 检查是否仍然没有提供者
    if not config.providers:
        warning_msg = "警告：未配置任何云平台提供者，警告将在本地日志记录，不会转发到外部服务"
        alert_logger.warning(warning_msg)
    
    # 初始化负载均衡器
    load_balancer = RoundRobinLoadBalancer(config.providers)
    alert_logger.info(f"负载均衡器已启动，共 {len(load_balancer.providers)} 个提供者")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global load_balancer
    if load_balancer:
        await load_balancer.close()


@app.post("/webhook")
async def webhook_handler(payload: Dict[str, Any]):
    """
    接收webhook请求并转发到云平台
    
    FastAPI 会自动将 JSON 请求体解析为 Python 字典。
    无需手动解析，payload 参数已包含完整的 Grafana webhook 数据。
    
    Args:
        payload: webhook请求体（FastAPI 自动从 JSON 解析为 Dict[str, Any]）
                包含完整的 Grafana 格式：receiver, status, alerts, title 等所有字段
        
    Returns:
        Dict[str, Any]: 转发结果
    """
    if load_balancer is None:
        raise HTTPException(status_code=503, detail="负载均衡器未初始化")
    
    # 记录接收到的报警信息（保持原始 Grafana 格式，不做修改）
    if alert_logger:
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
    
    result = await load_balancer.send(payload)
    
    # 记录转发结果
    if alert_logger:
        try:
            if result["success"]:
                provider_name = result.get("provider", "unknown")
                alert_logger.info(f"报警转发成功 [提供者={provider_name}]")
            else:
                # 如果没有provider，只是记录在本地，不算失败
                if result.get("error") == "没有可用的云平台提供者":
                    alert_logger.info("报警已记录在本地（无可用云平台提供者，不会转发）")
                else:
                    error_msg = result.get("error", "未知错误")
                    provider_name = result.get("provider", "unknown")
                    alert_logger.warning(f"报警转发失败 [提供者={provider_name}, 错误={error_msg}]")
        except Exception as e:
            alert_logger.error(f"记录转发结果失败: {e}")
    
    # 如果没有provider，返回200 OK，表示已接收并记录（不会转发到外部服务）
    if not result["success"] and result.get("error") == "没有可用的云平台提供者":
        return {
            "success": True,
            "message": "报警已接收并记录在本地日志（无可用云平台提供者）",
            "provider": None,
            "forwarded": False
        }
    
    # 如果转发失败，返回502错误
    if not result["success"]:
        return JSONResponse(
            status_code=502,
            content=result
        )
    
    return result


@app.get("/status")
async def get_status():
    """
    获取所有云平台提供者的状态
    
    Returns:
        Dict[str, Any]: 提供者状态信息
    """
    if load_balancer is None:
        raise HTTPException(status_code=503, detail="负载均衡器未初始化")
    
    return load_balancer.get_status()


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

