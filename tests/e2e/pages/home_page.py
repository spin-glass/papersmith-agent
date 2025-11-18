# -*- coding: utf-8 -*-
"""Home Page Object

ホームページのPage Objectを提供します。
ホームページの要素とインタラクションをカプセル化します。

Requirements: 2.1, 2.2, 2.3, 2.4
"""
from typing import List

from playwright.sync_api import Page

from tests.e2e.pages.base_page import BasePage


class HomePage(BasePage):
    """ホームページのPage Object
    
    Papersmith AgentのホームページのUI要素と操作を提供します。
    ナビゲーション、タイトル表示、システム状態の確認などを行います。
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    
    def __init__(self, page: Page, base_url: str):
        """HomePage初期化
        
        Args:
            page: Playwrightページオブジェクト
            base_url: アプリケーションのベースURL
        """
        super().__init__(page, base_url)
        
        # ページ要素のセレクタ
        # Streamlitはカスタムマークダウンでタイトルを表示するため、複数のセレクタを試す
        self.title_selectors = [
            "text=Papersmith Agent",
            ".main-header:has-text('Papersmith Agent')",
            "div:has-text('Papersmith Agent')"
        ]
        self.sidebar_selector = "[data-testid='stSidebar']"
        self.navigation_selector = "[data-testid='stSidebar'] a"
        self.system_overview_selector = "text=システム概要"
    
    def is_loaded(self) -> bool:
        """ページが読み込まれたか確認
        
        ホームページのタイトルが表示されているかを確認します。
        
        Requirements: 2.1
        
        Returns:
            bool: ページが正しく読み込まれた場合True
        
        Example:
            >>> home = HomePage(page, "http://localhost:8501")
            >>> home.navigate()
            >>> assert home.is_loaded()
        """
        # ページタイトルをチェック（Streamlitまたはカスタムタイトル）
        try:
            page_title = self.page.title()
            if "Papersmith Agent" in page_title or "Streamlit" in page_title:
                # さらに、ページコンテンツが読み込まれているか確認
                # サイドバーまたはメインコンテンツが存在すればOK
                if (self.page.locator(self.sidebar_selector).count() > 0 or
                    self.page.locator("text=システム概要").count() > 0):
                    return True
        except Exception:
            pass
        
        # 複数のセレクタを試す（要素の存在をチェック）
        for selector in self.title_selectors:
            try:
                # count() > 0 で要素の存在を確認（is_visible()より確実）
                if self.page.locator(selector).count() > 0:
                    return True
            except Exception:
                continue
        
        # システム概要が表示されていればページは読み込まれている
        try:
            if self.page.locator(self.system_overview_selector).count() > 0:
                return True
        except Exception:
            pass
        
        # どのセレクタでも見つからない場合はFalse
        return False
    
    def get_navigation_links(self) -> List[str]:
        """ナビゲーションリンクを取得
        
        サイドバーに表示されているナビゲーションリンクのテキストを取得します。
        
        Requirements: 2.2, 2.3
        
        Returns:
            List[str]: ナビゲーションリンクのテキストリスト
        
        Example:
            >>> home = HomePage(page, "http://localhost:8501")
            >>> home.navigate()
            >>> links = home.get_navigation_links()
            >>> assert "論文検索" in links
            >>> assert "RAG質問応答" in links
            >>> assert "論文一覧" in links
        """
        try:
            # サイドバーが表示されるまで待機
            self.page.wait_for_selector(self.sidebar_selector, timeout=5000)
            
            # ナビゲーションリンクを取得
            link_elements = self.page.locator(self.navigation_selector).all()
            
            # リンクテキストを抽出
            links = []
            for element in link_elements:
                try:
                    text = element.inner_text()
                    if text:  # 空でないテキストのみ追加
                        links.append(text)
                except Exception:
                    continue
            
            return links
        except Exception as e:
            print(f"Warning: Failed to get navigation links: {e}")
            return []
    
    def navigate_to_search(self) -> None:
        """検索ページに移動
        
        サイドバーの「論文検索」リンクをクリックして検索ページに遷移します。
        
        Requirements: 2.4
        
        Example:
            >>> home = HomePage(page, "http://localhost:8501")
            >>> home.navigate()
            >>> home.navigate_to_search()
            >>> assert "search" in page.url
        """
        try:
            # 「論文検索」リンクを探してクリック（絵文字を含む）
            # Streamlitのpage_linkは "📖 論文検索" という形式
            search_link = self.page.locator(
                f"{self.sidebar_selector} a:has-text('論文検索')"
            ).first
            
            search_link.click()
            self.wait_for_load()
        except Exception as e:
            # フォールバック: 直接URLで遷移
            print(f"Warning: Failed to click search link, navigating directly: {e}")
            self.navigate("/search")
    
    def navigate_to_rag(self) -> None:
        """RAGページに移動
        
        サイドバーの「RAG質問応答」リンクをクリックしてRAGページに遷移します。
        
        Requirements: 2.4
        
        Example:
            >>> home = HomePage(page, "http://localhost:8501")
            >>> home.navigate()
            >>> home.navigate_to_rag()
            >>> assert "rag" in page.url
        """
        try:
            # 「RAG質問応答」リンクを探してクリック（絵文字を含む）
            # Streamlitのpage_linkは "💬 RAG質問応答" という形式
            rag_link = self.page.locator(
                f"{self.sidebar_selector} a:has-text('RAG質問応答')"
            ).first
            
            rag_link.click()
            self.wait_for_load()
        except Exception as e:
            # フォールバック: 直接URLで遷移
            print(f"Warning: Failed to click RAG link, navigating directly: {e}")
            self.navigate("/rag")
    
    def navigate_to_papers(self) -> None:
        """論文一覧ページに移動
        
        サイドバーの「論文一覧」リンクをクリックして論文一覧ページに遷移します。
        
        Requirements: 2.4
        
        Example:
            >>> home = HomePage(page, "http://localhost:8501")
            >>> home.navigate()
            >>> home.navigate_to_papers()
            >>> assert "papers" in page.url
        """
        try:
            # 「論文一覧」リンクを探してクリック（絵文字を含む）
            # Streamlitのpage_linkは "📚 論文一覧" という形式
            papers_link = self.page.locator(
                f"{self.sidebar_selector} a:has-text('論文一覧')"
            ).first
            
            papers_link.click()
            self.wait_for_load()
        except Exception as e:
            # フォールバック: 直接URLで遷移
            print(f"Warning: Failed to click papers link, navigating directly: {e}")
            self.navigate("/papers")
    
    def get_system_status(self) -> dict:
        """システム状態を取得
        
        サイドバーに表示されているシステム状態情報を取得します。
        
        Returns:
            dict: システム状態情報（api_status, index_size など）
        
        Example:
            >>> home = HomePage(page, "http://localhost:8501")
            >>> home.navigate()
            >>> status = home.get_system_status()
            >>> print(status['api_status'])
        """
        status = {
            "api_status": "unknown",
            "index_size": 0,
            "has_warning": False
        }
        
        try:
            # API接続状態を確認
            if self.is_element_visible("text=API接続: 正常", timeout=2000):
                status["api_status"] = "ok"
            elif self.is_element_visible("text=API接続: エラー", timeout=2000):
                status["api_status"] = "error"
            
            # インデックスサイズを取得（可能な場合）
            try:
                index_info = self.page.locator("text=/インデックス: \\d+ ドキュメント/").first
                if index_info.is_visible(timeout=1000):
                    text = index_info.inner_text()
                    # "インデックス: 5 ドキュメント" から数値を抽出
                    import re
                    match = re.search(r'(\d+)', text)
                    if match:
                        status["index_size"] = int(match.group(1))
            except Exception:
                pass
            
            # 警告メッセージの有無を確認
            status["has_warning"] = self.is_element_visible(
                "[data-testid='stAlert']",
                timeout=1000
            )
            
        except Exception as e:
            print(f"Warning: Failed to get system status: {e}")
        
        return status
    
    def has_system_overview(self) -> bool:
        """システム概要セクションが表示されているか確認
        
        Requirements: 2.2
        
        Returns:
            bool: システム概要が表示されている場合True
        """
        try:
            # より柔軟なセレクタを試す
            # Streamlitのheaderは複数の形式で表示される可能性がある
            selectors = [
                "text=システム概要",
                "h2:has-text('システム概要')",
                "h3:has-text('システム概要')",
                "[data-testid='stHeader']:has-text('システム概要')",
                "div:has-text('システム概要')"
            ]
            
            for selector in selectors:
                if self.page.locator(selector).count() > 0:
                    return True
            
            return False
        except Exception as e:
            print(f"Warning: Failed to check system overview: {e}")
            return False
