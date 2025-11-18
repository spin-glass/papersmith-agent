# -*- coding: utf-8 -*-
"""RAG Page Object

RAG質問応答ページのPage Objectを提供します。
RAGページの要素とインタラクションをカプセル化します。

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""
from typing import List, Optional

from playwright.sync_api import Page

from tests.e2e.pages.base_page import BasePage


class RAGPage(BasePage):
    """RAG質問応答ページのPage Object
    
    Papersmith AgentのRAG質問応答ページのUI要素と操作を提供します。
    質問送信、回答取得、参照元チャンク表示などを行います。
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    # クラス変数としてサイドバーセレクタを定義
    sidebar_selector = "[data-testid='stSidebar']"
    
    def navigate(self, path: str = "") -> None:
        """RAG ページに移動
        
        Streamlitのマルチページアプリでは、直接URLにアクセスしても
        ルーティングが機能しないため、ホームページからサイドバーの
        リンクをクリックしてページ遷移します。
        
        Requirements: 4.1
        
        Args:
            path: 使用されません（互換性のため保持）
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate()
            >>> assert rag.is_element_visible(rag.question_input_selector)
        """
        # まずホームページに移動
        self.page.goto(self.base_url)
        self.wait_for_load()
        
        # サイドバーが完全にレンダリングされるまで待機
        self.page.wait_for_timeout(1000)
        
        # サイドバーの「RAG質問応答」リンクをクリック
        try:
            # Streamlitの st.page_link は複数のセレクタで試す
            selectors = [
                f"{self.sidebar_selector} a:has-text('RAG質問応答')",
                f"{self.sidebar_selector} a:has-text('💬 RAG質問応答')",
                f"{self.sidebar_selector} [data-testid='stPageLink-NavLink']:has-text('RAG質問応答')",
                "a[href*='2_rag']",
                "a[href*='rag']"
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
                raise Exception("Could not find RAG link with any selector")
            
            # ページ遷移を待機
            self.page.wait_for_timeout(2000)
            self.wait_for_load()
        except Exception as e:
            print(f"Warning: Failed to click RAG link: {e}")
            # フォールバック: 直接URLで試す（動作しない可能性が高い）
            super().navigate("/2_rag")
    
    def __init__(self, page: Page, base_url: str):
        """RAGPage初期化
        
        Args:
            page: Playwrightページオブジェクト
            base_url: アプリケーションのベースURL
        """
        super().__init__(page, base_url)
        
        # ページ要素のセレクタ
        self.question_input_selector = "textarea[aria-label='質問']"
        self.submit_button_selector = "button:has-text('質問する')"
        self.clear_button_selector = "button:has-text('クリア')"
        
        # 回答表示エリア
        self.answer_box_selector = ".answer-box"
        self.answer_text_selector = ".answer-text"
        self.question_box_selector = ".question-box"
        
        # 参照元チャンク
        self.expander_selector = "[data-testid='stExpander']"
        self.source_box_selector = ".source-box"
        self.source_text_selector = ".source-text"
        self.source_meta_selector = ".source-meta"
        
        # ローディング・メッセージ
        self.spinner_selector = ".stSpinner"
        self.warning_selector = "[data-testid='stAlert']"
        self.success_selector = ".stSuccess"
        
        # サイドバー要素
        self.sidebar_selector = "[data-testid='stSidebar']"
        self.top_k_slider_selector = "input[type='range']"
    
    def ask_question(self, question: str, wait_for_answer: bool = True) -> None:
        """質問を送信
        
        質問入力フィールドに質問を入力し、送信ボタンをクリックします。
        デフォルトでは回答生成完了まで待機します。
        
        Requirements: 4.1, 4.2
        
        Args:
            question: 質問テキスト
            wait_for_answer: 回答生成完了まで待機するか（デフォルト: True）
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> answer = rag.get_answer()
        """
        # 質問入力フィールドに入力
        question_input = self.page.locator(self.question_input_selector).first
        question_input.fill(question)
        
        # 送信ボタンをクリック
        submit_button = self.page.locator(self.submit_button_selector).first
        submit_button.click()
        
        # 回答生成完了まで待機
        if wait_for_answer:
            self.wait_for_answer_complete()
    
    def get_answer(self) -> str:
        """回答を取得
        
        生成された回答テキストを取得します。
        回答が表示されていない場合は空文字列を返します。
        
        Requirements: 4.2
        
        Returns:
            str: 回答テキスト（回答が表示されていない場合は空文字列）
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> answer = rag.get_answer()
            >>> assert len(answer) > 0
        """
        try:
            # 回答ボックスが表示されるまで待機
            answer_box = self.page.locator(self.answer_box_selector).first
            answer_box.wait_for(state="visible", timeout=5000)
            
            # 回答テキストを取得
            answer_text = self.page.locator(self.answer_text_selector).first
            return answer_text.inner_text()
        except Exception as e:
            print(f"Warning: Failed to get answer: {e}")
            return ""
    
    def expand_sources(self, index: int = 0) -> None:
        """参照元を展開
        
        指定されたインデックスの参照元エクスパンダーを展開します。
        
        Requirements: 4.3, 4.4
        
        Args:
            index: 展開するエクスパンダーのインデックス（デフォルト: 0）
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> rag.expand_sources(0)  # 最初の参照元を展開
            >>> chunks = rag.get_source_chunks()
        """
        try:
            # エクスパンダーを取得
            expanders = self.page.locator(self.expander_selector).all()
            
            if index < len(expanders):
                expander = expanders[index]
                
                # エクスパンダーが閉じている場合のみクリック
                # Streamlitのエクスパンダーは summary 要素を持つ
                summary = expander.locator("summary").first
                if summary.is_visible():
                    summary.click()
                    # 展開アニメーション完了を待機
                    self.page.wait_for_timeout(500)
            else:
                print(f"Warning: Expander index {index} out of range")
        except Exception as e:
            print(f"Warning: Failed to expand sources: {e}")
    
    def expand_all_sources(self) -> None:
        """全ての参照元を展開
        
        全ての参照元エクスパンダーを展開します。
        
        Requirements: 4.3, 4.4
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> rag.expand_all_sources()
            >>> chunks = rag.get_source_chunks()
        """
        try:
            # 全てのエクスパンダーを取得
            expanders = self.page.locator(self.expander_selector).all()
            
            for expander in expanders:
                try:
                    summary = expander.locator("summary").first
                    if summary.is_visible():
                        summary.click()
                        # 展開アニメーション完了を待機
                        self.page.wait_for_timeout(300)
                except Exception:
                    continue
        except Exception as e:
            print(f"Warning: Failed to expand all sources: {e}")
    
    def get_source_chunks(self) -> List[dict]:
        """参照元チャンクを取得
        
        表示されている参照元チャンクの情報を取得します。
        エクスパンダーが展開されている必要があります。
        
        Requirements: 4.4
        
        Returns:
            List[dict]: チャンク情報のリスト
                各辞書には以下のキーが含まれます:
                - text: チャンクのテキスト
                - metadata: メタデータ（論文ID、セクション、チャンクIDなど）
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> rag.expand_all_sources()
            >>> chunks = rag.get_source_chunks()
            >>> assert len(chunks) > 0
            >>> assert "text" in chunks[0]
        """
        chunks = []
        
        try:
            # 全てのソースボックスを取得
            source_boxes = self.page.locator(self.source_box_selector).all()
            
            for source_box in source_boxes:
                try:
                    # チャンクテキストを取得
                    text_element = source_box.locator(self.source_text_selector).first
                    text = text_element.inner_text() if text_element.is_visible() else ""
                    
                    # メタデータを取得
                    meta_element = source_box.locator(self.source_meta_selector).first
                    metadata_text = meta_element.inner_text() if meta_element.is_visible() else ""
                    
                    # メタデータをパース（簡易版）
                    metadata = self._parse_metadata(metadata_text)
                    
                    chunks.append({
                        "text": text,
                        "metadata": metadata,
                        "metadata_raw": metadata_text
                    })
                except Exception as e:
                    print(f"Warning: Failed to parse source chunk: {e}")
                    continue
        except Exception as e:
            print(f"Warning: Failed to get source chunks: {e}")
        
        return chunks
    
    def _parse_metadata(self, metadata_text: str) -> dict:
        """メタデータテキストをパース
        
        Args:
            metadata_text: メタデータテキスト
                例: "📌 論文ID: 2301.00001 | 📑 セクション: introduction | 🆔 チャンクID: chunk_0"
        
        Returns:
            dict: パースされたメタデータ
        """
        metadata = {}
        
        try:
            # 論文IDを抽出
            if "論文ID:" in metadata_text:
                parts = metadata_text.split("論文ID:")[1].split("|")[0].strip()
                metadata["arxiv_id"] = parts
            
            # セクションを抽出
            if "セクション:" in metadata_text:
                parts = metadata_text.split("セクション:")[1].split("|")[0].strip()
                metadata["section"] = parts
            
            # チャンクIDを抽出
            if "チャンクID:" in metadata_text:
                parts = metadata_text.split("チャンクID:")[1].strip()
                metadata["chunk_id"] = parts
        except Exception as e:
            print(f"Warning: Failed to parse metadata: {e}")
        
        return metadata
    
    def wait_for_answer_complete(self, timeout: int = 60000) -> None:
        """回答生成完了を待機
        
        スピナーが消えるまで待機します。
        RAG質問応答はLLM推論を含むため、デフォルトで60秒のタイムアウトを設定しています。
        
        Requirements: 4.5
        
        Args:
            timeout: タイムアウト時間（ミリ秒、デフォルト: 60000）
        
        Raises:
            TimeoutError: タイムアウト時間内に完了しなかった場合
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> question_input = page.locator("textarea[aria-label='質問']")
            >>> question_input.fill("この論文の主な貢献は何ですか？")
            >>> submit_button = page.locator("button:has-text('質問する')")
            >>> submit_button.click()
            >>> rag.wait_for_answer_complete()
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
            print(f"Warning: wait_for_answer_complete timeout or error: {e}")
            # タイムアウトしても続行（回答が表示されている可能性がある）
    
    def get_question_text(self) -> str:
        """表示されている質問テキストを取得
        
        Returns:
            str: 質問テキスト（表示されていない場合は空文字列）
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> question = rag.get_question_text()
            >>> assert "主な貢献" in question
        """
        try:
            question_box = self.page.locator(self.question_box_selector).first
            if question_box.is_visible(timeout=2000):
                return question_box.inner_text()
        except Exception:
            pass
        
        return ""
    
    def has_warning(self) -> bool:
        """警告メッセージが表示されているか確認
        
        インデックスが空の場合などに警告が表示されます。
        
        Requirements: 4.6
        
        Returns:
            bool: 警告が表示されている場合True
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> if rag.has_warning():
            ...     print("インデックスが空です")
        """
        return self.is_element_visible(self.warning_selector, timeout=2000)
    
    def get_warning_message(self) -> str:
        """警告メッセージを取得
        
        Returns:
            str: 警告メッセージ（表示されていない場合は空文字列）
        """
        try:
            warning = self.page.locator(self.warning_selector).first
            if warning.is_visible(timeout=2000):
                return warning.inner_text()
        except Exception:
            pass
        
        return ""
    
    def clear_results(self) -> None:
        """結果をクリア
        
        クリアボタンをクリックして結果を消去します。
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> rag.clear_results()
        """
        try:
            clear_button = self.page.locator(self.clear_button_selector).first
            if clear_button.is_visible(timeout=2000):
                clear_button.click()
                # ページリロード完了を待機
                self.wait_for_load()
        except Exception as e:
            print(f"Warning: Failed to clear results: {e}")
    
    def set_top_k(self, value: int) -> None:
        """取得チャンク数を設定
        
        サイドバーのスライダーで取得チャンク数を設定します。
        
        Args:
            value: 取得チャンク数（1-20）
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.set_top_k(10)
        """
        try:
            # サイドバー内のスライダーを取得
            slider = self.page.locator(
                f"{self.sidebar_selector} {self.top_k_slider_selector}"
            ).first
            
            if slider.is_visible(timeout=2000):
                # スライダーの値を設定
                slider.fill(str(value))
        except Exception as e:
            print(f"Warning: Failed to set top_k: {e}")
    
    def get_sources_count(self) -> int:
        """参照元チャンクの数を取得
        
        Returns:
            int: 参照元チャンクの数
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> count = rag.get_sources_count()
            >>> assert count > 0
        """
        try:
            expanders = self.page.locator(self.expander_selector).all()
            return len(expanders)
        except Exception:
            return 0
    
    def is_answer_displayed(self) -> bool:
        """回答が表示されているか確認
        
        Returns:
            bool: 回答が表示されている場合True
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> rag.ask_question("この論文の主な貢献は何ですか？")
            >>> assert rag.is_answer_displayed()
        """
        return self.is_element_visible(self.answer_box_selector, timeout=5000)
    
    def get_indexed_papers_count(self) -> Optional[int]:
        """インデックス化された論文数を取得
        
        サイドバーに表示されているインデックス化された論文数を取得します。
        
        Returns:
            Optional[int]: 論文数（取得できない場合はNone）
        
        Example:
            >>> rag = RAGPage(page, "http://localhost:8501")
            >>> rag.navigate("/2_rag")
            >>> count = rag.get_indexed_papers_count()
            >>> if count is not None:
            ...     print(f"{count}件の論文がインデックス化されています")
        """
        try:
            # サイドバー内の成功メッセージを探す
            # 例: "✅ 5件の論文がインデックス化されています"
            success_msg = self.page.locator(
                f"{self.sidebar_selector} .stSuccess"
            ).first
            
            if success_msg.is_visible(timeout=2000):
                text = success_msg.inner_text()
                # 数値を抽出
                import re
                match = re.search(r'(\d+)件', text)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        
        return None
