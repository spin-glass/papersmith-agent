# -*- coding: utf-8 -*-
"""Papersmith Agent - Streamlit UI メインアプリケーション

Requirements: 3.1
"""

import asyncio

import httpx
import streamlit as st

from ui.config import api_config
from ui.utils.error_handler import ErrorHandler, LoadingState


# ページ設定
st.set_page_config(
    page_title="Papersmith Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    .status-ok {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


async def check_api_health():
    """FastAPI ヘルスチェック
    
    Returns:
        dict: ヘルスチェック結果
    """
    try:
        async with api_config.get_client() as client:
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {"status": "error", "error": "API接続エラー: サーバーに接続できません"}
    except httpx.TimeoutException:
        return {"status": "error", "error": "タイムアウト: サーバーの応答がありません"}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            return {"status": "error", "error": "サービス準備中: インデックスを構築しています"}
        return {"status": "error", "error": f"HTTPエラー ({e.response.status_code})"}
    except Exception as e:
        return {"status": "error", "error": f"予期しないエラー: {str(e)}"}


def main():
    """メインアプリケーション"""
    
    # ヘッダー
    st.markdown('<div class="main-header">📚 Papersmith Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">完全ローカルで動作する自律型論文解析エージェントシステム</div>',
        unsafe_allow_html=True
    )
    
    # サイドバー
    with st.sidebar:
        st.title("ナビゲーション")
        st.markdown("---")
        
        # API接続状態
        st.subheader("システム状態")
        
        # ヘルスチェックを実行
        health_status = asyncio.run(check_api_health())
        
        if health_status.get("status") == "ok":
            st.markdown(
                f'<span class="status-ok">✓ API接続: 正常</span>',
                unsafe_allow_html=True
            )
            st.info(f"インデックス: {health_status.get('index_size', 0)} ドキュメント")
            
            if not health_status.get("index_ready", False):
                st.warning("⚠️ インデックス構築中...")
        else:
            st.markdown(
                f'<span class="status-error">✗ API接続: エラー</span>',
                unsafe_allow_html=True
            )
            error_msg = health_status.get("error", "不明なエラー")
            st.error(f"エラー: {error_msg}")
        
        st.markdown("---")
        
        # ページリンク
        st.subheader("機能")
        st.page_link("pages/1_search.py", label="📖 論文検索", icon="📖")
        st.page_link("pages/2_rag.py", label="💬 RAG質問応答", icon="💬")
        st.page_link("pages/3_papers.py", label="📚 論文一覧", icon="📚")
        
        st.markdown("---")
        st.caption(f"API URL: {api_config.base_url}")
    
    # メインコンテンツ
    st.header("システム概要")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3>📖 論文検索</h3>
            <p>arXiv APIを使用してキーワードで論文を検索し、PDFをダウンロードしてインデックス化します。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-box">
            <h3>💬 RAG質問応答</h3>
            <p>インデックス化された論文に対して質問を投げかけ、LLMが関連情報を基に回答を生成します。</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3>📚 論文一覧</h3>
            <p>インデックス化された論文の一覧を表示し、詳細情報を確認できます。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-box">
            <h3>🔍 ベクター検索</h3>
            <p>Chromaベクターストアを使用した高速な意味検索を実現します。</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 使い方
    st.header("使い方")
    
    st.markdown("""
    ### 1. 論文を検索してダウンロード
    左サイドバーから「📖 論文検索」を選択し、キーワードで論文を検索します。
    検索結果から興味のある論文をダウンロードしてインデックス化します。
    
    ### 2. 質問を投げかける
    「💬 RAG質問応答」ページで、インデックス化された論文に対して質問を入力します。
    LLMが関連する情報を検索し、回答を生成します。
    
    ### 3. 論文を管理
    「📚 論文一覧」ページで、インデックス化された論文の一覧を確認できます。
    """)
    
    # 技術スタック
    st.header("技術スタック")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **バックエンド**
        - FastAPI
        - Python 3.11
        - Docker
        """)
    
    with col2:
        st.markdown("""
        **AI/ML**
        - HuggingFace Transformers
        - ELYZA-JP-8B (LLM)
        - multilingual-e5-base (Embedding)
        """)
    
    with col3:
        st.markdown("""
        **データ**
        - ChromaDB (ベクターストア)
        - arXiv API
        - PyPDF (PDF処理)
        """)
    
    # フッター
    st.markdown("---")
    st.caption("Papersmith Agent v1.0.0 - 完全ローカルで動作する論文解析システム")


if __name__ == "__main__":
    main()
