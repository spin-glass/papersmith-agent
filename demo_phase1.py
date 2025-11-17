#!/usr/bin/env python3
"""
Phase 1 機能デモスクリプト

実際に各機能を動かして結果を出力します。
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.clients.arxiv_client import ArxivClient
from src.clients.chroma_client import ChromaClient
from src.services.paper_service import PaperService
from src.services.embedding_service import EmbeddingService
from src.services.rag_service import RAGService, basic_rag_query, build_context
from src.models.config import ChromaConfig, EmbeddingConfig


def print_section(title):
    """セクションタイトルを表示"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(label, value, indent=0):
    """結果を整形して表示"""
    prefix = "  " * indent
    if isinstance(value, list):
        print(f"{prefix}✓ {label}: {len(value)}件")
        for i, item in enumerate(value[:3], 1):  # 最初の3件のみ表示
            print(f"{prefix}  {i}. {item}")
        if len(value) > 3:
            print(f"{prefix}  ... 他{len(value) - 3}件")
    elif isinstance(value, str) and len(value) > 100:
        print(f"{prefix}✓ {label}: {len(value)}文字")
        print(f"{prefix}  {value[:100]}...")
    else:
        print(f"{prefix}✓ {label}: {value}")


async def demo_1_arxiv_search():
    """デモ1: arXiv論文検索"""
    print_section("デモ1: arXiv論文検索")
    
    # ArxivClientを初期化
    arxiv_client = ArxivClient(
        cache_dir=Path("./demo_cache/pdfs"),
        max_retries=3,
        timeout=30
    )
    
    # 論文を検索
    print("🔍 検索クエリ: 'machine learning'")
    papers = await arxiv_client.search_papers("machine learning", max_results=3)
    
    print_result("検索結果", papers)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n📄 論文 {i}:")
        print_result("arXiv ID", paper.arxiv_id, indent=1)
        print_result("タイトル", paper.title, indent=1)
        print_result("著者", ", ".join(paper.authors[:3]), indent=1)
        print_result("発行年", paper.year, indent=1)
        print_result("カテゴリ", ", ".join(paper.categories), indent=1)
        print_result("要旨", paper.abstract[:150] + "...", indent=1)
    
    return papers[0] if papers else None


async def demo_2_pdf_download(paper):
    """デモ2: PDF取得とテキスト抽出"""
    print_section("デモ2: PDF取得とテキスト抽出")
    
    if not paper:
        print("⚠️ 論文が見つかりませんでした")
        return None
    
    # PaperServiceを初期化
    arxiv_client = ArxivClient(cache_dir=Path("./demo_cache/pdfs"))
    paper_service = PaperService(
        arxiv_client=arxiv_client,
        cache_dir=Path("./demo_cache")
    )
    
    print(f"📥 PDFをダウンロード: {paper.arxiv_id}")
    pdf_path = await paper_service.download_pdf(paper.arxiv_id, paper.pdf_url)
    print_result("PDF保存先", str(pdf_path))
    print_result("ファイルサイズ", f"{pdf_path.stat().st_size / 1024:.1f} KB")
    
    print(f"\n📝 テキストを抽出中...")
    text = await paper_service.extract_text(pdf_path)
    print_result("抽出テキスト", text)
    
    return text


async def demo_3_text_processing(text):
    """デモ3: テキスト処理（セクション分割とチャンク化）"""
    print_section("デモ3: テキスト処理")
    
    if not text:
        print("⚠️ テキストがありません")
        return None
    
    # RAGServiceを初期化（Embedding不要）
    chroma_config = ChromaConfig(
        persist_dir=Path("./demo_cache/chroma"),
        collection_name="demo_collection"
    )
    chroma_client = ChromaClient(chroma_config)
    chroma_client.initialize()
    
    embedding_config = EmbeddingConfig(device="cpu")
    embedding_service = EmbeddingService(embedding_config)
    
    rag_service = RAGService(
        chroma_client=chroma_client,
        embedding_service=embedding_service
    )
    
    # IMRaD構造でセクション分割
    print("📑 IMRaD構造でセクション分割中...")
    sections = rag_service._split_by_imrad(text)
    print_result("検出されたセクション", list(sections.keys()))
    
    for section_name, section_text in sections.items():
        if section_text.strip():
            print(f"\n  📌 {section_name.upper()}:")
            print_result("文字数", len(section_text), indent=2)
            print_result("プレビュー", section_text[:100].strip(), indent=2)
    
    # テキストをチャンク化
    print("\n✂️ テキストをチャンク化中...")
    all_chunks = []
    for section_name, section_text in sections.items():
        if section_text.strip():
            chunks = rag_service._chunk_text(section_text, chunk_size=300)
            all_chunks.extend(chunks)
            print_result(f"{section_name}のチャンク数", len(chunks), indent=1)
    
    print_result("\n合計チャンク数", len(all_chunks))
    
    # 最初の3チャンクを表示
    print("\n📦 チャンクのサンプル:")
    for i, chunk in enumerate(all_chunks[:3], 1):
        print(f"\n  チャンク {i} ({len(chunk)}文字):")
        print(f"    {chunk[:100]}...")
    
    return all_chunks


