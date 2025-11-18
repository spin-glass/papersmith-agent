"""UI設定とFastAPI接続設定

Requirements: 3.1
"""

import os

import httpx


class APIConfig:
    """FastAPI接続設定"""

    def __init__(self):
        self.base_url = os.getenv("PAPERSMITH_API_URL", "http://localhost:8000")
        self.timeout = 300.0  # LLM処理は時間がかかるため長めに設定

    def get_client(self) -> httpx.AsyncClient:
        """httpxクライアントを取得"""
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )


# グローバル設定インスタンス
api_config = APIConfig()
