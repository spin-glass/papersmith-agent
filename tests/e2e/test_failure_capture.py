# -*- coding: utf-8 -*-
"""Test to verify automatic failure capture

This test intentionally fails to verify that the automatic
screenshot and log capture works correctly.

Requirements: 8.3, 8.4, 10.1, 10.2, 10.3
"""
import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.skip(reason="Intentional failure test - only run manually to verify capture")
def test_intentional_failure(page: Page):
    """テスト失敗時に自動キャプチャが動作することを確認
    
    このテストは意図的に失敗し、自動キャプチャ機能をテストします。
    通常のテスト実行では@pytest.mark.skipでスキップされます。
    
    手動で実行する場合:
    uv run pytest tests/e2e/test_failure_capture.py::test_intentional_failure -v --no-cov -s
    
    Requirements: 8.3, 8.4, 10.1, 10.2, 10.3
    """
    # テストページに移動
    page.goto("https://example.com")
    
    # 意図的に失敗させる
    assert False, "This is an intentional failure to test capture functionality"
