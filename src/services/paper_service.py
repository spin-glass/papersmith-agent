# -*- coding: utf-8 -*-
"""論文取得・管理サービス

Requirements: 1.1, 1.4, 1.5
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from pypdf import PdfReader

from src.clients.arxiv_client import ArxivClient, ArxivClientError
from src.models.paper import PaperMetadata


logger = logging.getLogger(__name__)


class PaperServiceError(Exception):
    """PaperService関連エラー"""
    pass


class PaperService:
    """論文取得・管理サービス
    
    論文の検索、PDF取得、メタデータ管理、テキスト抽出を提供します。
    キャッシュ機能により重複ダウンロードを防止します。
    
    Requirements: 1.1, 1.4, 1.5
    """
    
    def __init__(
        self,
        arxiv_client: ArxivClient,
        cache_dir: Path = Path("./cache")
    ):
        """
        Args:
            arxiv_client: ArxivClientインスタンス
            cache_dir: キャッシュディレクトリ（PDF、メタデータ）
        """
        self.arxiv_client = arxiv_client
        self.cache_dir = Path(cache_dir)
        
        # キャッシュディレクトリを作成
        self.pdf_cache_dir = self.cache_dir / "pdfs"
        self.metadata_cache_dir = self.cache_dir / "metadata"
        self.pdf_cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"PaperService initialized: "
            f"pdf_cache={self.pdf_cache_dir}, "
            f"metadata_cache={self.metadata_cache_dir}"
        )
    
    async def search_papers(
        self,
        query: str,
        max_results: int = 10
    ) -> List[PaperMetadata]:
        """論文検索
        
        ArxivClientを使用してキーワードで論文を検索します。
        
        Args:
            query: 検索クエリ（キーワード、著者名など）
            max_results: 最大取得件数
        
        Returns:
            PaperMetadataのリスト
        
        Raises:
            PaperServiceError: 検索失敗時
        
        Requirements: 1.1
        """
        try:
            logger.info(f"Searching papers: query='{query}', max_results={max_results}")
            papers = await self.arxiv_client.search_papers(query, max_results)
            logger.info(f"Search completed: found {len(papers)} papers")
            return papers
        except ArxivClientError as e:
            logger.error(f"Failed to search papers: {e}")
            raise PaperServiceError(f"Failed to search papers: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise PaperServiceError(f"Unexpected error: {e}") from e
    
    async def download_pdf(
        self,
        arxiv_id: str,
        pdf_url: Optional[str] = None
    ) -> Path:
        """PDF取得
        
        論文PDFをダウンロードしてローカルに保存します。
        キャッシュをチェックし、既に存在する場合は再ダウンロードしません。
        
        Args:
            arxiv_id: arXiv論文ID
            pdf_url: PDF URL（省略時は自動生成）
        
        Returns:
            保存されたPDFファイルのPath
        
        Raises:
            PaperServiceError: ダウンロード失敗時
        
        Requirements: 1.4
        """
        try:
            # キャッシュパスを生成
            pdf_path = self.pdf_cache_dir / f"{arxiv_id.replace('/', '_')}.pdf"
            
            # キャッシュが存在する場合はスキップ
            if pdf_path.exists():
                logger.info(f"PDF already cached: {pdf_path}")
                return pdf_path
            
            logger.info(f"Downloading PDF for arxiv_id={arxiv_id}")
            
            # ArxivClientを使用してダウンロード
            downloaded_path = await self.arxiv_client.download_pdf(arxiv_id, pdf_url)
            
            # ArxivClientのキャッシュディレクトリと異なる場合はコピー
            if downloaded_path != pdf_path:
                import shutil
                shutil.copy(downloaded_path, pdf_path)
                logger.info(f"PDF copied to cache: {pdf_path}")
            
            return pdf_path
            
        except ArxivClientError as e:
            logger.error(f"Failed to download PDF: {e}")
            raise PaperServiceError(f"Failed to download PDF: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF: {e}")
            raise PaperServiceError(f"Unexpected error: {e}") from e
    
    async def get_metadata(
        self,
        arxiv_id: str,
        force_refresh: bool = False
    ) -> PaperMetadata:
        """メタデータ取得
        
        論文のメタデータを取得します。
        キャッシュを優先し、存在しない場合はarXiv APIから取得してJSON保存します。
        
        Args:
            arxiv_id: arXiv論文ID
            force_refresh: Trueの場合、キャッシュを無視して再取得
        
        Returns:
            PaperMetadata
        
        Raises:
            PaperServiceError: 取得失敗時
        
        Requirements: 1.5
        """
        try:
            # キャッシュパスを生成
            metadata_path = self.metadata_cache_dir / f"{arxiv_id.replace('/', '_')}.json"
            
            # キャッシュが存在し、force_refreshでない場合はキャッシュから読み込み
            if metadata_path.exists() and not force_refresh:
                logger.info(f"Loading metadata from cache: {metadata_path}")
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # datetimeをパース
                    data['published_date'] = datetime.fromisoformat(data['published_date'])
                    return PaperMetadata(**data)
            
            # arXiv APIから取得
            logger.info(f"Fetching metadata from arXiv API: arxiv_id={arxiv_id}")
            metadata = await self.arxiv_client.get_metadata(arxiv_id)
            
            # JSONとして保存
            with open(metadata_path, 'w', encoding='utf-8') as f:
                # Pydanticモデルをdictに変換
                data = metadata.model_dump()
                # datetimeをISO形式文字列に変換
                data['published_date'] = metadata.published_date.isoformat()
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Metadata cached: {metadata_path}")
            return metadata
            
        except ArxivClientError as e:
            logger.error(f"Failed to get metadata: {e}")
            raise PaperServiceError(f"Failed to get metadata: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting metadata: {e}")
            raise PaperServiceError(f"Unexpected error: {e}") from e
    
    async def extract_text(
        self,
        pdf_path: Path
    ) -> str:
        """テキスト抽出
        
        PDFファイルからテキストを抽出します。
        pypdfを使用してページごとにテキストを抽出し、結合します。
        
        Args:
            pdf_path: PDFファイルのPath
        
        Returns:
            抽出されたテキスト
        
        Raises:
            PaperServiceError: 抽出失敗時
        
        Requirements: 1.4
        """
        try:
            if not pdf_path.exists():
                raise PaperServiceError(f"PDF file not found: {pdf_path}")
            
            logger.info(f"Extracting text from PDF: {pdf_path}")
            
            # PdfReaderでPDFを読み込み
            reader = PdfReader(str(pdf_path))
            
            # 全ページのテキストを抽出
            text_parts = []
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    continue
            
            # テキストを結合
            full_text = "\n\n".join(text_parts)
            
            logger.info(
                f"Text extraction completed: "
                f"{len(reader.pages)} pages, {len(full_text)} characters"
            )
            
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            raise PaperServiceError(f"Failed to extract text: {e}") from e
