# 企业知识库 RAG 服务 MVP - 分阶段交付方案

你是资深全栈工程师 + MLOps 工程师。我需要你帮我构建一个**离线可部署的企业知识库 RAG 服务**，采用**分阶段交付**策略。

## 🎯 项目目标
构建最小可验证原型（MVP），可在内网离线环境运行，支持：
- 文档摄取与向量化
- 基于检索的问答
- 基础可观测性
- 可复现部署

## 📋 固定技术栈
- **LLM**: Ollama + llama3.1:8b（本地推理）
- **Embedding**: bge-m3（离线加载）
- **向量数据库**: PostgreSQL + pgvector
- **后端**: FastAPI
- **前端**: Streamlit
- **监控**: Prometheus metrics（/metrics 端点）

---

## 🚀 第一阶段：核心骨架（请先完成这部分）

### 1.1 项目结构
请输出**完整目录树**，包含：
```
rag-mvp/
├── app/
│   ├── api/          # FastAPI 路由
│   ├── core/         # 配置、日志
│   ├── rag/          # 核心 RAG 逻辑
│   ├── db/           # 数据库模型
│   └── ui/           # Streamlit UI
├── data/raw/         # 原始文档
├── models/           # 离线模型存放
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

### 1.2 配置管理（app/core/config.py）
使用 Pydantic Settings，必须包含：
- `DATABASE_URL`
- `OLLAMA_URL`
- `EMBED_MODEL_PATH`
- `CHUNK_SIZE`, `CHUNK_OVERLAP`
- `TOP_K`, `SCORE_THRESHOLD`

### 1.3 数据库初始化（app/db/models.py + init.sql）
定义三张表：
1. **documents**: `doc_id, title, source_path, content_hash, created_at`
2. **chunks**: `chunk_id, doc_id, text, metadata(jsonb), embedding(vector), created_at`
3. **rag_feedback**: `id, question, answer, rating, created_at`

### 1.4 Docker Compose
包含服务：
- postgres（带 pgvector 扩展）
- api
- ui
- ollama（可选，注释说明可用本地 Ollama）

### 1.5 README.md
必须包含：
- 快速启动步骤（3-5 步）
- 模型文件放置说明
- 最小示例演示

**✅ 完成标准**：执行 `docker-compose up` 后，所有服务健康启动，API /health 返回 200。

---

## 🔄 第二阶段：核心功能（在我确认第一阶段后执行）

### 2.1 文档摄取（app/rag/ingest.py）
- CLI 命令：`python -m app.cli ingest --path data/raw`
- 支持 `.txt` 和 `.md` 文件
- 切分逻辑：保存 `chunk_id`, `doc_id`, `char_start`, `char_end`
- 错误处理：文件读取失败、embedding 失败、数据库写入失败

### 2.2 检索与生成（app/rag/query.py）
API 端点：`POST /query`
```json
{
  "question": "string",
  "top_k": 5,
  "filters": {"doc_id": "xxx"}  // 可选
}
```

响应：
```json
{
  "answer": "结构化答案，包含 [1][2] 引用",
  "citations": [
    {"chunk_id": "...", "snippet": "...", "score": 0.xx, "source_path": "..."}
  ],
  "refusal": null | "证据不足，建议..."
}
```

**关键逻辑**：
- 相似度检索（cosine）
- 证据不足判断（score < threshold 或 top_k < 3）
- Prompt 模板：强制基于引用回答
- Ollama 调用错误处理

### 2.3 Streamlit UI（app/ui/app.py）
两个页面：
1. **文档管理**：显示 data/raw 文件列表 + 一键 Ingest 按钮
2. **问答界面**：输入框 + 答案展示 + 引用卡片 + 反馈按钮（👍/👎）

**✅ 完成标准**：可通过 UI 上传文档、执行问答、看到引用来源。

---

## 📊 第三阶段：可观测性与评测（最后执行）

### 3.1 Prometheus Metrics（app/core/metrics.py）
在 `/metrics` 端点暴露：
- `rag_requests_total` (Counter)
- `rag_latency_seconds` (Histogram)
- `retrieval_no_results_total` (Counter)
- `llm_errors_total` (Counter)

### 3.2 评测框架（eval/）
- `golden_set.jsonl`：10 条示例问题
- `eval/run.py`：运行评测脚本
- 输出 `eval/report.json`：命中率、延迟、失败原因

**✅ 完成标准**：执行 `python -m eval.run` 后生成评测报告。

---

## ⚠️ 重要约束

### 必须遵守
1. **分文件输出**：每次只输出 3-5 个关键文件，等我确认后继续
2. **可运行优先**：代码必须能直接运行，不要伪代码或片段
3. **错误处理**：所有外部调用（DB、Ollama、文件 IO）必须有 try-except
4. **配置外置**：所有硬编码值必须可通过环境变量覆盖

### 简化原则
- **MVP 范围**：先做 .txt/.md，PDF/Docx 留扩展点
- **日志简化**：使用 Python logging，JSON 格式可选
- **文档最小化**：README 必须有，其他文档可后续补充

---

## 📝 执行流程

**第 1 步（现在开始）**：
请输出第一阶段的：
1. 完整目录树
2. `docker-compose.yml`
3. `app/core/config.py`
4. `app/db/models.py`
5. `.env.example`
6. `README.md`（快速启动部分）

输出后**暂停**，等待我确认后再继续第二阶段。

---

## ❓ 在开始前，请先确认

1. 你理解这是**分阶段交付**，不是一次性输出所有代码？
2. 你确认可以生成**完整可运行的代码**（不是伪代码）？
3. 对技术栈或需求有任何疑问吗？

请回复"已理解，开始第一阶段"并输出上述 6 个文件。