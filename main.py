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
from config import AppConfig

app = FastAPI(title="Webhook报警接收服务", version="1.0.0")

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
    """应用启动时初始化日志"""
    global alert_logger
    
    # 初始化日志
    alert_logger = setup_logging()
    alert_logger.info("=" * 50)
    alert_logger.info("Webhook报警接收服务启动")
    alert_logger.info("服务模式: 仅本地记录（不转发到外部服务）")


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
        # 即使日志记录失败，也返回成功响应（200状态码）
        return {
            "status": "error",
            "message": f"Failed to record alert: {str(e)}"
        }
    
    # 返回成功响应（固定格式，200状态码）
    return {
        "status": "success",
        "message": "Alert received and recorded"
    }


@app.get("/status")
async def get_status():
    """
    获取服务状态
    
    Returns:
        Dict[str, Any]: 服务状态信息
    """
    return {
        "service": "webhook-alert-receiver",
        "mode": "local-only",
        "status": "running",
        "log_enabled": alert_logger is not None
    }


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

