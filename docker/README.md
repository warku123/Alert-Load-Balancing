# Docker 部署说明

## 构建镜像

### 方式一：使用 docker build

```bash
# 在项目根目录执行
docker build -f docker/Dockerfile -t webhook-load-balancer:latest .
```

### 方式二：使用 docker-compose

```bash
# 在 docker 目录下执行
cd docker
docker-compose build
```

## 运行容器

### 方式一：使用 docker run

```bash
docker run -d \
  --name webhook-load-balancer \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  webhook-load-balancer:latest
```

### 方式二：使用 docker-compose（推荐）

```bash
# 在 docker 目录下执行
cd docker
docker-compose up -d
```

查看日志：
```bash
docker-compose logs -f
```

## 停止容器

```bash
# 使用 docker-compose
docker-compose down

# 或使用 docker
docker stop webhook-load-balancer
docker rm webhook-load-balancer
```

## 环境变量配置

可以通过环境变量或 `.env` 文件配置服务：

```bash
docker run -d \
  --name webhook-load-balancer \
  -p 8000:8000 \
  -e PORT=8000 \
  -e HOST=0.0.0.0 \
  -v $(pwd)/logs:/app/logs \
  webhook-load-balancer:latest
```

或在 `docker-compose.yml` 中的 `environment` 部分添加配置。

## 健康检查

容器启动后，可以通过以下方式检查服务状态：

```bash
# 健康检查端点
curl http://localhost:8000/health

# 查看提供者状态
curl http://localhost:8000/status
```

## 查看日志

```bash
# 查看容器日志
docker logs -f webhook-load-balancer

# 查看应用日志（挂载的 logs 目录）
tail -f logs/alerts_*.log
```

