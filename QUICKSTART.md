# 快速开始指南

## 5 分钟快速启动

### 步骤 1: 准备 Ollama

```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull llama3.1:8b
ollama serve
```

### 步骤 2: 下载 Embedding 模型

```bash
# 创建模型目录
mkdir -p models/bge-m3

# 从 HuggingFace 下载 bge-m3
# 访问: https://huggingface.co/BAAI/bge-m3
# 下载所有文件到 models/bge-m3/
```

### 步骤 3: 配置并启动

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env,设置本地 Ollama 地址
echo "OLLAMA_URL=http://host.docker.internal:11434" >> .env

# 启动所有服务
docker-compose up -d

# 等待服务启动(约 30 秒)
docker-compose logs -f api
```

### 步骤 4: 验证服务

```bash
# 检查健康状态
curl http://localhost:8000/health

# 应返回: {"status":"healthy","database":"connected"}
```

### 步骤 5: 访问 UI

打开浏览器访问: http://localhost:8501

## 第一次使用

### 1. 摄取文档

系统已包含示例文档,或者添加你自己的文档:

```bash
# 将文档放到 data/raw/ 目录
cp your-document.txt data/raw/

# 通过 UI 摄取
# 在"文档管理"页面点击"🚀 开始摄取"
```

### 2. 提问测试

在"智能问答"页面尝试这些问题:
- "企业知识库系统是什么?"
- "系统支持哪些文档格式?"
- "如何部署这个系统?"
- "系统使用什么技术栈?"

### 3. 查看指标

访问 http://localhost:8000/metrics 查看 Prometheus 指标

## 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看日志
docker-compose logs -f api
docker-compose logs -f ui

# 重启某个服务
docker-compose restart api

# 进入容器调试
docker-compose exec api bash
docker-compose exec postgres psql -U raguser -d ragdb

# 查看数据库
docker-compose exec postgres psql -U raguser -d ragdb -c "SELECT COUNT(*) FROM documents;"
```

## 故障排除

### 问题 1: API 无法连接

```bash
# 检查容器状态
docker-compose ps

# 检查 API 日志
docker-compose logs api
```

### 问题 2: Ollama 连接失败

确认 `.env` 中设置:
```bash
# 本地 Ollama
OLLAMA_URL=http://host.docker.internal:11434

# 或 Docker Ollama
OLLAMA_URL=http://ollama:11434
```

### 问题 3: 模型加载失败

确认:
1. 模型文件完整下载到 `models/bge-m3/`
2. 目录权限正确
3. 容器可以访问挂载的 models 目录

### 问题 4: 查询无结果

可能原因:
- 文档未摄取:检查 `/api/documents`
- 相似度阈值过高:降低 `SCORE_THRESHOLD`
- 问题不相关:提供更明确的问题

## 下一步

- 📖 阅读 [API 文档](API.md) 了解所有接口
- 🚀 查看 [部署指南](DEPLOYMENT.md) 进行生产部署
- 📊 运行 `python -m eval.run` 执行系统评测
- 🔧 根据 [部署指南](DEPLOYMENT.md) 进行性能调优

## 获取帮助

遇到问题?
1. 查看日志: `docker-compose logs`
2. 检查配置: 确认 `.env` 文件
3. 查看文档: README.md, API.md, DEPLOYMENT.md
