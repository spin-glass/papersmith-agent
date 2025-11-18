# -*- coding: utf-8 -*-
"""E2E Test Fixtures

共通のテストフィクスチャを提供します。
- FastAPIサーバーの起動・停止
- Streamlitサーバーの起動・停止
- Playwrightページオブジェクト
- テストデータ

Requirements: 1.5, 9.1, 9.2
"""
import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Page, Playwright

from tests.e2e.utils.server import cleanup_test_data, wait_for_server


@pytest.fixture(scope="session")
def fastapi_server() -> Generator[str, None, None]:
    """FastAPIサーバーを起動
    
    セッションスコープでFastAPIサーバーを起動し、
    全テスト終了後に停止します。
    
    Requirements: 1.5
    
    Yields:
        str: FastAPI base URL
    """
    # テスト用環境変数を設定
    env = os.environ.copy()
    env["CHROMA_PERSIST_DIR"] = "./data/test_chroma"
    env["CACHE_DIR"] = "./cache/test"
    
    # FastAPIサーバーを起動
    process = subprocess.Popen(
        ["uv", "run", "uvicorn", "src.api.main:app", "--port", "8000", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    try:
        # サーバー起動を待機
        wait_for_server("http://127.0.0.1:8000/health", timeout=60)
        print("✓ FastAPI server started successfully")
        
        yield "http://127.0.0.1:8000"
        
    finally:
        # サーバーを停止
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("✓ FastAPI server stopped")


@pytest.fixture(scope="session")
def streamlit_server(fastapi_server: str) -> Generator[str, None, None]:
    """Streamlitサーバーを起動
    
    セッションスコープでStreamlitサーバーを起動し、
    全テスト終了後に停止します。
    
    Requirements: 1.5
    
    Args:
        fastapi_server: FastAPI base URL (依存関係)
    
    Yields:
        str: Streamlit base URL
    """
    # テスト用環境変数を設定
    env = os.environ.copy()
    env["API_BASE_URL"] = fastapi_server
    
    # PYTHONPATHにプロジェクトルートを追加（uiモジュールのインポートのため）
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_root}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = project_root
    
    # Streamlitサーバーを起動
    process = subprocess.Popen(
        [
            "uv", "run", "streamlit", "run", "ui/app.py",
            "--server.port", "8501",
            "--server.address", "127.0.0.1",
            "--server.headless", "true"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=project_root  # カレントディレクトリをプロジェクトルートに設定
    )
    
    try:
        # サーバー起動を待機
        wait_for_server("http://127.0.0.1:8501", timeout=60)
        print("✓ Streamlit server started successfully")
        
        yield "http://127.0.0.1:8501"
        
    finally:
        # サーバーを停止
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("✓ Streamlit server stopped")


@pytest.fixture
def page(playwright: Playwright, streamlit_server: str, request) -> Generator[Page, None, None]:
    """Playwrightページオブジェクト
    
    各テストで新しいブラウザコンテキストとページを作成します。
    テスト終了後に自動的にクリーンアップします。
    テスト失敗時には自動的にスクリーンショットとログを保存します。
    
    Requirements: 1.5, 8.3, 8.4, 10.1, 10.2, 10.3
    
    Args:
        playwright: Playwright instance (pytest-playwrightが提供)
        streamlit_server: Streamlit base URL (依存関係)
        request: pytest request object (テスト情報取得用)
    
    Yields:
        Page: Playwright page object
    """
    # ブラウザを起動
    browser = playwright.chromium.launch(
        headless=True,
        slow_mo=0  # デバッグ時は500-1000に設定
    )
    
    # コンテキストを作成
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="ja-JP",
        timezone_id="Asia/Tokyo"
    )
    
    # ページを作成
    page = context.new_page()
    
    # コンソールログを収集
    console_messages = []
    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
    
    # エラーログを記録
    page.on("pageerror", lambda err: print(f"Page error: {err}"))
    
    # ページオブジェクトにコンソールメッセージを保存
    page.console_messages = console_messages  # type: ignore
    
    yield page
    
    # テスト失敗時にキャプチャを保存
    if request.node.rep_call.failed if hasattr(request.node, 'rep_call') else False:
        from tests.e2e.utils.capture import capture_on_failure
        test_name = request.node.name
        try:
            capture_on_failure(page, test_name)
            print(f"✓ Captured failure artifacts for {test_name}")
        except Exception as e:
            print(f"✗ Failed to capture artifacts: {e}")
    
    # クリーンアップ
    page.close()
    context.close()
    browser.close()


@pytest.fixture
def test_data() -> dict:
    """テスト用モックデータ
    
    各テストで使用する共通のテストデータを提供します。
    
    Requirements: 9.1, 9.2
    
    Returns:
        dict: テストデータ
    """
    return {
        "search_query": "machine learning",
        "rag_question": "この論文の主な貢献は何ですか？",
        "mock_papers": [
            {
                "arxiv_id": "2301.00001",
                "title": "Test Paper 1: Machine Learning Advances",
                "authors": ["Author A", "Author B"],
                "year": 2023,
                "summary": "This paper presents advances in machine learning."
            },
            {
                "arxiv_id": "2301.00002",
                "title": "Test Paper 2: Deep Learning Applications",
                "authors": ["Author C", "Author D"],
                "year": 2023,
                "summary": "This paper explores deep learning applications."
            }
        ]
    }


@pytest.fixture(scope="session", autouse=True)
def cleanup_before_tests():
    """テスト実行前のクリーンアップ
    
    テスト開始前にテスト用データをクリーンアップします。
    
    Requirements: 9.2, 9.3
    """
    print("\n=== Cleaning up test data before tests ===")
    cleanup_test_data()
    yield
    print("\n=== Cleaning up test data after tests ===")
    cleanup_test_data()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """テスト結果をキャプチャするためのフック
    
    テストの実行結果をitemに保存し、
    page fixtureでテスト失敗時の処理に使用します。
    
    Requirements: 8.3, 8.4, 10.1
    """
    # テスト実行
    outcome = yield
    rep = outcome.get_result()
    
    # テスト結果をitemに保存
    setattr(item, f"rep_{rep.when}", rep)
