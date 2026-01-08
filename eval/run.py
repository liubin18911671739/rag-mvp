import json
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import httpx
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGEvaluator:
    """Evaluate RAG system performance using golden dataset."""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.results = []

    async def evaluate_single(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single question.

        Args:
            question_data: Dict with keys: question, expected_keywords, category

        Returns:
            Evaluation result dict
        """
        question = question_data["question"]
        expected_keywords = question_data["expected_keywords"]
        category = question_data["category"]

        logger.info(f"Evaluating: {question}")

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/query",
                    json={"question": question, "top_k": 5}
                )
                response.raise_for_status()
                result = response.json()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "question": question,
                "category": category,
                "status": "error",
                "error": str(e),
                "latency_seconds": time.time() - start_time
            }

        latency = time.time() - start_time
        answer = result.get("answer", "")
        refusal = result.get("refusal", "")
        citations = result.get("citations", [])

        # Check if answer contains expected keywords
        found_keywords = [kw for kw in expected_keywords if kw.lower() in answer.lower()]
        keyword_match_rate = len(found_keywords) / len(expected_keywords) if expected_keywords else 0

        # Determine success
        success = (
            not refusal and
            answer and
            keyword_match_rate >= 0.3  # At least 30% of keywords found
        )

        return {
            "question": question,
            "category": category,
            "status": "success" if success else "failure",
            "answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "refusal": refusal,
            "keyword_match_rate": keyword_match_rate,
            "found_keywords": found_keywords,
            "expected_keywords": expected_keywords,
            "num_citations": len(citations),
            "latency_seconds": latency,
            "top_score": citations[0]["score"] if citations else 0.0
        }

    async def run_evaluation(self, golden_set_path: str) -> Dict[str, Any]:
        """
        Run full evaluation on golden dataset.

        Args:
            golden_set_path: Path to golden_set.jsonl file

        Returns:
            Summary report dict
        """
        # Load golden set
        logger.info(f"Loading golden set from {golden_set_path}")
        questions = []
        with open(golden_set_path, 'r', encoding='utf-8') as f:
            for line in f:
                questions.append(json.loads(line.strip()))

        logger.info(f"Loaded {len(questions)} test questions")

        # Check API health
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/health")
                response.raise_for_status()
                logger.info("API is healthy")
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return {"error": "API not available", "details": str(e)}

        # Evaluate each question
        results = []
        for q in questions:
            result = await self.evaluate_single(q)
            results.append(result)
            time.sleep(0.5)  # Small delay between requests

        # Generate summary
        total = len(results)
        successful = sum(1 for r in results if r["status"] == "success")
        errors = sum(1 for r in results if r["status"] == "error")
        avg_latency = sum(r["latency_seconds"] for r in results) / total if total > 0 else 0
        avg_keyword_match = sum(r["keyword_match_rate"] for r in results if r["status"] != "error") / (total - errors) if (total - errors) > 0 else 0

        # Category-wise stats
        categories = {}
        for r in results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "success": 0}
            categories[cat]["total"] += 1
            if r["status"] == "success":
                categories[cat]["success"] += 1

        summary = {
            "evaluation_time": datetime.utcnow().isoformat(),
            "total_questions": total,
            "successful_queries": successful,
            "failed_queries": total - successful - errors,
            "error_queries": errors,
            "success_rate": successful / total if total > 0 else 0,
            "avg_latency_seconds": avg_latency,
            "avg_keyword_match_rate": avg_keyword_match,
            "categories": categories,
            "results": results
        }

        return summary

    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save evaluation report to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Report saved to {output_path}")

    def print_summary(self, report: Dict[str, Any]):
        """Print evaluation summary to console."""
        print("\n" + "="*60)
        print("RAG 系统评测报告")
        print("="*60)
        print(f"评测时间: {report['evaluation_time']}")
        print(f"总问题数: {report['total_questions']}")
        print(f"成功查询: {report['successful_queries']}")
        print(f"失败查询: {report['failed_queries']}")
        print(f"错误查询: {report['error_queries']}")
        print(f"成功率: {report['success_rate']:.2%}")
        print(f"平均延迟: {report['avg_latency_seconds']:.2f}s")
        print(f"平均关键词匹配率: {report['avg_keyword_match_rate']:.2%}")
        print("\n分类统计:")
        for cat, stats in report['categories'].items():
            rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
            print(f"  {cat}: {stats['success']}/{stats['total']} ({rate:.2%})")
        print("="*60 + "\n")


async def main():
    """Main evaluation entry point."""
    import sys

    # Configuration
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    golden_set_path = sys.argv[2] if len(sys.argv) > 2 else "eval/data/golden_set.jsonl"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "eval/report.json"

    logger.info(f"Starting evaluation with API: {api_url}")

    # Run evaluation
    evaluator = RAGEvaluator(api_base_url=api_url)
    report = await evaluator.run_evaluation(golden_set_path)

    # Print and save report
    if "error" not in report:
        evaluator.print_summary(report)
        evaluator.save_report(report, output_path)
        logger.info("Evaluation completed successfully")
    else:
        logger.error(f"Evaluation failed: {report['error']}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
