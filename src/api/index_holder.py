# -*- coding: utf-8 -*-
"""InMemoryIndexHolder - Chromaインデックスのシングルトンホルダー

Requirements: 8.1, 8.2, 8.4
"""

import asyncio
import logging
from typing import Optional

from src.clients.chroma_client import ChromaClient

logger = logging.getLogger(__name__)


class InMemoryIndexHolder:
    """Chromaインデックスのシングルトンホルダー
    
    アプリケーション起動時にChromaインデックスをロードし、
    全エンドポイントで共有するためのシングルトンクラス。
    asyncio.Lockで排他制御を行い、スレッドセーフな操作を保証する。
    
    Requirements:
    - 8.1: システム起動時にChromaインデックスをロード
    - 8.2: インデックスロード中は503ステータスコードを返す
    - 8.4: InMemoryIndexHolderを通じてアクセスを提供
    """
    
    _instance: Optional['InMemoryIndexHolder'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls) -> 'InMemoryIndexHolder':
        """シングルトンパターンの実装
        
        Returns:
            InMemoryIndexHolderのシングルトンインスタンス
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初期化
        
        シングルトンのため、初回のみ初期化を実行する。
        """
        if not self._initialized:
            self._index: Optional[ChromaClient] = None
            self._instance_lock = asyncio.Lock()
            self._initialized = True
            logger.info("InMemoryIndexHolder initialized")
    
    async def set(self, index: ChromaClient) -> None:
        """インデックスを設定
        
        Args:
            index: ChromaClientインスタンス
        
        Requirements: 8.1
        """
        async with self._instance_lock:
            self._index = index
            logger.info(
                f"Index set: collection='{index.config.collection_name}', "
                f"documents={index.count()}"
            )
    
    async def get(self) -> ChromaClient:
        """インデックスを取得
        
        Returns:
            ChromaClientインスタンス
        
        Raises:
            RuntimeError: インデックスが未準備の場合（503エラーに対応）
        
        Requirements: 8.2, 8.4
        """
        async with self._instance_lock:
            if self._index is None:
                raise RuntimeError(
                    "Index not ready. Please wait for initialization to complete."
                )
            return self._index
    
    def is_ready(self) -> bool:
        """インデックスが利用可能かチェック
        
        Returns:
            True: インデックスが利用可能
            False: インデックスが未準備
        
        Requirements: 8.2
        """
        return self._index is not None
    
    def size(self) -> int:
        """インデックス内のドキュメント数を取得
        
        Returns:
            ドキュメント数（インデックスが未準備の場合は0）
        
        Requirements: 8.4
        """
        if self._index is None:
            return 0
        
        try:
            return self._index.count()
        except Exception as e:
            logger.error(f"Failed to get index size: {e}")
            return 0
    
    async def reset(self) -> None:
        """インデックスをリセット
        
        主にテストや管理用途で使用。
        """
        async with self._instance_lock:
            if self._index is not None:
                logger.warning("Resetting index")
                self._index = None
            else:
                logger.info("Index already empty, nothing to reset")


# グローバルシングルトンインスタンス
index_holder = InMemoryIndexHolder()
