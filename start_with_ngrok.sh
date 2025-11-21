#!/bin/bash

# Webhook负载均衡服务 + ngrok 启动脚本

echo "=========================================="
echo "启动 Webhook 负载均衡服务"
echo "=========================================="

# 检查是否在conda环境中
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "激活 conda 环境 webhook-lb..."
    eval "$(conda shell.bash hook)"
    conda activate webhook-lb
fi

# 检查 ngrok 是否安装
if ! command -v ngrok &> /dev/null; then
    echo "错误: ngrok 未安装"
    echo "请先安装 ngrok:"
    echo "  brew install ngrok/ngrok/ngrok"
    echo "或访问: https://ngrok.com/download"
    exit 1
fi

# 检查服务是否已经在运行
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "警告: 端口 8000 已被占用"
    echo "请先停止占用该端口的服务"
    exit 1
fi

# 启动服务（后台运行）
echo "启动服务在端口 8000..."
python main.py &
SERVICE_PID=$!

# 等待服务启动
sleep 3

# 检查服务是否启动成功
if ! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "错误: 服务启动失败"
    kill $SERVICE_PID 2>/dev/null
    exit 1
fi

echo "服务已启动 (PID: $SERVICE_PID)"
echo ""

# 启动 ngrok
echo "启动 ngrok 隧道..."
ngrok http 8000 &
NGROK_PID=$!

echo ""
echo "=========================================="
echo "服务已启动！"
echo "=========================================="
echo "本地服务: http://localhost:8000"
echo "本地服务: http://10.10.13.191:8000 (局域网)"
echo ""
echo "ngrok 正在启动，请访问 http://localhost:4040 查看公网地址"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

# 等待用户中断
trap "echo ''; echo '正在停止服务...'; kill $SERVICE_PID $NGROK_PID 2>/dev/null; exit" INT

# 保持脚本运行
wait

