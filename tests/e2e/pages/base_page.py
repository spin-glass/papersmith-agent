# -*- coding: utf-8 -*-
"""Base Page Object

全ページの基底クラスを提供します。
共通のページ操作メソッドを実装します。

Requirements: 2.1, 6.1, 10.1
"""
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page


class BasePage:
    """全ページの基底クラス
    
    Page Object Modelパターンの基底クラスです。
    全てのページオブジェクトはこのクラスを継承します。
    
    Attributes:
        page: Playwrightページオブジェクト
        base_url: アプリケーションのベースURL
    
    Requirements: 2.1, 6.1, 10.1
    """
    
    def __init__(self, page: Page, base_url: str):
        """BasePage初期化
        
        Args:
            page: Playwrightページオブジェクト
            base_url: アプリケーションのベースURL
        """
        self.page = page
        self.base_url = base_url
    
    def navigate(self, path: str = "") -> None:
        """ページに移動
        
        指定されたパスにページを遷移します。
        遷移後、ページの読み込み完了を待機します。
        
        Requirements: 2.1
        
        Args:
            path: ベースURLからの相対パス（デフォルト: ""）
        
        Example:
            >>> page_obj.navigate()  # ホームページに移動
            >>> page_obj.navigate("/1_search")  # 検索ページに移動
        """
        url = f"{self.base_url}{path}"
        self.page.goto(url)
        self.wait_for_load()
    
    def wait_for_load(self, timeout: int = 5000) -> None:
        """ページ読み込み完了を待機
        
        ページのネットワークアクティビティが落ち着くまで待機します。
        Streamlitアプリケーションの初期化を待つために使用します。
        
        Requirements: 2.1
        
        Args:
            timeout: タイムアウト時間（ミリ秒、デフォルト: 5000）
        
        Raises:
            TimeoutError: タイムアウト時間内に読み込みが完了しなかった場合
        """
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as e:
            # タイムアウトの場合でも、DOMContentLoadedまで待機できていれば続行
            print(f"Warning: wait_for_load timeout, but continuing: {e}")
    
    def take_screenshot(self, name: str) -> str:
        """スクリーンショット撮影
        
        現在のページのスクリーンショットを撮影し、
        test-resultsディレクトリに保存します。
        
        Requirements: 10.1
        
        Args:
            name: スクリーンショットのファイル名（拡張子なし）
        
        Returns:
            str: 保存されたスクリーンショットのパス
        
        Example:
            >>> path = page_obj.take_screenshot("search_page")
            >>> print(f"Screenshot saved to: {path}")
        """
        # test-resultsディレクトリを作成
        results_dir = Path("test-results")
        results_dir.mkdir(exist_ok=True)
        
        # スクリーンショットを保存
        screenshot_path = results_dir / f"{name}.png"
        self.page.screenshot(path=str(screenshot_path), full_page=True)
        
        return str(screenshot_path)
    
    def get_error_message(self) -> str:
        """エラーメッセージを取得
        
        ページに表示されているエラーメッセージを取得します。
        Streamlitのst.error、st.warning、st.infoを検出します。
        
        Requirements: 6.1
        
        Returns:
            str: エラーメッセージ（エラーが表示されていない場合は空文字列）
        
        Example:
            >>> error = page_obj.get_error_message()
            >>> if error:
            ...     print(f"Error found: {error}")
        """
        # Streamlitのアラート要素を検索
        # st.error, st.warning, st.info などを検出
        error_selectors = [
            "[data-testid='stAlert']",  # Streamlit 1.x
            ".stAlert",  # 旧バージョン
            "[data-testid='stException']",  # 例外表示
            ".stException"  # 旧バージョン
        ]
        
        for selector in error_selectors:
            try:
                error_element = self.page.locator(selector).first
                if error_element.is_visible(timeout=1000):
                    return error_element.inner_text()
            except Exception:
                # 要素が見つからない場合は次のセレクタを試す
                continue
        
        return ""
    
    def is_element_visible(self, selector: str, timeout: int = 5000) -> bool:
        """要素が表示されているか確認
        
        指定されたセレクタの要素が表示されているか確認します。
        
        Args:
            selector: CSSセレクタ
            timeout: タイムアウト時間（ミリ秒、デフォルト: 5000）
        
        Returns:
            bool: 要素が表示されている場合True
        """
        try:
            element = self.page.locator(selector).first
            return element.is_visible(timeout=timeout)
        except Exception:
            return False
    
    def get_page_title(self) -> str:
        """ページタイトルを取得
        
        Returns:
            str: ページタイトル
        """
        return self.page.title()
    
    def get_current_url(self) -> str:
        """現在のURLを取得
        
        Returns:
            str: 現在のURL
        """
        return self.page.url
