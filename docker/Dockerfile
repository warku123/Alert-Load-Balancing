# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖（如果需要）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY main.py .
COPY config.py .
COPY load_balancer.py .
COPY providers/ ./providers/
COPY providers_config.py .
COPY .env .

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口（默认 8048，可通过环境变量修改）
EXPOSE 8048

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8048/health || exit 1

# 启动命令
CMD ["python", "main.py"]

