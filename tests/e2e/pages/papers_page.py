# -*- coding: utf-8 -*-
"""Papers Page Object

論文一覧ページのPage Objectを提供します。
論文一覧ページの要素とインタラクションをカプセル化します。

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""
from typing import List, Optional

from playwright.sync_api import Page

from tests.e2e.pages.base_page import BasePage


class PapersPage(BasePage):
    """論文一覧ページのPage Object
    
    Papersmith Agentの論文一覧ページのUI要素と操作を提供します。
    インデックス化された論文の一覧表示、メタデータ確認などを行います。
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def navigate(self, path: str = "") -> None:
        """Papers ページに移動
        
        Streamlitのマルチページアプリでは、直接URLにアクセスしても
        ルーティングが機能しないため、ホームページからサイドバーの
        リンクをクリックしてページ遷移します。
        
        Requirements: 5.1
        
        Args:
            path: 使用されません（互換性のため保持）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate()
            >>> assert papers.is_loaded()
        """
        # まずホームページに移動
        self.page.goto(self.base_url)
        self.wait_for_load()
        
        # サイドバーが完全にレンダリングされるまで待機
        self.page.wait_for_timeout(1000)
        
        # サイドバーの「論文一覧」リンクをクリック
        try:
            # Streamlitの st.page_link は複数のセレクタで試す
            selectors = [
                "[data-testid='stSidebar'] a:has-text('論文一覧')",
                "[data-testid='stSidebar'] a:has-text('📚 論文一覧')",
                "[data-testid='stSidebar'] [data-testid='stPageLink-NavLink']:has-text('論文一覧')",
                "a[href*='3_papers']",
                "a[href*='papers']"
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
                raise Exception("Could not find papers link with any selector")
            
            # ページ遷移を待機
            self.page.wait_for_timeout(2000)
            self.wait_for_load()
        except Exception as e:
            print(f"Warning: Failed to click papers link: {e}")
            # フォールバック: 直接URLで試す（動作しない可能性が高い）
            super().navigate("/3_papers")
    
    def __init__(self, page: Page, base_url: str):
        """PapersPage初期化
        
        Args:
            page: Playwrightページオブジェクト
            base_url: アプリケーションのベースURL
        """
        super().__init__(page, base_url)
        
        # ページ要素のセレクタ
        self.page_title_selector = "text=📚 論文一覧"
        self.sidebar_papers_link_selector = "[data-testid='stSidebar'] a:has-text('論文一覧')"
        
        # 論文カード
        self.paper_card_selector = ".paper-list-card"
        self.paper_title_selector = ".paper-list-title"
        self.paper_authors_selector = ".paper-list-authors"
        self.paper_meta_selector = ".paper-list-meta"
        self.paper_stats_selector = ".paper-list-stats"
        
        # 空の状態
        self.empty_state_selector = ".empty-state"
        self.empty_state_message_selector = "text=インデックス化された論文がありません"
        
        # サイドバー要素
        self.sidebar_selector = "[data-testid='stSidebar']"
        self.index_stats_selector = ".stMetric"
        self.refresh_button_selector = "button:has-text('🔄 リフレッシュ')"
        
        # ソート・フィルター
        self.sort_selector = "select"
        
        # 成功メッセージ
        self.success_selector = ".stSuccess"
        
        # 詳細エクスパンダー
        self.expander_selector = "[data-testid='stExpander']"
        
        # PDFリンク
        self.pdf_link_selector = "a:has-text('🔗 PDF')"
    
    def is_loaded(self) -> bool:
        """ページが読み込まれたか確認
        
        論文一覧ページのタイトルが表示されているかを確認します。
        
        Requirements: 5.1
        
        Returns:
            bool: ページが正しく読み込まれた場合True
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> assert papers.is_loaded()
        """
        # Streamlitのマルチページアプリでは、ページ遷移後もURLが変わらないことがある
        # そのため、ページ固有の要素の存在で判定する
        
        try:
            # ページタイトルをチェック
            page_title = self.page.title()
            if "論文一覧" in page_title:
                return True
        except Exception:
            pass
        
        # URLで確認（Streamlitの新しいバージョンでは /papers になる）
        try:
            current_url = self.page.url
            if "3_papers" in current_url or "/papers" in current_url:
                return True
        except Exception:
            pass
        
        # タイトル要素の存在をチェック（複数のセレクタを試す）
        title_selectors = [
            "text=📚 論文一覧",
            "h1:has-text('論文一覧')",
            "text=論文一覧"
        ]
        
        for selector in title_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=3000):
                    return True
            except Exception:
                continue
        
        # ページ固有の要素で確認（インデックス統計ヘッダー）
        try:
            stats_header = self.page.locator("text=インデックス統計").first
            if stats_header.is_visible(timeout=3000):
                return True
        except Exception:
            pass
        
        # 空状態メッセージまたは論文カードの存在で確認
        try:
            # 空状態メッセージ
            if self.page.locator(self.empty_state_selector).count() > 0:
                return True
            # または論文カード
            if self.page.locator(self.paper_card_selector).count() > 0:
                return True
        except Exception:
            pass
        
        return False
    
    def get_papers_count(self) -> int:
        """論文数を取得
        
        表示されている論文カードの数を取得します。
        
        Requirements: 5.1, 5.5
        
        Returns:
            int: 論文数（空の場合は0）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> count = papers.get_papers_count()
            >>> assert count >= 0
        """
        try:
            # 論文カードを取得
            cards = self.page.locator(self.paper_card_selector).all()
            return len(cards)
        except Exception:
            return 0
    
    def get_paper_titles(self) -> List[str]:
        """論文タイトルのリストを取得
        
        表示されている全ての論文のタイトルを取得します。
        
        Requirements: 5.2
        
        Returns:
            List[str]: 論文タイトルのリスト
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> titles = papers.get_paper_titles()
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
            print(f"Warning: Failed to get paper titles: {e}")
        
        return titles
    
    def is_empty(self) -> bool:
        """空状態か確認
        
        論文が1件もインデックス化されていない状態かを確認します。
        
        Requirements: 5.4
        
        Returns:
            bool: 空状態の場合True
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> if papers.is_empty():
            ...     print("論文がありません")
        """
        try:
            # 空状態メッセージが表示されているか確認
            empty_state = self.page.locator(self.empty_state_selector).first
            if empty_state.is_visible(timeout=2000):
                return True
            
            # または、空状態メッセージテキストで確認
            empty_message = self.page.locator(self.empty_state_message_selector).first
            if empty_message.is_visible(timeout=2000):
                return True
        except Exception:
            pass
        
        # 論文カードが0件の場合も空状態
        return self.get_papers_count() == 0
    
    def get_paper_metadata(self, index: int = 0) -> dict:
        """論文のメタデータを取得
        
        指定されたインデックスの論文のメタデータを取得します。
        
        Requirements: 5.2, 5.3
        
        Args:
            index: 論文のインデックス（0始まり）
        
        Returns:
            dict: 論文メタデータ（title, authors, year, arxiv_id, chunk_count など）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> metadata = papers.get_paper_metadata(0)
            >>> assert "title" in metadata
            >>> assert "authors" in metadata
        """
        metadata = {
            "title": "",
            "authors": "",
            "year": "",
            "arxiv_id": "",
            "chunk_count": None
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
                    authors_text = authors_element.inner_text()
                    # "👤 " プレフィックスを除去
                    metadata["authors"] = authors_text.replace("👤 ", "").strip()
                
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
                
                # チャンク数を取得（カードの外側のメトリックから）
                # 論文カードの後にst.metricが表示されている
                try:
                    # カードの次の要素グループからメトリックを探す
                    # 実装では、カードの後にst.columnsでメトリックが表示される
                    # ここでは簡易的に、カードに続く要素から取得を試みる
                    
                    # 親要素から次の兄弟要素を探す
                    parent = card.locator("xpath=..").first
                    metrics = parent.locator(".stMetric").all()
                    
                    if len(metrics) > 0:
                        # 最初のメトリック（インデックス済みチャンク）を取得
                        metric_value = metrics[0].locator("[data-testid='stMetricValue']").first
                        if metric_value.is_visible():
                            chunk_text = metric_value.inner_text()
                            # 数値を抽出
                            chunk_match = re.search(r'(\d+)', chunk_text)
                            if chunk_match:
                                metadata["chunk_count"] = int(chunk_match.group(1))
                except Exception as e:
                    print(f"Warning: Failed to get chunk count: {e}")
        except Exception as e:
            print(f"Warning: Failed to get paper metadata: {e}")
        
        return metadata
    
    def get_all_papers_metadata(self) -> List[dict]:
        """全ての論文のメタデータを取得
        
        Returns:
            List[dict]: 論文メタデータのリスト
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> all_metadata = papers.get_all_papers_metadata()
            >>> assert len(all_metadata) > 0
        """
        all_metadata = []
        count = self.get_papers_count()
        
        for i in range(count):
            metadata = self.get_paper_metadata(i)
            all_metadata.append(metadata)
        
        return all_metadata
    
    def expand_details(self, index: int = 0) -> None:
        """詳細情報を展開
        
        指定されたインデックスの論文の詳細エクスパンダーを展開します。
        
        Args:
            index: 展開する論文のインデックス（デフォルト: 0）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> papers.expand_details(0)
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
            print(f"Warning: Failed to expand details: {e}")
    
    def click_pdf_link(self, index: int = 0) -> None:
        """PDFリンクをクリック
        
        指定されたインデックスの論文のPDFリンクをクリックします。
        
        Args:
            index: 論文のインデックス（デフォルト: 0）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> papers.click_pdf_link(0)
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
    
    def refresh_page(self) -> None:
        """ページをリフレッシュ
        
        サイドバーのリフレッシュボタンをクリックしてページを更新します。
        Streamlitのリフレッシュボタンがない場合は、ページを再ナビゲートします。
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> papers.refresh_page()
        """
        try:
            # サイドバー内のリフレッシュボタンを探す
            refresh_button = self.page.locator(
                f"{self.sidebar_selector} {self.refresh_button_selector}"
            ).first
            
            if refresh_button.is_visible(timeout=2000):
                refresh_button.click()
                # ページリロード完了を待機
                self.page.wait_for_timeout(2000)
                self.wait_for_load()
            else:
                # リフレッシュボタンが見つからない場合は、ページを再ナビゲート
                # Streamlitのマルチページアプリでは、reload()するとホームに戻るため
                print("Refresh button not found, re-navigating to page")
                self.navigate()
        except Exception as e:
            print(f"Warning: Failed to refresh page with button, re-navigating: {e}")
            # フォールバック: ページを再ナビゲート
            try:
                self.navigate()
            except Exception as e2:
                print(f"Warning: Failed to re-navigate: {e2}")
    
    def get_index_stats(self) -> dict:
        """インデックス統計情報を取得
        
        サイドバーに表示されているインデックス統計情報を取得します。
        
        Returns:
            dict: 統計情報（total_documents, index_ready など）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> stats = papers.get_index_stats()
            >>> print(f"総ドキュメント数: {stats['total_documents']}")
        """
        stats = {
            "total_documents": 0,
            "index_ready": False
        }
        
        try:
            # サイドバー内のメトリックを取得
            metrics = self.page.locator(
                f"{self.sidebar_selector} {self.index_stats_selector}"
            ).all()
            
            if len(metrics) > 0:
                # 最初のメトリック（総ドキュメント数）を取得
                metric_value = metrics[0].locator("[data-testid='stMetricValue']").first
                if metric_value.is_visible():
                    value_text = metric_value.inner_text()
                    # 数値を抽出
                    import re
                    match = re.search(r'(\d+)', value_text)
                    if match:
                        stats["total_documents"] = int(match.group(1))
            
            # インデックス準備状態を確認
            if self.is_element_visible(
                f"{self.sidebar_selector} .stSuccess:has-text('インデックス準備完了')",
                timeout=2000
            ):
                stats["index_ready"] = True
        except Exception as e:
            print(f"Warning: Failed to get index stats: {e}")
        
        return stats
    
    def has_success_message(self) -> bool:
        """成功メッセージが表示されているか確認
        
        "X件の論文がインデックス化されています" メッセージが表示されているか確認します。
        
        Requirements: 5.5
        
        Returns:
            bool: 成功メッセージが表示されている場合True
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> if papers.has_success_message():
            ...     print("論文がインデックス化されています")
        """
        return self.is_element_visible(
            f"{self.success_selector}:has-text('件の論文がインデックス化されています')",
            timeout=2000
        )
    
    def get_success_message(self) -> str:
        """成功メッセージを取得
        
        Returns:
            str: 成功メッセージ（表示されていない場合は空文字列）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> message = papers.get_success_message()
            >>> assert "件の論文がインデックス化されています" in message
        """
        try:
            success = self.page.locator(self.success_selector).first
            if success.is_visible(timeout=2000):
                return success.inner_text()
        except Exception:
            pass
        
        return ""
    
    def set_sort_option(self, option: str) -> None:
        """ソートオプションを設定
        
        Args:
            option: ソートオプション（"新しい順", "古い順", "タイトル順"）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> papers.set_sort_option("新しい順")
        """
        try:
            # ソートセレクトボックスを取得
            sort_select = self.page.locator(self.sort_selector).first
            
            if sort_select.is_visible(timeout=2000):
                sort_select.select_option(label=option)
                # ソート処理完了を待機
                self.page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Warning: Failed to set sort option: {e}")
    
    def get_empty_state_message(self) -> str:
        """空状態メッセージを取得
        
        Returns:
            str: 空状態メッセージ（表示されていない場合は空文字列）
        
        Example:
            >>> papers = PapersPage(page, "http://localhost:8501")
            >>> papers.navigate("/3_papers")
            >>> if papers.is_empty():
            ...     message = papers.get_empty_state_message()
            ...     assert "インデックス化された論文がありません" in message
        """
        try:
            # 空状態のdivを探す
            empty_state = self.page.locator(self.empty_state_selector).first
            if empty_state.is_visible(timeout=2000):
                return empty_state.inner_text()
        except Exception:
            pass
        
        # フォールバック: 特定のテキストを直接探す
        try:
            empty_message = self.page.locator("text=インデックス化された論文がありません").first
            if empty_message.is_visible(timeout=2000):
                # 親要素全体のテキストを取得
                parent = empty_message.locator("xpath=../..").first
                if parent.is_visible():
                    return parent.inner_text()
                return empty_message.inner_text()
        except Exception:
            pass
        
        return ""
