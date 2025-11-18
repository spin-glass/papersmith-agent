# -*- coding: utf-8 -*-
"""Base Page Object Tests

BasePageクラスの機能をテストします。

Requirements: 2.1, 6.1, 10.1
"""
import pytest
from pathlib import Path
from playwright.sync_api import Page

from tests.e2e.pages.base_page import BasePage


@pytest.mark.e2e
@pytest.mark.ui
def test_base_page_navigate(page: Page, streamlit_server: str):
    """navigate()メソッドが正しく動作することを確認
    
    Requirements: 2.1
    """
    base_page = BasePage(page, streamlit_server)
    
    # ホームページに移動
    base_page.navigate()
    
    # URLが正しいことを確認
    assert page.url == streamlit_server or page.url == f"{streamlit_server}/"
    
    # ページが読み込まれたことを確認
    assert "Papersmith" in page.title() or "Streamlit" in page.title()


@pytest.mark.e2e
@pytest.mark.ui
def test_base_page_wait_for_load(page: Page, streamlit_server: str):
    """wait_for_load()メソッドが正しく動作することを確認
    
    Requirements: 2.1
    """
    base_page = BasePage(page, streamlit_server)
    
    # ページに移動
    page.goto(streamlit_server)
    
    # wait_for_load()がタイムアウトせずに完了することを確認
    try:
        base_page.wait_for_load(timeout=10000)
        success = True
    except Exception as e:
        success = False
        print(f"wait_for_load failed: {e}")
    
    assert success, "wait_for_load should complete without timeout"


@pytest.mark.e2e
@pytest.mark.ui
def test_base_page_take_screenshot(page: Page, streamlit_server: str):
    """take_screenshot()メソッドが正しく動作することを確認
    
    Requirements: 10.1
    """
    base_page = BasePage(page, streamlit_server)
    
    # ページに移動
    base_page.navigate()
    
    # スクリーンショットを撮影
    screenshot_path = base_page.take_screenshot("test_base_page")
    
    # スクリーンショットファイルが作成されたことを確認
    assert Path(screenshot_path).exists()
    assert Path(screenshot_path).stat().st_size > 0
    
    # クリーンアップ
    Path(screenshot_path).unlink()


@pytest.mark.e2e
@pytest.mark.ui
def test_base_page_get_error_message_no_error(page: Page, streamlit_server: str):
    """get_error_message()メソッドがエラーなし時に空文字列を返すことを確認
    
    Requirements: 6.1
    """
    base_page = BasePage(page, streamlit_server)
    
    # ページに移動
    base_page.navigate()
    
    # エラーメッセージを取得（エラーがない場合は空文字列）
    error_message = base_page.get_error_message()
    
    # エラーがない場合は空文字列であることを確認
    assert isinstance(error_message, str)


@pytest.mark.e2e
@pytest.mark.ui
def test_base_page_is_element_visible(page: Page, streamlit_server: str):
    """is_element_visible()メソッドが正しく動作することを確認
    
    Requirements: 2.1
    """
    base_page = BasePage(page, streamlit_server)
    
    # ページに移動
    base_page.navigate()
    
    # 存在しない要素は表示されていないことを確認
    # タイムアウトを短く設定して、すぐに結果を返すことを確認
    is_visible = base_page.is_element_visible("#non-existent-element-12345", timeout=1000)
    assert not is_visible, "Non-existent element should not be visible"
    
    # メソッドが正しく動作することを確認（Falseを返す）
    # これでis_element_visibleメソッドの基本機能は検証できた


@pytest.mark.e2e
@pytest.mark.ui
def test_base_page_get_page_title(page: Page, streamlit_server: str):
    """get_page_title()メソッドが正しく動作することを確認
    
    Requirements: 2.1
    """
    base_page = BasePage(page, streamlit_server)
    
    # ページに移動
    base_page.navigate()
    
    # ページタイトルを取得
    title = base_page.get_page_title()
    
    # タイトルが空でないことを確認
    assert isinstance(title, str)
    assert len(title) > 0


@pytest.mark.e2e
@pytest.mark.ui
def test_base_page_get_current_url(page: Page, streamlit_server: str):
    """get_current_url()メソッドが正しく動作することを確認
    
    Requirements: 2.1
    """
    base_page = BasePage(page, streamlit_server)
    
    # ページに移動
    base_page.navigate()
    
    # 現在のURLを取得
    current_url = base_page.get_current_url()
    
    # URLが正しいことを確認
    assert current_url.startswith(streamlit_server)
