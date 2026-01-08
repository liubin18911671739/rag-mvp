# API 文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`

## 端点列表

### 1. 健康检查

检查 API 和数据库连接状态。

**请求**:
```
GET /health
```

**响应** (200 OK):
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. RAG 查询

执行检索增强生成查询。

**请求**:
```
POST /api/query
Content-Type: application/json

{
  "question": "企业知识库系统是什么?",
  "top_k": 5,
  "filters": {
    "doc_id": "xxx-xxx-xxx"  // 可选
  }
}
```

**参数**:
- `question` (string, required): 用户问题
- `top_k` (integer, optional): 检索的文档块数量 (1-20)
- `filters` (object, optional): 过滤条件,目前支持 `doc_id`

**响应** (200 OK):
```json
{
  "answer": "企业知识库系统是一个基于检索增强生成的问答系统...[1][2]",
  "citations": [
    {
      "chunk_id": "xxx",
      "snippet": "文档片段内容",
      "score": 0.85,
      "source_path": "/app/data/raw/doc1.txt",
      "title": "doc1",
      "metadata": {
        "chunk_index": 0,
        "char_start": 0,
        "char_end": 512
      }
    }
  ],
  "refusal": null
}
```

**失败响应** (证据不足):
```json
{
  "answer": "",
  "citations": [],
  "refusal": "相关度不足,无法基于现有文档生成可靠答案。"
}
```

### 3. 文档摄取

摄取指定目录下的所有文档。

**请求**:
```
POST /api/ingest
Content-Type: multipart/form-data

path: /app/data/raw
```

**参数**:
- `path` (string, required): 文档目录路径

**响应** (200 OK):
```json
{
  "total": 10,
  "succeeded": 8,
  "failed": 2,
  "errors": [
    "file1.txt: 读取失败",
    "file2.txt: 空文件"
  ]
}
```

**支持的文件格式**:
- `.txt` - 纯文本文件
- `.md` - Markdown 文件

### 4. 文档列表

获取所有已摄取的文档列表。

**请求**:
```
GET /api/documents
```

**响应** (200 OK):
```json
[
  {
    "doc_id": "xxx-xxx-xxx",
    "title": "文档标题",
    "source_path": "/app/data/raw/doc1.txt",
    "content_hash": "abc123...",
    "created_at": "2024-01-01T12:00:00"
  }
]
```

### 5. 提交反馈

提交用户反馈,用于质量监控。

**请求**:
```
POST /api/feedback
Content-Type: multipart/form-data

question: "用户的问题"
answer: "生成的答案"
rating: 1
```

**参数**:
- `question` (string, required): 原始问题
- `answer` (string, required): 生成的答案
- `rating` (integer, required): 反馈评分
  - `1` - 👍 (满意)
  - `-1` - 👎 (不满意)

**响应** (200 OK):
```json
{
  "status": "success",
  "message": "Feedback recorded"
}
```

### 6. Prometheus 指标

获取 Prometheus 格式的监控指标。

**请求**:
```
GET /metrics
```

**响应** (200 OK):
```
# HELP rag_requests_total Total number of RAG requests
# TYPE rag_requests_total counter
rag_requests_total{status="success"} 42
rag_requests_total{status="failure"} 3

# HELP rag_latency_seconds RAG request latency in seconds
# TYPE rag_latency_seconds histogram
rag_latency_seconds_bucket{operation="query",le="0.1"} 0
rag_latency_seconds_bucket{operation="query",le="0.5"} 5
...
```

## 错误响应

所有错误端点返回以下格式:

```json
{
  "detail": "错误描述信息"
}
```

**常见 HTTP 状态码**:
- `400` - 请求参数错误
- `500` - 服务器内部错误
- `503` - 服务不可用

## 使用示例

### Python

```python
import httpx

async def query_rag(question: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/query",
            json={"question": question, "top_k": 5}
        )
        return response.json()

result = query_rag("系统有什么特点?")
print(result["answer"])
```

### cURL

```bash
# 查询
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "测试问题"}'

# 摄取文档
curl -X POST http://localhost:8000/api/ingest \
  -F "path=/app/data/raw"

# 查看文档
curl http://localhost:8000/api/documents
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    question: '测试问题',
    top_k: 5
  })
});
const data = await response.json();
console.log(data.answer);
```

## 速率限制

当前版本未实现速率限制,生产环境建议使用 Nginx 或 API Gateway 添加。

## 认证

当前版本未实现认证,生产环境建议添加 API Key 或 OAuth2。
