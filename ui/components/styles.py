"""共通スタイル定義

Requirements: 3.1
"""

import streamlit as st


def apply_common_styles():
    """共通CSSスタイルを適用"""
    st.markdown("""
    <style>
        /* 論文カードスタイル */
        .paper-card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            border-left: 4px solid #1f77b4;
            margin-bottom: 1rem;
        }
        .paper-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 0.5rem;
        }
        .paper-authors {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        .paper-meta {
            color: #888;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }
        .paper-summary {
            color: #333;
            font-size: 0.9rem;
            margin-top: 0.5rem;
            line-height: 1.5;
        }

        /* RAG回答スタイル */
        .answer-box {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #e8f4f8;
            border-left: 4px solid #1f77b4;
            margin-bottom: 1.5rem;
        }
        .answer-title {
            font-size: 1.1rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 0.5rem;
        }
        .answer-text {
            color: #333;
            font-size: 1rem;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        /* 参照元チャンクスタイル */
        .source-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            border-left: 3px solid #6c757d;
            margin-bottom: 0.8rem;
        }
        .source-text {
            color: #555;
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 0.5rem;
        }
        .source-meta {
            color: #888;
            font-size: 0.8rem;
        }

        /* 質問ボックススタイル */
        .question-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            margin-bottom: 1rem;
        }

        /* メッセージスタイル */
        .success-message {
            color: #28a745;
            font-weight: bold;
        }
        .error-message {
            color: #dc3545;
            font-weight: bold;
        }
        .info-message {
            color: #17a2b8;
            font-weight: bold;
        }

        /* バッジスタイル */
        .score-badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 0.3rem;
            background-color: #28a745;
            color: white;
            font-size: 0.75rem;
            font-weight: bold;
        }
        .stat-badge {
            display: inline-block;
            padding: 0.3rem 0.6rem;
            border-radius: 0.3rem;
            background-color: #17a2b8;
            color: white;
            font-size: 0.85rem;
            font-weight: bold;
            margin-right: 0.5rem;
        }

        /* 論文一覧カードスタイル */
        .paper-list-card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            border-left: 4px solid #28a745;
            margin-bottom: 1rem;
        }
        .paper-list-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #28a745;
            margin-bottom: 0.5rem;
        }
        .paper-list-authors {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        .paper-list-meta {
            color: #888;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }

        /* 空の状態スタイル */
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #6c757d;
        }
        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }

        /* ヘッダースタイル */
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

        /* フィーチャーボックススタイル */
        .feature-box {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f0f2f6;
            margin-bottom: 1rem;
        }

        /* ステータススタイル */
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
