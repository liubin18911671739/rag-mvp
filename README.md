# 企业知识库 RAG 服务 MVP

离线可部署的企业级检索增强生成(RAG)服务,基于本地 LLM 和向量搜索。

## 技术栈

- **LLM**: Ollama + llama3.1:8b (本地推理)
- **Embedding**: bge-m3 (离线加载)
- **向量数据库**: PostgreSQL 16 + pgvector
- **后端**: FastAPI
- **前端**: Streamlit
- **监控**: Prometheus metrics

## 快速启动

### 前置要求

1. **安装 Docker 和 Docker Compose**
2. **准备 Ollama 环境** (二选一):
   - 方式 A: 本地运行 Ollama (推荐)
     ```bash
     # macOS/Linux
     curl -fsSL https://ollama.com/install.sh | sh

     # 拉取模型
     ollama pull llama3.1:8b
     ```

   - 方式 B: 使用 Docker 运行 Ollama
     - 取消 `docker-compose.yml` 中 `ollama` 服务的注释
     - 启动后会自动拉取模型

3. **下载 Embedding 模型**:
   ```bash
   # 从 HuggingFace 下载 bge-m3 模型
   # 下载地址: https://huggingface.co/BAAI/bge-m3
   # 解压后放置到 models/bge-m3/ 目录
   ```

### 启动步骤

1. **复制环境变量配置**:
   ```bash
   cp .env.example .env
   ```

2. **配置 Ollama URL** (根据部署方式):
   ```bash
   # 使用本地 Ollama
   OLLAMA_URL=http://host.docker.internal:11434

   # 使用 Docker Ollama
   OLLAMA_URL=http://ollama:11434
   ```

3. **启动所有服务**:
   ```bash
   docker-compose up -d
   ```

4. **验证服务状态**:
   ```bash
   # 检查 API 健康状态
   curl http://localhost:8000/health

   # 检查数据库连接
   docker-compose exec postgres pg_isready

   # 查看服务日志
   docker-compose logs -f api
   ```

5. **访问应用**:
   - Streamlit UI: http://localhost:8501
   - API 文档: http://localhost:8000/docs
   - Metrics: http://localhost:8000/metrics

## 最小示例演示

### 1. 准备测试文档

```bash
# 创建测试文档
echo "企业知识库系统是一个基于检索增强生成的问答系统。
该系统使用本地大语言模型,可在内网离线环境部署。
系统支持文档自动切分、向量化存储和语义检索。" > data/raw/test.txt
```

### 2. 执行文档摄取

```bash
# 通过 API 上传文档 (后续阶段实现)
curl -X POST http://localhost:8000/ingest \
  -F "file=@data/raw/test.txt"

# 或通过 CLI 命令 (后续阶段实现)
docker-compose exec api python -m app.cli ingest --path /app/data/raw
```

### 3. 执行问答查询

```bash
# 通过 API 问答 (后续阶段实现)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "这个系统有什么特点?",
    "top_k": 3
  }'
```

### 4. 通过 UI 交互

1. 打开浏览器访问 http://localhost:8501
2. 在"文档管理"页面点击"Ingest"上传文档
3. 切换到"问答"页面输入问题
4. 查看答案和引用来源,点击👍/👎提供反馈

## 项目结构

```
rag-mvp/
├── app/
│   ├── api/          # FastAPI 路由
│   ├── core/         # 配置、日志
│   ├── rag/          # RAG 核心逻辑
│   ├── db/           # 数据库模型
│   └── ui/           # Streamlit UI
├── data/raw/         # 原始文档
├── models/           # 离线模型存放
├── scripts/          # 初始化脚本
├── eval/             # 评测框架
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

## 常见问题

### Q: 如何使用本地已有的 Ollama?

A: 编辑 `.env` 文件,设置:
```bash
OLLAMA_URL=http://host.docker.internal:11434
```

### Q: 如何更换 Embedding 模型?

A: 1. 下载新模型到 `models/` 目录
   2. 修改 `.env` 中的 `EMBED_MODEL_PATH`
   3. 如果维度不同,需要修改数据库 schema 和 SQL 索引

### Q: 数据库连接失败怎么办?

A: 检查以下几点:
1. PostgreSQL 容器是否正常运行: `docker-compose ps`
2. 环境变量配置是否正确
3. 查看数据库日志: `docker-compose logs postgres`

### Q: 如何查看系统监控指标?

A: 访问 http://localhost:8000/metrics 查看 Prometheus 格式的指标数据

## 开发进度

- [x] 第一阶段: 核心骨架 (数据库、配置、Docker)
- [ ] 第二阶段: 核心功能 (文档摄取、检索问答、UI)
- [ ] 第三阶段: 可观测性与评测

## License

MIT
# rag-mvp
