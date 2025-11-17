# -*- coding: utf-8 -*-
"""FastAPI アプリケーション - Papersmith Agent

Requirements: 8.1, 8.2, 8.3, 8.5
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.index_holder import index_holder
from src.clients.arxiv_client import ArxivClient
from src.clients.chroma_client import ChromaClient
from src.models.paper import PaperMetadata
from src.models.rag import RAGResponse
from src.services.embedding_service import EmbeddingService
from src.services.llm_service import LLMService
from src.services.paper_service import PaperService
from src.services.rag_service import basic_rag_query
from src.utils.config_loader import load_chroma_config, load_embedding_config, load_llm_config
from src.utils.errors import APIError, IndexNotReadyError, LLMError, PapersmithError
from src.utils.logger import setup_logger


# ロギング設定
logger = setup_logger(
    name="papersmith.api",
    level="INFO",
    log_file=Path("./logs/papersmith.log")
)


# グローバルサービスインスタンス
paper_service: Optional[PaperService] = None
embedding_service: Optional[EmbeddingService] = None
llm_service: Optional[LLMService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理
    
    startup: Chromaインデックスをロード、InMemoryIndexHolderに設定
    shutdown: クリーンアップ処理
    
    Requirements: 8.1, 8.2
    """
    # Startup
    logger.info("Starting Papersmith Agent API...")
    
    global paper_service, embedding_service, llm_service
    
    try:
        # 設定を環境変数から読み込み
        chroma_config = load_chroma_config()
        embedding_config = load_embedding_config()
        llm_config = load_llm_config()
        
        logger.info(f"Configuration loaded - LLM backend: {llm_config.backend}, Embedding backend: {embedding_config.backend}")
        
        # Chromaクライアントを初期化
        logger.info("Initializing Chroma client...")
        chroma_client = ChromaClient(chroma_config)
        chroma_client.initialize()
        
        # InMemoryIndexHolderに設定
        await index_holder.set(chroma_client)
        logger.info(f"Chroma index loaded: {chroma_client.count()} documents")
        
        # Embeddingサービスを初期化
        logger.info("Loading embedding model...")
        embedding_service = EmbeddingService(config=embedding_config)
        await embedding_service.load_model()
        logger.info("Embedding model loaded")
        
        # LLMサービスを初期化
        logger.info("Loading LLM model...")
        llm_service = LLMService(config=llm_config)
        await llm_service.load_model()
        logger.info("LLM model loaded")
        
        # PaperServiceを初期化
        arxiv_client = ArxivClient()
        paper_service = PaperService(
            arxiv_client=arxiv_client,
            cache_dir=Path("./cache")
        )
        logger.info("PaperService initialized")
        
        logger.info("Papersmith Agent API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Papersmith Agent API...")


# FastAPIアプリケーション作成
app = FastAPI(
    title="Papersmith Agent API",
    description="完全ローカルで動作する自律型論文解析エージェントシステム",
    version="1.0.0",
    lifespan=lifespan
)


# ===== リクエスト/レスポンスモデル =====

class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = Field(..., description="ステータス (ok/initializing)")
    index_ready: bool = Field(..., description="インデックスが利用可能か")
    index_size: int = Field(..., description="インデックス内のドキュメント数")


class SearchRequest(BaseModel):
    """論文検索リクエスト"""
    query: str = Field(..., description="検索クエリ")
    max_results: int = Field(default=10, ge=1, le=100, description="最大取得件数")


class SearchResponse(BaseModel):
    """論文検索レスポンス"""
    papers: List[PaperMetadata] = Field(..., description="検索結果の論文リスト")
    count: int = Field(..., description="取得件数")


class DownloadRequest(BaseModel):
    """PDF取得リクエスト"""
    arxiv_id: str = Field(..., description="arXiv論文ID")


class DownloadResponse(BaseModel):
    """PDF取得レスポンス"""
    status: str = Field(..., description="ステータス (success/error)")
    arxiv_id: str = Field(..., description="arXiv論文ID")
    pdf_path: str = Field(..., description="保存されたPDFパス")
    indexed_chunks: int = Field(..., description="インデックス化されたチャンク数")
    message: str = Field(..., description="メッセージ")


class RAGQueryRequest(BaseModel):
    """RAGクエリリクエスト"""
    question: str = Field(..., description="質問")
    arxiv_ids: Optional[List[str]] = Field(None, description="フィルタリングする論文IDリスト")
    top_k: int = Field(default=5, ge=1, le=20, description="取得する検索結果数")


