# -*- coding: utf-8 -*-
"""
カスタム例外クラス

Papersmith Agentで使用するカスタム例外を定義します。
"""


class PapersmithError(Exception):
    """Papersmith Agent基底例外クラス"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class APIError(PapersmithError):
    """外部API関連エラー
    
    arXiv、CrossRef、Semantic Scholar APIとの通信エラー時に使用
    """
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None, details: dict = None):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(message, details)


class IndexNotReadyError(PapersmithError):
    """インデックス未準備エラー
    
    Chromaインデックスがまだロードされていない、または初期化中の場合に使用
    """
    
    def __init__(self, message: str = "インデックスが準備できていません。しばらくお待ちください。", details: dict = None):
        super().__init__(message, details)


class LLMError(PapersmithError):
    """LLM推論エラー
    
    LLMモデルのロード、推論、生成時のエラーに使用
    """
    
    def __init__(self, message: str, model_name: str = None, details: dict = None):
        self.model_name = model_name
        super().__init__(message, details)
