"""エラーハンドリングユーティリティ

Requirements: 3.5
"""

from collections.abc import Callable
from typing import Any, Optional

import httpx
import streamlit as st


class ErrorHandler:
    """エラーハンドリングクラス"""

    @staticmethod
    def handle_api_error(error: Exception, context: str = "") -> None:
        """API呼び出しエラーを処理

        Args:
            error: 発生した例外
            context: エラーのコンテキスト（どの処理で発生したか）
        """
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code

            # 503エラー（インデックス未準備）
            if status_code == 503:
                st.warning(
                    "⚠️ システムが準備中です\n\n"
                    "インデックスの構築が完了していません。\n"
                    "しばらく待ってから再度お試しください。"
                )
                return

            # 404エラー
            if status_code == 404:
                st.error(
                    f"❌ リソースが見つかりません\n\n"
                    f"{context}が見つかりませんでした。"
                )
                return

            # 400エラー（不正なリクエスト）
            if status_code == 400:
                try:
                    error_detail = error.response.json().get("detail", "不正なリクエストです")
                except:
                    error_detail = "不正なリクエストです"

                st.error(
                    f"❌ リクエストエラー\n\n"
                    f"{error_detail}"
                )
                return

            # 500エラー（サーバーエラー）
            if status_code >= 500:
                try:
                    error_detail = error.response.json().get("detail", "サーバーでエラーが発生しました")
                except:
                    error_detail = "サーバーでエラーが発生しました"

                st.error(
                    f"❌ サーバーエラー\n\n"
                    f"{error_detail}\n\n"
                    f"しばらく待ってから再度お試しください。"
                )
                return

            # その他のHTTPエラー
            st.error(
                f"❌ HTTPエラー (ステータスコード: {status_code})\n\n"
                f"{context}中にエラーが発生しました。"
            )

        elif isinstance(error, httpx.ConnectError):
            st.error(
                "❌ API接続エラー\n\n"
                "FastAPI サーバーに接続できません。\n"
                "サーバーが起動しているか確認してください。\n\n"
                "**確認事項:**\n"
                "- Docker コンテナが起動しているか\n"
                "- API URL が正しいか (デフォルト: http://localhost:8000)"
            )

        elif isinstance(error, httpx.TimeoutException):
            st.error(
                "❌ タイムアウトエラー\n\n"
                f"{context}の処理に時間がかかりすぎています。\n\n"
                "**考えられる原因:**\n"
                "- LLM推論に時間がかかっている\n"
                "- 大量のデータを処理している\n"
                "- ネットワークが不安定\n\n"
                "しばらく待ってから再度お試しください。"
            )

        elif isinstance(error, httpx.HTTPError):
            st.error(
                f"❌ ネットワークエラー\n\n"
                f"{context}中にネットワークエラーが発生しました。\n"
                f"エラー詳細: {str(error)}"
            )

        else:
            # その他の予期しないエラー
            st.error(
                f"❌ 予期しないエラー\n\n"
                f"{context}中にエラーが発生しました。\n"
                f"エラー詳細: {str(error)}"
            )

    @staticmethod
    def with_error_handling(
        func: Callable,
        context: str = "",
        success_message: Optional[str] = None
    ) -> Optional[Any]:
        """エラーハンドリング付きで関数を実行

        Args:
            func: 実行する関数
            context: エラーのコンテキスト
            success_message: 成功時のメッセージ（オプション）

        Returns:
            関数の戻り値、またはエラー時はNone
        """
        try:
            result = func()
            if success_message:
                st.success(success_message)
            return result
        except Exception as e:
            ErrorHandler.handle_api_error(e, context)
            return None


class LoadingState:
    """ローディング状態管理クラス"""

    @staticmethod
    def spinner(message: str):
        """スピナーを表示

        Args:
            message: 表示するメッセージ
        """
        return st.spinner(message)

    @staticmethod
    def progress_bar(total: int, current: int, message: str = ""):
        """プログレスバーを表示

        Args:
            total: 総数
            current: 現在の進捗
            message: 表示するメッセージ
        """
        progress = current / total if total > 0 else 0
        st.progress(progress, text=f"{message} ({current}/{total})")

    @staticmethod
    def status_message(message: str, icon: str = "⏳"):
        """ステータスメッセージを表示

        Args:
            message: 表示するメッセージ
            icon: アイコン
        """
        return st.status(f"{icon} {message}", expanded=True)


def validate_input(value: str, field_name: str, min_length: int = 1) -> bool:
    """入力値を検証

    Args:
        value: 検証する値
        field_name: フィールド名
        min_length: 最小文字数

    Returns:
        検証結果（True: 有効、False: 無効）
    """
    if not value or not value.strip():
        st.warning(f"⚠️ {field_name}を入力してください")
        return False

    if len(value.strip()) < min_length:
        st.warning(f"⚠️ {field_name}は{min_length}文字以上で入力してください")
        return False

    return True
