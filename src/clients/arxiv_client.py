"""arXiv APIクライアント

Requirements: 1.1, 1.4
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import arxiv
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.models.paper import PaperMetadata

logger = logging.getLogger(__name__)


class ArxivClientError(Exception):
    """arXivクライアント関連エラー"""
    pass


class ArxivClient:
    """arXiv APIクライアント

    論文検索、メタデータ取得、PDF取得を提供します。
    エラーハンドリングとリトライロジックを含みます。

    Requirements: 1.1, 1.4
    """

    def __init__(
        self,
        cache_dir: Path = Path("./cache/pdfs"),
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Args:
            cache_dir: PDFキャッシュディレクトリ
            max_retries: 最大リトライ回数
            timeout: タイムアウト秒数
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.timeout = timeout
        self.client = arxiv.Client()

        logger.info(
            f"ArxivClient initialized: cache_dir={cache_dir}, "
            f"max_retries={max_retries}, timeout={timeout}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((arxiv.ArxivError, httpx.HTTPError)),
        reraise=True
    )
    async def search_papers(
        self,
        query: str,
        max_results: int = 10,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance
    ) -> list[PaperMetadata]:
        """論文検索

        キーワードで論文を検索し、メタデータのリストを返します。

        Args:
            query: 検索クエリ（キーワード、著者名など）
            max_results: 最大取得件数
            sort_by: ソート基準（Relevance/LastUpdatedDate/SubmittedDate）

        Returns:
            PaperMetadataのリスト

        Raises:
            ArxivClientError: 検索失敗時

        Requirements: 1.1
        """
        try:
            logger.info(f"Searching papers: query='{query}', max_results={max_results}")

            # arxiv.Searchを使用して検索
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by
            )

            # 非同期実行のためにrun_in_executorを使用
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.client.results(search))
            )

            # PaperMetadataに変換
            papers = []
            for result in results:
                paper = self._convert_to_metadata(result)
                papers.append(paper)

            logger.info(f"Found {len(papers)} papers")
            return papers

        except arxiv.ArxivError as e:
            logger.error(f"arXiv API error: {e}")
            raise ArxivClientError(f"Failed to search papers: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise ArxivClientError(f"Unexpected error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((arxiv.ArxivError, httpx.HTTPError)),
        reraise=True
    )
    async def get_metadata(
        self,
        arxiv_id: str
    ) -> PaperMetadata:
        """メタデータ取得

        arxiv_idから論文のメタデータを取得します。

        Args:
            arxiv_id: arXiv論文ID（例: "2301.00001"）

        Returns:
            PaperMetadata

        Raises:
            ArxivClientError: 取得失敗時

        Requirements: 1.1
        """
        try:
            logger.info(f"Getting metadata: arxiv_id={arxiv_id}")

            # ID検索
            search = arxiv.Search(id_list=[arxiv_id])

            # 非同期実行
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.client.results(search))
            )

            if not results:
                raise ArxivClientError(f"Paper not found: {arxiv_id}")

            paper = self._convert_to_metadata(results[0])
            logger.info(f"Retrieved metadata: {paper.title}")
            return paper

        except arxiv.ArxivError as e:
            logger.error(f"arXiv API error: {e}")
            raise ArxivClientError(f"Failed to get metadata: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting metadata: {e}")
            raise ArxivClientError(f"Unexpected error: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True
    )
    async def download_pdf(
        self,
        arxiv_id: str,
        pdf_url: Optional[str] = None
    ) -> Path:
        """PDF取得

        論文PDFをダウンロードしてローカルに保存します。
        既にキャッシュが存在する場合は再ダウンロードしません。

        Args:
            arxiv_id: arXiv論文ID
            pdf_url: PDF URL（省略時は自動生成）

        Returns:
            保存されたPDFファイルのPath

        Raises:
            ArxivClientError: ダウンロード失敗時

        Requirements: 1.4
        """
        try:
            # キャッシュパスを生成
            pdf_path = self.cache_dir / f"{arxiv_id.replace('/', '_')}.pdf"

            # キャッシュが存在する場合はスキップ
            if pdf_path.exists():
                logger.info(f"PDF already cached: {pdf_path}")
                return pdf_path

            # PDF URLを生成（省略時）
            if pdf_url is None:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            logger.info(f"Downloading PDF: {pdf_url} -> {pdf_path}")

            # httpxで非同期ダウンロード
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(pdf_url, follow_redirects=True)
                response.raise_for_status()

                # ファイルに保存
                pdf_path.write_bytes(response.content)

            logger.info(f"PDF downloaded successfully: {pdf_path} ({len(response.content)} bytes)")
            return pdf_path

        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading PDF: {e}")
            raise ArxivClientError(f"Failed to download PDF: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF: {e}")
            raise ArxivClientError(f"Unexpected error: {e}") from e

    def _convert_to_metadata(self, result: arxiv.Result) -> PaperMetadata:
        """arxiv.ResultをPaperMetadataに変換

        Args:
            result: arxiv.Result

        Returns:
            PaperMetadata
        """
        # arXiv IDを正規化（バージョン番号を除去）
        arxiv_id = result.entry_id.split("/")[-1].split("v")[0]

        # 著者リストを抽出
        authors = [author.name for author in result.authors]

        # カテゴリリストを抽出
        categories = [cat for cat in result.categories]

        # 発行年を抽出
        year = result.published.year

        # PDF URLを生成
        pdf_url = result.pdf_url

        # DOIを取得（存在する場合）
        doi = result.doi if hasattr(result, 'doi') else None

        return PaperMetadata(
            arxiv_id=arxiv_id,
            title=result.title,
            authors=authors,
            abstract=result.summary,
            year=year,
            categories=categories,
            pdf_url=pdf_url,
            doi=doi,
            published_date=result.published
        )
