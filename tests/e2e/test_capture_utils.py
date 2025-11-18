# -*- coding: utf-8 -*-
"""Tests for capture utilities

Requirements: 8.3, 8.4, 10.1, 10.2, 10.3
"""
import json
from pathlib import Path

import pytest
from playwright.sync_api import Page

from tests.e2e.utils.capture import (
    capture_on_failure,
    save_console_logs,
    save_network_logs,
)


@pytest.mark.e2e
@pytest.mark.ui
def test_capture_on_failure(page: Page):
    """capture_on_failure関数が正しく動作する
    
    Requirements: 8.3, 8.4, 10.1, 10.2, 10.3
    """
    # テストページに移動
    page.goto("https://example.com")
    
    # キャプチャを実行
    result = capture_on_failure(page, "test_capture")
    
    # 結果を検証
    assert "screenshot" in result
    assert "console_log" in result
    assert "network_log" in result
    
    # ファイルが作成されたことを確認
    screenshot_path = Path(result["screenshot"])
    console_log_path = Path(result["console_log"])
    network_log_path = Path(result["network_log"])
    
    assert screenshot_path.exists()
    assert console_log_path.exists()
    assert network_log_path.exists()
    
    # スクリーンショットがPNGファイルであることを確認
    assert screenshot_path.suffix == ".png"
    assert screenshot_path.stat().st_size > 0
    
    # コンソールログが読み取れることを確認
    with open(console_log_path, "r", encoding="utf-8") as f:
        console_content = f.read()
        assert len(console_content) > 0
        assert "Page Title:" in console_content
        assert "Page URL:" in console_content
    
    # ネットワークログがJSONとして読み取れることを確認
    with open(network_log_path, "r", encoding="utf-8") as f:
        network_data = json.load(f)
        assert isinstance(network_data, list)
        assert len(network_data) > 0
    
    # クリーンアップ
    screenshot_path.unlink()
    console_log_path.unlink()
    network_log_path.unlink()


@pytest.mark.e2e
@pytest.mark.ui
def test_save_console_logs(page: Page, tmp_path: Path):
    """save_console_logs関数が正しく動作する
    
    Requirements: 10.2
    """
    # テストページに移動
    page.goto("https://example.com")
    
    # ログを保存
    log_path = tmp_path / "console.log"
    logs = save_console_logs(page, str(log_path))
    
    # 結果を検証
    assert isinstance(logs, list)
    assert len(logs) > 0
    
    # ファイルが作成されたことを確認
    assert log_path.exists()
    
    # ファイル内容を確認
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Page Title:" in content
        assert "Page URL:" in content


@pytest.mark.e2e
@pytest.mark.ui
def test_save_network_logs(page: Page, tmp_path: Path):
    """save_network_logs関数が正しく動作する
    
    Requirements: 10.3
    """
    # テストページに移動
    page.goto("https://example.com")
    
    # ネットワークログを保存
    log_path = tmp_path / "network.json"
    logs = save_network_logs(page, str(log_path))
    
    # 結果を検証
    assert isinstance(logs, list)
    assert len(logs) > 0
    
    # ファイルが作成されたことを確認
    assert log_path.exists()
    
    # ファイル内容を確認
    with open(log_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0
