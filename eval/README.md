# RAG 系统评测框架

## 概述

自动化评测工具,用于评估 RAG 系统的检索和生成质量。

## 使用方法

### 1. 准备测试数据

编辑 `eval/data/golden_set.jsonl`,每行一个测试问题:

```json
{
  "question": "测试问题",
  "expected_keywords": ["关键词1", "关键词2"],
  "category": "分类名称"
}
```

### 2. 运行评测

```bash
# 使用默认配置 (API: http://localhost:8000)
python -m eval.run

# 指定 API 地址
python -m eval.run http://localhost:8000

# 指定自定义数据集
python -m eval.run http://localhost:8000 eval/data/custom_set.jsonl

# 指定输出路径
python -m eval.run http://localhost:8000 eval/data/golden_set.jsonl eval/report.json
```

### 3. 查看报告

评测完成后会:
- 在控制台打印摘要报告
- 生成详细 JSON 报告到 `eval/report.json`

## 评测指标

- **成功率**: 生成有效答案的比例
- **关键词匹配率**: 答案中包含预期关键词的比例
- **平均延迟**: 查询响应时间
- **分类统计**: 按问题类别的成功率

## 报告示例

```json
{
  "total_questions": 10,
  "successful_queries": 8,
  "success_rate": 0.8,
  "avg_latency_seconds": 2.5,
  "avg_keyword_match_rate": 0.65,
  "categories": {
    "系统概述": {"total": 3, "success": 3},
    "技术实现": {"total": 4, "success": 3},
    "部署": {"total": 3, "success": 2}
  }
}
```

## 扩展

可以自定义评测逻辑:
- 修改 `eval/run.py` 中的成功判定标准
- 添加新的评测指标
- 集成第三方评测工具 (如 RAGAS)
