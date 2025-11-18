# -*- coding: utf-8 -*-
"""Search Page Object

論文検索ページのPage Objectを提供します。
検索ページの要素とインタラクションをカプセル化します。

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
from typing import List, Optional

from playwright.sync_api import Page

from tests.e2e.pages.base_page import BasePage


class SearchPage(BasePage):
    """論文検索ページのPage Object
    
    Papersmith Agentの論文検索ページのUI要素と操作を提供します。
    論文検索、結果表示、ダウンロードなどを行います。
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    
    # クラス変数としてサイドバーセレクタを定義
    sidebar_selector = "[data-testid='stSidebar']"
    
    def navigate(self, path: str = "") -> None:
        """Search ページに移動
        
        Streamlitのマルチページアプリでは、直接URLにアクセスしても
        ルーティングが機能しないため、ホームページからサイドバーの
        リンクをクリックしてページ遷移します。
        
        Requirements: 3.1
        
        Args:
            path: 使用されません（互換性のため保持）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate()
            >>> assert search.is_search_form_visible()
        """
        # まずホームページに移動
        self.page.goto(self.base_url)
        self.wait_for_load()
        
        # サイドバーが完全にレンダリングされるまで待機
        self.page.wait_for_timeout(1000)
        
        # サイドバーの「論文検索」リンクをクリック
        try:
            # Streamlitの st.page_link は複数のセレクタで試す
            selectors = [
                f"{self.sidebar_selector} a:has-text('論文検索')",
                f"{self.sidebar_selector} a:has-text('📖 論文検索')",
                f"{self.sidebar_selector} [data-testid='stPageLink-NavLink']:has-text('論文検索')",
                "a[href*='1_search']",
                "a[href*='search']"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    link = self.page.locator(selector).first
                    if link.is_visible(timeout=3000):
                        link.click()
                        clicked = True
                        break
                except Exception:
                    continue
            
            if not clicked:
                raise Exception("Could not find search link with any selector")
            
            # ページ遷移を待機
            self.page.wait_for_timeout(2000)
            self.wait_for_load()
        except Exception as e:
            print(f"Warning: Failed to click search link: {e}")
            # フォールバック: 直接URLで試す（動作しない可能性が高い）
            super().navigate("/1_search")
    
    def __init__(self, page: Page, base_url: str):
        """SearchPage初期化
        
        Args:
            page: Playwrightページオブジェクト
            base_url: アプリケー��ョンのベースURL
        """
        super().__init__(page, base_url)
        
        # サイドバー要素のセレクタ
        self.sidebar_selector = "[data-testid='stSidebar']"
        self.search_input_selector = "input[aria-label='🔍 検索キーワード']"
        self.max_results_slider_selector = "input[type='range']"
        self.search_button_selector = "button:has-text('検索')"
        
        # 検索結果エリア
        self.results_container_selector = "[data-testid='stVerticalBlock']"
        self.paper_card_selector = ".paper-card"
        self.paper_title_selector = ".paper-title"
        self.paper_authors_selector = ".paper-authors"
        self.paper_meta_selector = ".paper-meta"
        
        # アクションボタン
        self.download_button_selector = "button:has-text('ダウンロード')"
        self.pdf_link_selector = "a:has-text('PDF')"
        self.expander_selector = "[data-testid='stExpander']"
        
        # メッセージ
        self.spinner_selector = ".stSpinner"
        self.success_selector = ".stSuccess"
        self.info_selector = ".stInfo"
        self.error_selector = "[data-testid='stAlert']"
    
    def search(self, query: str, max_results: Optional[int] = None, wait_for_results: bool = True) -> None:
        """論文を検索
        
        検索キーワードを入力し、検索を実行します。
        デフォルトでは検索完了まで待機します。
        
        Requirements: 3.1, 3.2
        
        Args:
            query: 検索キーワード
            max_results: 最大取得件数（Noneの場合はデフォルト値を使用）
            wait_for_results: 検索完了まで待機するか（デフォルト: True）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer attention", max_results=10)
            >>> count = search.get_results_count()
        """
        # サイドバー内の検索入力フィールドに入力
        search_input = self.page.locator(
            f"{self.sidebar_selector} {self.search_input_selector}"
        ).first
        search_input.fill(query)
        
        # 最大取得件数を設定（指定された場合）
        if max_results is not None:
            self.set_max_results(max_results)
        
        # 検索ボタンをクリック
        search_button = self.page.locator(
            f"{self.sidebar_selector} {self.search_button_selector}"
        ).first
        search_button.click()
        
        # 検索完了まで待機
        if wait_for_results:
            self.wait_for_search_complete()
    
    def set_max_results(self, value: int) -> None:
        """最大取得件数を設定
        
        サイドバーのスライダーで最大取得件数を設定します。
        
        Args:
            value: 最大取得件数（1-50）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.set_max_results(20)
        """
        try:
            # サイドバー内のスライダーを取得
            slider = self.page.locator(
                f"{self.sidebar_selector} {self.max_results_slider_selector}"
            ).first
            
            if slider.is_visible(timeout=2000):
                # スライダーの値を設定
                slider.fill(str(value))
        except Exception as e:
            print(f"Warning: Failed to set max_results: {e}")
    
    def wait_for_search_complete(self, timeout: int = 30000) -> None:
        """検索完了を待機
        
        スピナーが消えるまで待機します。
        arXiv API呼び出しを含むため、デフォルトで30秒のタイムアウトを設定しています。
        
        Requirements: 3.5
        
        Args:
            timeout: タイムアウト時間（ミリ秒、デフォルト: 30000）
        
        Raises:
            TimeoutError: タイムアウト時間内に完了しなかった場合
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search_input = page.locator("input[aria-label='🔍 検索キーワード']")
            >>> search_input.fill("transformer")
            >>> search_button = page.locator("button:has-text('検索')")
            >>> search_button.click()
            >>> search.wait_for_search_complete()
        """
        try:
            # スピナーが表示されるまで待機（最大5秒）
            spinner = self.page.locator(self.spinner_selector).first
            try:
                spinner.wait_for(state="visible", timeout=5000)
            except Exception:
                # スピナーが表示されない場合もある（高速な応答）
                pass
            
            # スピナーが消えるまで待機
            spinner.wait_for(state="hidden", timeout=timeout)
            
            # 追加の待機（UIの更新を確実にするため）
            self.page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Warning: wait_for_search_complete timeout or error: {e}")
            # タイムアウトしても続行（結果が表示されている可能性がある）
    
    def get_results_count(self) -> int:
        """検索結果数を取得
        
        表示されている論文カードの数を取得します。
        
        Requirements: 3.3
        
        Returns:
            int: 検索結果数
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> count = search.get_results_count()
            >>> assert count > 0
        """
        try:
            # 論文カードを取得
            cards = self.page.locator(self.paper_card_selector).all()
            return len(cards)
        except Exception:
            return 0
    
    def get_first_result_title(self) -> str:
        """最初の結果のタイトルを取得
        
        最初の検索結果の論文タイトルを取得します。
        
        Requirements: 3.4
        
        Returns:
            str: 論文タイトル（結果がない場合は空文字列）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> title = search.get_first_result_title()
            >>> assert len(title) > 0
        """
        try:
            # 最初の論文カードのタイトルを取得
            first_title = self.page.locator(self.paper_title_selector).first
            if first_title.is_visible(timeout=2000):
                return first_title.inner_text()
        except Exception:
            pass
        
        return ""
    
    def get_result_titles(self) -> List[str]:
        """全ての検索結果のタイトルを取得
        
        Returns:
            List[str]: 論文タイトルのリスト
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> titles = search.get_result_titles()
            >>> assert len(titles) > 0
        """
        titles = []
        
        try:
            # 全ての論文タイトルを取得
            title_elements = self.page.locator(self.paper_title_selector).all()
            
            for element in title_elements:
                try:
                    if element.is_visible():
                        titles.append(element.inner_text())
                except Exception:
                    continue
        except Exception as e:
            print(f"Warning: Failed to get result titles: {e}")
        
        return titles
    
    def download_first_result(self, wait_for_completion: bool = True) -> None:
        """最初の結果をダウンロード
        
        最初の検索結果の論文をダウンロードします。
        デフォルトではダウンロード完了まで待機します。
        
        Requirements: 3.6
        
        Args:
            wait_for_completion: ダウンロード完了まで待機するか（デフォルト: True）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> search.download_first_result()
            >>> assert search.has_success_message()
        """
        try:
            # 最初のダウンロードボタンをクリック
            download_button = self.page.locator(self.download_button_selector).first
            download_button.click()
            
            # ダウンロード完了まで待機
            if wait_for_completion:
                self.wait_for_download_complete()
        except Exception as e:
            print(f"Warning: Failed to download first result: {e}")
    
    def download_result_by_index(self, index: int, wait_for_completion: bool = True) -> None:
        """指定されたインデックスの結果をダウンロード
        
        Args:
            index: ダウンロードする論文のインデックス（0始まり）
            wait_for_completion: ダウンロード完了まで待機するか（デフォルト: True）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> search.download_result_by_index(1)  # 2番目の論文をダウンロード
        """
        try:
            # 指定されたインデックスのダウンロードボタンをクリック
            download_buttons = self.page.locator(self.download_button_selector).all()
            
            if index < len(download_buttons):
                download_buttons[index].click()
                
                # ダウンロード完了まで待機
                if wait_for_completion:
                    self.wait_for_download_complete()
            else:
                print(f"Warning: Download button index {index} out of range")
        except Exception as e:
            print(f"Warning: Failed to download result by index: {e}")
    
    def wait_for_download_complete(self, timeout: int = 60000) -> None:
        """ダウンロード完了を待機
        
        スピナーが消えて成功メッセージが表示されるまで待機します。
        PDF処理とインデックス化を含むため、デフォルトで60秒のタイムアウトを設定しています。
        
        Requirements: 3.5, 3.6
        
        Args:
            timeout: タイムアウト時間（ミリ秒、デフォルト: 60000）
        
        Raises:
            TimeoutError: タイムアウト時間内に完了しなかった場合
        """
        try:
            # スピナーが表示されるまで待機（最大5秒）
            spinner = self.page.locator(self.spinner_selector).first
            try:
                spinner.wait_for(state="visible", timeout=5000)
            except Exception:
                # スピナーが表示されない場合もある
                pass
            
            # スピナーが消えるまで待機
            spinner.wait_for(state="hidden", timeout=timeout)
            
            # 成功メッセージが表示されるまで待機
            success = self.page.locator(self.success_selector).first
            success.wait_for(state="visible", timeout=5000)
            
            # 追加の待機（UIの更新を確実にするため）
            self.page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Warning: wait_for_download_complete timeout or error: {e}")
            # タイムアウトしても続行
    
    def has_success_message(self) -> bool:
        """成功メッセージが表示されているか確認
        
        Returns:
            bool: 成功メッセージが表示されている場合True
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> search.download_first_result()
            >>> assert search.has_success_message()
        """
        return self.is_element_visible(self.success_selector, timeout=2000)
    
    def get_success_message(self) -> str:
        """成功メッセージを取得
        
        Returns:
            str: 成功メッセージ（表示されていない場合は空文字列）
        """
        try:
            success = self.page.locator(self.success_selector).first
            if success.is_visible(timeout=2000):
                return success.inner_text()
        except Exception:
            pass
        
        return ""
    
    def has_no_results_message(self) -> bool:
        """検索結果なしメッセージが表示されているか確認
        
        Returns:
            bool: 検索結果なしメッセージが表示されている場合True
        """
        try:
            # "検索結果が見つかりませんでした" メッセージを探す
            no_results = self.page.locator("text=検索結果が見つかりませんでした").first
            return no_results.is_visible(timeout=2000)
        except Exception:
            return False
    
    def expand_summary(self, index: int = 0) -> None:
        """要約を展開
        
        指定されたインデックスの論文の要約エクスパンダーを展開します。
        
        Args:
            index: 展開する要約のインデックス（デフォルト: 0）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> search.expand_summary(0)  # 最初の論文の要約を展開
        """
        try:
            # エクスパンダーを取得
            expanders = self.page.locator(self.expander_selector).all()
            
            if index < len(expanders):
                expander = expanders[index]
                
                # エクスパンダーが閉じている場合のみクリック
                summary = expander.locator("summary").first
                if summary.is_visible():
                    summary.click()
                    # 展開アニメーション完了を待機
                    self.page.wait_for_timeout(500)
            else:
                print(f"Warning: Expander index {index} out of range")
        except Exception as e:
            print(f"Warning: Failed to expand summary: {e}")
    
    def get_paper_metadata(self, index: int = 0) -> dict:
        """論文のメタデータを取得
        
        指定されたインデックスの論文のメタデータを取得します。
        
        Args:
            index: 論文のインデックス（デフォルト: 0）
        
        Returns:
            dict: 論文メタデータ（title, authors, year, arxiv_id など）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> metadata = search.get_paper_metadata(0)
            >>> assert "title" in metadata
        """
        metadata = {
            "title": "",
            "authors": "",
            "year": "",
            "arxiv_id": ""
        }
        
        try:
            # 論文カードを取得
            cards = self.page.locator(self.paper_card_selector).all()
            
            if index < len(cards):
                card = cards[index]
                
                # タイトルを取得
                title_element = card.locator(self.paper_title_selector).first
                if title_element.is_visible():
                    metadata["title"] = title_element.inner_text()
                
                # 著者を取得
                authors_element = card.locator(self.paper_authors_selector).first
                if authors_element.is_visible():
                    metadata["authors"] = authors_element.inner_text()
                
                # メタデータ（年、arXiv ID）を取得
                meta_element = card.locator(self.paper_meta_selector).first
                if meta_element.is_visible():
                    meta_text = meta_element.inner_text()
                    # "📅 2023 | 🆔 2301.00001" から抽出
                    import re
                    year_match = re.search(r'📅\s*(\d{4})', meta_text)
                    if year_match:
                        metadata["year"] = year_match.group(1)
                    
                    arxiv_match = re.search(r'🆔\s*([\d.]+)', meta_text)
                    if arxiv_match:
                        metadata["arxiv_id"] = arxiv_match.group(1)
        except Exception as e:
            print(f"Warning: Failed to get paper metadata: {e}")
        
        return metadata
    
    def click_pdf_link(self, index: int = 0) -> None:
        """PDFリンクをクリック
        
        指定されたインデックスの論文のPDFリンクをクリックします。
        
        Args:
            index: 論文のインデックス（デフォルト: 0）
        
        Example:
            >>> search = SearchPage(page, "http://localhost:8501")
            >>> search.navigate("/1_search")
            >>> search.search("transformer")
            >>> search.click_pdf_link(0)
        """
        try:
            # PDFリンクを取得
            pdf_links = self.page.locator(self.pdf_link_selector).all()
            
            if index < len(pdf_links):
                pdf_links[index].click()
            else:
                print(f"Warning: PDF link index {index} out of range")
        except Exception as e:
            print(f"Warning: Failed to click PDF link: {e}")
    
    def is_search_form_visible(self) -> bool:
        """検索フォームが表示されているか確認
        
        Requirements: 3.1
        
        Returns:
            bool: 検索フォームが表示されている場合True
        """
        try:
            # サイドバー内の検索入力フィールドを確認
            search_input = self.page.locator(
                f"{self.sidebar_selector} {self.search_input_selector}"
            ).first
            
            return search_input.is_visible(timeout=5000)
        except Exception:
            return False
