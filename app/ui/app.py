import streamlit as st
import httpx
import os
from typing import List, Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
st.set_page_config(
    page_title="企业知识库 RAG 系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "documents"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def api_request(method: str, endpoint: str, data: dict = None, params: dict = None):
    """Make API request."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        with httpx.Client(timeout=120.0) as client:
            if method == "GET":
                response = client.get(url, params=params)
            elif method == "POST":
                response = client.post(url, json=data)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        st.error(f"API 请求失败: {str(e)}")
        return None
    except httpx.HTTPStatusError as e:
        st.error(f"API 错误: {e.response.status_code}")
        return None


def documents_page():
    """Document management page."""
    st.title("📄 文档管理")

    # Ingest section
    st.subheader("文档摄取")
    col1, col2 = st.columns([3, 1])
    with col1:
        ingest_path = st.text_input(
            "文档目录路径",
            value="/app/data/raw",
            help="包含 .txt 和 .md 文件的目录路径"
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("🚀 开始摄取", type="primary"):
            with st.spinner("正在摄取文档..."):
                result = api_request("POST", "/ingest", data={"path": ingest_path})
                if result:
                    st.success(f"✅ 摄取完成!")
                    st.json(result)

    # Documents list
    st.subheader("已摄取文档")
    documents = api_request("GET", "/documents")
    if documents:
        for doc in documents:
            with st.expander(f"📄 {doc['title']}"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"**路径**: {doc['source_path']}")
                col2.write(f"**哈希**: {doc['content_hash'][:16]}...")
                col3.write(f"**创建时间**: {doc['created_at'][:10]}")
    else:
        st.info("暂无文档,请先执行文档摄取")


def query_page():
    """Query and answer page."""
    st.title("🔍 智能问答")

    # Query input
    with st.form("query_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            question = st.text_input(
                "输入问题",
                placeholder="例如: 这个系统有什么特点?",
                height=100
            )
        with col2:
            st.write("")
            top_k = st.number_input("检索数量", min_value=1, max_value=20, value=5)
            st.write("")
            submitted = st.form_submit_button("🔎 提问", type="primary", use_container_width=True)

    if submitted and question:
        with st.spinner("正在检索和生成答案..."):
            result = api_request(
                "POST",
                "/query",
                data={"question": question, "top_k": top_k}
            )

            if result:
                # Display refusal if any
                if result.get("refusal"):
                    st.warning(f"⚠️ {result['refusal']}")

                # Display answer
                if result.get("answer"):
                    st.markdown("### 📖 答案")
                    st.markdown(result["answer"])

                    # Feedback buttons
                    col1, col2, col3 = st.columns([1, 1, 8])
                    with col1:
                        if st.button("👍", key="thumbs_up"):
                            api_request("POST", "/feedback", data={
                                "question": question,
                                "answer": result["answer"],
                                "rating": 1
                            })
                            st.success("感谢反馈!")
                    with col2:
                        if st.button("👎", key="thumbs_down"):
                            api_request("POST", "/feedback", data={
                                "question": question,
                                "answer": result["answer"],
                                "rating": -1
                            })
                            st.success("感谢反馈!")

                # Display citations
                if result.get("citations"):
                    st.markdown("### 📚 引用来源")
                    for i, citation in enumerate(result["citations"], 1):
                        with st.expander(f"[{i}] {citation['title']} (相关度: {citation['score']:.2f})"):
                            st.markdown(f"**片段**: {citation['snippet']}")
                            st.caption(f"来源: {citation['source_path']}")


def main():
    """Main application."""
    # Sidebar
    with st.sidebar:
        st.title("📚 企业知识库 RAG")
        st.markdown("---")

        # Page navigation
        page = st.radio(
            "导航",
            ["📄 文档管理", "🔍 智能问答"],
            index=0 if st.session_state.page == "documents" else 1
        )
        st.session_state.page = "documents" if "文档管理" in page else "query"

        st.markdown("---")
        st.markdown("### 系统状态")
        health = api_request("GET", "/health")
        if health:
            st.success(f"✅ API: {health['status']}")
            st.success(f"✅ 数据库: {health['database']}")
        else:
            st.error("❌ 服务不可用")

        st.markdown("---")
        st.markdown("""
        **使用说明**:
        1. 先在"文档管理"中摄取文档
        2. 然后在"智能问答"中提问
        3. 查看答案和引用来源
        """)

    # Render selected page
    if st.session_state.page == "documents":
        documents_page()
    else:
        query_page()


if __name__ == "__main__":
    main()
