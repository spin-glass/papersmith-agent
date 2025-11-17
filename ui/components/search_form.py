# -*- coding: utf-8 -*-
"""検索フォームコンポーネント

Requirements: 3.2
"""

import asyncio
from typing import Optional, Tuple

import httpx
import streamlit as st

from ui.config import api_config


async def search_papers(query: str, max_results: int) -> Optional[dict]:
    """論文を検索
    
    Args:
        query: 検索クエリ
        max_results: 最大取得件数
        
    Returns:
        検索結果（papers, count）またはNone
    """
    try:
        async with api_config.get_client() as client:
            response = await client.post(
                "/papers/search",
                json={"query": query, "max_results": max_results}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        st.error(f"❌ API接続エラー: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        return None


def render_search_form() -> Tuple[Optional[str], Optional[int], bool]:
    """検索フォームを表示
    
    Returns:
        (query, max_results, search_clicked): 検索クエリ、最大取得件数、検索ボタンがクリックされたか
    """
    st.header("検索設定")
    
    # キーワード入力
    query = st.text_input(
        "🔍 検索キーワード",
        placeholder="例: transformer attention mechanism",
        help="論文のタイトル、要約、著者名などで検索できます"
    )
    
    # 最大取得件数
    max_results = st.slider(
        "📊 最大取得件数",
        min_value=1,
        max_value=50,
        value=10,
        help="取得する論文の最大件数を指定します"
    )
    
    # 検索ボタン
    search_button = st.button("🔍 検索", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # ヘルプ
    with st.expander("💡 検索のヒント"):
        st.markdown("""
        **効果的な検索方法:**
        - 具体的なキーワードを使用
        - 複数のキーワードを組み合わせる
        - 英語で検索すると精度が向上
        
        **例:**
        - `transformer attention`
        - `deep learning computer vision`
        - `reinforcement learning robotics`
        """)
    
    return query, max_results, search_button


def execute_search(query: str, max_results: int) -> Optional[dict]:
    """検索を実行
    
    Args:
        query: 検索クエリ
        max_results: 最大取得件数
        
    Returns:
        検索結果またはNone
    """
    if not query.strip():
        st.warning("⚠️ 検索キーワードを入力してください")
        return None
    
    # 検索実行
    with st.spinner(f"🔍 '{query}' を検索中..."):
        result = asyncio.run(search_papers(query, max_results))
    
    if result:
        papers = result.get("papers", [])
        count = result.get("count", 0)
        
        if count == 0:
            st.info("📭 検索結果が見つかりませんでした。別のキーワードで試してください。")
            return None
        else:
            st.success(f"✅ {count}件の論文が見つかりました")
            return result
    
    return None
