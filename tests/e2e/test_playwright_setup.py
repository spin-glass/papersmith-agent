# -*- coding: utf-8 -*-
"""
Playwright環境セットアップの検証テスト
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.ui
def test_playwright_basic_functionality(page: Page):
    """Playwrightの基本機能が動作することを確認"""
    # Google にアクセス
    page.goto("https://www.google.com")
    
    # タイトルに "Google" が含まれることを確認
    expect(page).to_have_title("Google")
    
    # ページが正しく読み込まれたことを確認
    assert page.url.startswith("https://www.google.com")


@pytest.mark.e2e
@pytest.mark.ui
def test_playwright_chromium_browser(browser):
    """Chromiumブラウザが正しく起動することを確認"""
    # ブラウザの種類を確認
    assert browser.browser_type.name == "chromium"
    
    # 新しいページを作成できることを確認
    page = browser.new_page()
    assert page is not None
    page.close()
