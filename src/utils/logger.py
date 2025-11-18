"""
ロガー設定

Papersmith Agentで使用する統一的なロガー設定を提供します。
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "papersmith",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """ロガーをセットアップ

    Args:
        name: ロガー名
        level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: ログファイルパス（Noneの場合は標準出力のみ）
        format_string: カスタムフォーマット文字列

    Returns:
        設定済みのロガー
    """
    logger = logging.getLogger(name)

    # 既存のハンドラをクリア
    logger.handlers.clear()

    # ログレベル設定
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # フォーマット設定
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ（指定された場合）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 親ロガーへの伝播を防ぐ
    logger.propagate = False

    return logger


def get_logger(name: str = "papersmith") -> logging.Logger:
    """既存のロガーを取得

    Args:
        name: ロガー名

    Returns:
        ロガー（存在しない場合は新規作成）
    """
    logger = logging.getLogger(name)

    # ハンドラが設定されていない場合はデフォルト設定
    if not logger.handlers:
        return setup_logger(name)

    return logger