async def demo_4_embedding_and_indexing(paper, text):
    """デモ4: Embedding生成とインデックス化"""
    print_section("デモ4: Embedding生成とインデックス化")
    
    if not text or not paper:
        print("⚠️ データがありません")
        return None
    
    # サービスを初期化
    chroma_config = ChromaConfig(
        persist_dir=Path("./demo_cache/chroma"),
        collection_name="demo_collection"
    )
    chroma_client = ChromaClient(chroma_config)
    chroma_client.initialize()
    
    embedding_config = EmbeddingConfig(device="cpu")
    embedding_service = EmbeddingService(embedding_config)
    
    print("🔧 Embeddingモデルをロード中...")
    await embedding_service.load_model()
    print_result("モデル名", embedding_service.config.model_name)
    print_result("Embedding次元", embedding_service.get_embedding_dimension())
    
    # RAGServiceを初期化
    rag_service = RAGService(
        chroma_client=chroma_client,
        embedding_service=embedding_service
    )
    
    # 論文をインデックス化
    print(f"\n📊 論文をインデックス化中: {paper.arxiv_id}")
    chunk_count = await rag_service.index_paper(
        arxiv_id=paper.arxiv_id,
        text=text,
        metadata=paper,
        chunk_size=300
    )
    
    print_result("インデックス化されたチャンク数", chunk_count)
    print_result("Chromaに保存されたドキュメント数", chroma_client.count())
    
    return rag_service


async def demo_5_vector_search(rag_service, paper):
    """デモ5: ベクター検索"""
    print_section("デモ5: ベクター検索")
    
    if not rag_service or not paper:
        print("⚠️ RAGサービスが初期化されていません")
        return None
    
    # 検索クエリ
    queries = [
        "What is the main contribution of this paper?",
        "What methods are used in this research?",
        "What are the experimental results?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 検索 {i}: {query}")
        
        results = await rag_service.query(
            question=query,
            arxiv_ids=[paper.arxiv_id],
            top_k=3
        )
        
        print_result("検索結果", f"{len(results)}件")
        
        for j, result in enumerate(results, 1):
            print(f"\n  結果 {j}:")
            print_result("スコア", f"{result.score:.4f}", indent=2)
            print_result("セクション", result.metadata.get("section", "unknown"), indent=2)
            print_result("テキスト", result.text[:100], indent=2)
    
    return results


async def demo_6_context_building(rag_service, paper):
    """デモ6: RAGコンテキスト構築"""
    print_section("デモ6: RAGコンテキスト構築")
    
    if not rag_service or not paper:
        print("⚠️ RAGサービスが初期化されていません")
        return
    
    # 質問
    question = "What is the main contribution and methodology of this paper?"
    print(f"❓ 質問: {question}")
    
    # ベクター検索
    print("\n🔍 関連チャンクを検索中...")
    results = await rag_service.query(
        question=question,
        arxiv_ids=[paper.arxiv_id],
        top_k=5
    )
    
    print_result("検索結果", f"{len(results)}件")
    
    # コンテキスト構築
    print("\n📝 コンテキストを構築中...")
    context = build_context(results)
    
    print_result("コンテキスト文字数", len(context))
    print("\n📄 構築されたコンテキスト:")
    print("-" * 80)
    print(context[:500])
    print("...")
    print("-" * 80)
    
    print("\n✅ RAGパイプライン完了！")
    print("   (LLMによる回答生成は、モデルが重いため省略)")


async def main():
    """メイン実行"""
    print("\n" + "🚀" * 40)
    print("  Phase 1 機能デモ - Papersmith Agent")
    print("🚀" * 40)
    
    try:
        # デモ1: 論文検索
        paper = await demo_1_arxiv_search()
        
        if not paper:
            print("\n⚠️ 論文が見つからなかったため、デモを終了します")
            return
        
        # デモ2: PDF取得とテキスト抽出
        text = await demo_2_pdf_download(paper)
        
        if not text:
            print("\n⚠️ テキスト抽出に失敗したため、デモを終了します")
            return
        
        # デモ3: テキスト処理
        chunks = await demo_3_text_processing(text)
        
        # デモ4: Embedding生成とインデックス化
        rag_service = await demo_4_embedding_and_indexing(paper, text)
        
        if not rag_service:
            print("\n⚠️ インデックス化に失敗したため、デモを終了します")
            return
        
        # デモ5: ベクター検索
        results = await demo_5_vector_search(rag_service, paper)
        
        # デモ6: コンテキスト構築
        await demo_6_context_building(rag_service, paper)
        
        print("\n" + "🎉" * 40)
        print("  Phase 1 全機能デモ完了！")
        print("🎉" * 40 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