class InitIndexRequest(BaseModel):
    """インデックス初期化リクエスト"""
    force: bool = Field(default=False, description="強制的に再構築するか")


class InitIndexResponse(BaseModel):
    """インデックス初期化レスポンス"""
    status: str = Field(..., description="ステータス (success/error)")
    indexed_count: int = Field(..., description="インデックス化されたドキュメント数")
    message: str = Field(..., description="メッセージ")


# ===== エラーハンドラー =====

@app.exception_handler(IndexNotReadyError)
async def index_not_ready_handler(request: Request, exc: IndexNotReadyError):
    """IndexNotReadyErrorハンドラー
    
    インデックス未準備時の503エラーを返します。
    
    Requirements: 8.2, 8.5
    """
    logger.warning(f"Index not ready: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": exc.message,
            "status": "initializing",
            "error_type": "IndexNotReadyError"
        }
    )


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """APIErrorハンドラー
    
    外部API関連エラーを処理します。
    
    Requirements: 8.5
    """
    logger.error(
        f"API error: {exc.message} (API: {exc.api_name}, Status: {exc.status_code})",
        extra={"details": exc.details}
    )
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": exc.message,
            "api_name": exc.api_name,
            "status_code": exc.status_code,
            "error_type": "APIError"
        }
    )


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError):
    """LLMErrorハンドラー
    
    LLM推論エラーを処理します。
    
    Requirements: 8.5
    """
    logger.error(
        f"LLM error: {exc.message} (Model: {exc.model_name})",
        extra={"details": exc.details}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": exc.message,
            "model_name": exc.model_name,
            "error_type": "LLMError",
            "fallback": "基本的なサマリーを提供できる可能性があります。"
        }
    )


@app.exception_handler(PapersmithError)
async def papersmith_error_handler(request: Request, exc: PapersmithError):
    """PapersmithErrorハンドラー
    
    Papersmith基底例外を処理します。
    
    Requirements: 8.5
    """
    logger.error(f"Papersmith error: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": exc.message,
            "error_type": "PapersmithError"
        }
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """RuntimeErrorハンドラー
    
    Requirements: 8.5
    """
    if "Index not ready" in str(exc):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "インデックス構築中です。しばらくお待ちください。",
                "status": "initializing"
            }
        )
    
    # その他のRuntimeError
    logger.error(f"Runtime error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般的な例外ハンドラー
    
    Requirements: 8.5
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "内部サーバーエラーが発生しました。"}
    )


