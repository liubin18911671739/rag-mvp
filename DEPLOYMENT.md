# 企业知识库 RAG 系统 - 部署指南

## 系统要求

### 硬件要求

**最低配置**:
- CPU: 4核
- 内存: 8GB
- 存储: 20GB

**推荐配置**:
- CPU: 8核+
- 内存: 16GB+
- 存储: 50GB+ SSD
- GPU: NVIDIA GPU (可选,用于加速 embedding)

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- (可选) 本地 Ollama 安装

## 部署步骤

### 方式 1: 使用本地 Ollama (推荐)

1. **安装并启动 Ollama**:
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# 启动 Ollama 服务
ollama serve

# 拉取模型
ollama pull llama3.1:8b
ollama pull nomic-embed-text  # 可选,用于 embedding
```

2. **下载 Embedding 模型**:
```bash
# 创建模型目录
mkdir -p models/bge-m3

# 从 HuggingFace 下载
# 访问: https://huggingface.co/BAAI/bge-m3
# 下载所有文件到 models/bge-m3/
```

3. **配置环境变量**:
```bash
cp .env.example .env

# 编辑 .env,设置:
OLLAMA_URL=http://host.docker.internal:11434
EMBED_MODEL_PATH=/models/bge-m3
```

4. **启动服务**:
```bash
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 方式 2: 使用 Docker Ollama

1. **修改 docker-compose.yml**:
```yaml
# 取消 ollama 服务的注释
ollama:
  image: ollama/ollama:latest
  ...
```

2. **配置环境变量**:
```bash
# .env
OLLAMA_URL=http://ollama:11434
```

3. **启动服务**:
```bash
docker-compose up -d

# 等待 Ollama 拉取模型
docker-compose exec ollama ollama pull llama3.1:8b
```

## 验证部署

### 1. 检查服务状态

```bash
# 检查所有容器
docker-compose ps

# 检查 API 健康
curl http://localhost:8000/health

# 检查数据库连接
docker-compose exec postgres pg_isready
```

### 2. 访问 Web UI

- Streamlit UI: http://localhost:8501
- API 文档: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

### 3. 运行测试

```bash
# 准备测试文档
echo "测试文档内容" > data/raw/test.txt

# 摄取文档
curl -X POST http://localhost:8000/api/ingest \
  -F "path=/app/data/raw"

# 查询测试
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "测试问题"}'
```

## 生产环境配置

### 1. 资源限制

修改 `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### 2. 数据持久化

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: /data/postgres
      o: bind
```

### 3. 安全配置

- 修改默认密码
- 配置 HTTPS/SSL
- 限制网络访问
- 启用日志审计

### 4. 监控告警

- 配置 Prometheus 抓取 `/metrics`
- 设置 Grafana 仪表板
- 配置告警规则

## 常见问题

### Q: Ollama 连接失败

A: 检查 `.env` 中的 `OLLAMA_URL`:
- 本地 Ollama: `http://host.docker.internal:11434`
- Docker Ollama: `http://ollama:11434`

### Q: Embedding 模型加载失败

A: 确认:
1. 模型文件完整下载到 `models/bge-m3/`
2. `.env` 中 `EMBED_MODEL_PATH` 配置正确
3. 容器有权限访问模型目录

### Q: 内存不足

A: 解决方案:
1. 减小 `CHUNK_SIZE` 和 `BATCH_SIZE`
2. 使用量化模型
3. 增加 swap 空间
4. 升级硬件配置

### Q: 查询速度慢

A: 优化方案:
1. 使用 GPU 加速 embedding
2. 调整向量索引参数 (`lists`)
3. 减少 `TOP_K` 值
4. 使用更快的 LLM (如 llama3.1:8b-q4)

## 备份与恢复

### 备份数据库

```bash
# 备份
docker-compose exec postgres pg_dump -U raguser ragdb > backup.sql

# 恢复
docker-compose exec -T postgres psql -U raguser ragdb < backup.sql
```

### 备份模型

```bash
# 打包模型文件
tar -czf bge-m3-backup.tar.gz models/bge-m3/

# 恢复
tar -xzf bge-m3-backup.tar.gz -C models/
```

## 升级指南

1. 备份数据和配置
2. 拉取最新代码
3. 重建镜像: `docker-compose build`
4. 重启服务: `docker-compose up -d`
5. 验证功能正常

## 性能调优

### 数据库优化

```sql
-- 调整向量索引参数
CREATE INDEX idx_chunks_embedding_optimized
ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 200);  -- 根据数据量调整

-- 定期 VACUUM
VACUUM ANALYZE chunks;
```

### API 优化

- 增加工作进程: `uvicorn workers`
- 启用缓存
- 使用连接池

### LLM 优化

- 调整 `temperature` 参数
- 减少 `num_predict` (生成长度)
- 使用量化模型