# ===== エンドポイント =====

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェックエンドポイント
    
    インデックスの準備状態を返します。
    
    Requirements: 8.2
    """
    is_ready = index_holder.is_ready()
    index_size = index_holder.size()
    
    return HealthResponse(
        status="ok" if is_ready else "initializing",
        index_ready=is_ready,
        index_size=index_size
    )


@app.post("/papers/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """論文検索エンドポイント
    
    PaperServiceを使用してarXiv論文を検索します。
    
    Requirements: 8.3
    """
    if paper_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PaperService is not initialized"
        )
    
    try:
        logger.info(f"Searching papers: query='{request.query}', max_results={request.max_results}")
        
        papers = await paper_service.search_papers(
            query=request.query,
            max_results=request.max_results
        )
        
        return SearchResponse(
            papers=papers,
            count=len(papers)
        )
        
    except Exception as e:
        logger.error(f"Failed to search papers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"論文検索に失敗しました: {str(e)}"
        )


@app.post("/papers/download", response_model=DownloadResponse)
async def download_paper(request: DownloadRequest):
    """PDF取得エンドポイント
    
    PDF取得、テキスト抽出、インデックス化を実行します。
    
    Requirements: 8.3
    """
    if paper_service is None or embedding_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services are not initialized"
        )
    
    # インデックスが準備できているか確認
    chroma_client = await index_holder.get()
    
    try:
        logger.info(f"Downloading paper: arxiv_id={request.arxiv_id}")
        
        # メタデータを取得
        metadata = await paper_service.get_metadata(request.arxiv_id)
        
        # PDFをダウンロード
        pdf_path = await paper_service.download_pdf(
            arxiv_id=request.arxiv_id,
            pdf_url=metadata.pdf_url
        )
        
        # テキストを抽出
        text = await paper_service.extract_text(pdf_path)
        
        # RAGServiceを使用してインデックス化
        from src.services.rag_service import RAGService
        rag_service = RAGService(
            chroma_client=chroma_client,
            embedding_service=embedding_service
        )
        
        indexed_chunks = await rag_service.index_paper(
            arxiv_id=request.arxiv_id,
            text=text,
            metadata=metadata
        )
        
        logger.info(
            f"Paper indexed successfully: arxiv_id={request.arxiv_id}, "
            f"chunks={indexed_chunks}"
        )
        
        return DownloadResponse(
            status="success",
            arxiv_id=request.arxiv_id,
            pdf_path=str(pdf_path),
            indexed_chunks=indexed_chunks,
            message=f"論文を正常にダウンロードし、{indexed_chunks}個のチャンクをインデックス化しました。"
        )
        
    except Exception as e:
        logger.error(f"Failed to download and index paper: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"論文のダウンロードとインデックス化に失敗しました: {str(e)}"
        )


@app.post("/rag/query", response_model=RAGResponse)
async def rag_query(request: RAGQueryRequest):
    """RAGクエリエンドポイント
    
    basic_rag_queryを使用して質問に回答します。
    
    Requirements: 8.3
    """
    if embedding_service is None or llm_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services are not initialized"
        )
    
    # インデックスが準備できているか確認
    chroma_client = await index_holder.get()
    
    try:
        logger.info(
            f"RAG query: question='{request.question[:50]}...', "
            f"arxiv_ids={request.arxiv_ids}, top_k={request.top_k}"
        )
        
        # basic_rag_queryを実行
        response = await basic_rag_query(
            question=request.question,
            arxiv_ids=request.arxiv_ids,
            chroma_client=chroma_client,
            embedding_service=embedding_service,
            llm_service=llm_service,
            top_k=request.top_k
        )
        
        logger.info("RAG query completed successfully")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to execute RAG query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAGクエリの実行に失敗しました: {str(e)}"
        )


@app.post("/admin/init-index", response_model=InitIndexResponse)
async def init_index(request: InitIndexRequest):
    """インデックス再構築エンドポイント
    
    Chromaインデックスを再構築します。
    
    Requirements: 8.3
    """
    if paper_service is None or embedding_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Services are not initialized"
        )
    
    try:
        logger.info(f"Initializing index: force={request.force}")
        
        # 現在のインデックスを取得
        chroma_client = await index_holder.get()
        
        # forceフラグが立っている場合はリセット
        if request.force:
            logger.warning("Force reset requested, resetting index...")
            chroma_client.reset()
        
        # キャッシュディレクトリから全PDFを再インデックス化
        pdf_cache_dir = Path("./cache/pdfs")
        
        if not pdf_cache_dir.exists():
            return InitIndexResponse(
                status="success",
                indexed_count=0,
                message="PDFキャッシュディレクトリが存在しません。"
            )
        
        # RAGServiceを初期化
        from src.services.rag_service import RAGService
        rag_service = RAGService(
            chroma_client=chroma_client,
            embedding_service=embedding_service
        )
        
        # 全PDFを処理
        total_chunks = 0
        pdf_files = list(pdf_cache_dir.glob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDFs to index")
        
        for pdf_path in pdf_files:
            try:
                # ファイル名からarxiv_idを抽出
                arxiv_id = pdf_path.stem.replace("_", "/")
                
                # メタデータを取得
                metadata = await paper_service.get_metadata(arxiv_id)
                
                # テキストを抽出
                text = await paper_service.extract_text(pdf_path)
                
                # インデックス化
                chunks = await rag_service.index_paper(
                    arxiv_id=arxiv_id,
                    text=text,
                    metadata=metadata
                )
                
                total_chunks += chunks
                logger.info(f"Indexed {arxiv_id}: {chunks} chunks")
                
            except Exception as e:
                logger.error(f"Failed to index {pdf_path}: {e}")
                continue
        
        logger.info(f"Index initialization completed: {total_chunks} total chunks")
        
        return InitIndexResponse(
            status="success",
            indexed_count=total_chunks,
            message=f"{len(pdf_files)}個のPDFから{total_chunks}個のチャンクをインデックス化しました。"
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"インデックスの初期化に失敗しました: {str(e)}"
        )


# ルートエンドポイント
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "name": "Papersmith Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }
