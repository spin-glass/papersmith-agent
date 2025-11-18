"""モックAPIレスポンスデータ

Requirements: Testing Strategy - Mocking Strategy
"""

from typing import Any

# arXiv API レスポンスのモック
ARXIV_SEARCH_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>ArXiv Query: machine learning</title>
  <id>http://arxiv.org/api/query?search_query=machine+learning&amp;id_list=&amp;start=0&amp;max_results=2</id>
  <updated>2023-01-01T00:00:00-05:00</updated>
  <opensearch:totalResults xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">2</opensearch:totalResults>
  <opensearch:startIndex xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">0</opensearch:startIndex>
  <opensearch:itemsPerPage xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">2</opensearch:itemsPerPage>
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <updated>2023-01-01T00:00:00Z</updated>
    <published>2023-01-01T00:00:00Z</published>
    <title>Example Paper: A Novel Approach to Machine Learning</title>
    <summary>This paper presents a novel approach to machine learning that improves accuracy by 15%.</summary>
    <author>
      <name>Alice Smith</name>
    </author>
    <author>
      <name>Bob Johnson</name>
    </author>
    <arxiv:doi xmlns:arxiv="http://arxiv.org/schemas/atom">10.1234/example.2023.00001</arxiv:doi>
    <link href="http://arxiv.org/abs/2301.00001v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2301.00001v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2301.00002v1</id>
    <updated>2023-01-02T00:00:00Z</updated>
    <published>2023-01-02T00:00:00Z</published>
    <title>Deep Learning for Computer Vision</title>
    <summary>A comprehensive survey of deep learning techniques for computer vision tasks.</summary>
    <author>
      <name>Carol Williams</name>
    </author>
    <link href="http://arxiv.org/abs/2301.00002v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2301.00002v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.CV" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.CV" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""


ARXIV_PAPER_METADATA = {
    "arxiv_id": "2301.00001",
    "title": "Example Paper: A Novel Approach to Machine Learning",
    "authors": ["Alice Smith", "Bob Johnson", "Carol Williams"],
    "abstract": "This paper presents a novel approach to machine learning that improves accuracy by 15%.",
    "year": 2023,
    "categories": ["cs.AI", "cs.LG"],
    "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
    "doi": "10.1234/example.2023.00001",
    "published_date": "2023-01-01T00:00:00Z"
}


# Gemini API レスポンスのモック
GEMINI_GENERATE_RESPONSE = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": "この論文では、機械学習の新しいアプローチを提案しています。提案手法は、深層学習と強化学習を組み合わせることで、従来手法と比較して15%の精度向上を実現しました。"
                    }
                ],
                "role": "model"
            },
            "finishReason": "STOP",
            "index": 0,
            "safetyRatings": []
        }
    ]
}


GEMINI_EMBEDDING_RESPONSE = {
    "embedding": [0.1] * 768  # 768次元のダミーEmbedding
}


GEMINI_BATCH_EMBEDDING_RESPONSE = [
    {"embedding": [0.1] * 768},
    {"embedding": [0.2] * 768},
    {"embedding": [0.3] * 768}
]


# OpenAI API レスポンスのモック
OPENAI_CHAT_COMPLETION_RESPONSE = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "この論文では、機械学習の新しいアプローチを提案しています。提案手法は、深層学習と強化学習を組み合わせることで、従来手法と比較して15%の精度向上を実現しました。"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150
    }
}


OPENAI_EMBEDDING_RESPONSE = {
    "object": "list",
    "data": [
        {
            "object": "embedding",
            "embedding": [0.1] * 1536,  # text-embedding-3-small dimension
            "index": 0
        }
    ],
    "model": "text-embedding-3-small",
    "usage": {
        "prompt_tokens": 10,
        "total_tokens": 10
    }
}


OPENAI_BATCH_EMBEDDING_RESPONSE = {
    "object": "list",
    "data": [
        {
            "object": "embedding",
            "embedding": [0.1] * 1536,
            "index": 0
        },
        {
            "object": "embedding",
            "embedding": [0.2] * 1536,
            "index": 1
        },
        {
            "object": "embedding",
            "embedding": [0.3] * 1536,
            "index": 2
        }
    ],
    "model": "text-embedding-3-small",
    "usage": {
        "prompt_tokens": 30,
        "total_tokens": 30
    }
}


# サンプルPDFテキスト（IMRaD構造）
SAMPLE_PDF_TEXT = """
Example Paper: A Novel Approach to Machine Learning

Alice Smith, Bob Johnson, Carol Williams
Department of Computer Science, Example University

Abstract
This paper presents a novel approach to machine learning that improves accuracy by 15%.
We combine deep learning with reinforcement learning to create a more robust algorithm.
Experiments on three benchmark datasets demonstrate the effectiveness of our approach.

1. Introduction
Machine learning has become increasingly important in recent years. However, existing
approaches have limitations in handling complex, high-dimensional data. This paper
addresses these limitations by proposing a new algorithm that combines the strengths
of deep learning and reinforcement learning.

The main contributions of this paper are:
- A novel algorithm that combines deep learning and reinforcement learning
- Comprehensive experiments on three benchmark datasets
- Analysis of the algorithm's performance and scalability

2. Related Work
Previous work in machine learning has focused on either deep learning or reinforcement
learning separately. Smith et al. (2020) proposed a deep learning approach that achieved
good results on image classification tasks. Johnson et al. (2021) developed a reinforcement
learning method for sequential decision making.

3. Methods
We propose a new algorithm that consists of three main components:

3.1 Feature Extraction
The feature extraction component uses a convolutional neural network (CNN) to extract
high-level features from raw input data. The CNN architecture consists of 5 convolutional
layers followed by 2 fully connected layers.

3.2 Policy Learning
The policy learning component uses a reinforcement learning algorithm to learn an optimal
policy based on the extracted features. We use the Proximal Policy Optimization (PPO)
algorithm with a learning rate of 0.001.

3.3 Reward Optimization
The reward optimization component adjusts the reward function dynamically based on the
current performance. This allows the algorithm to adapt to different tasks and datasets.

4. Results
We evaluated our algorithm on three benchmark datasets: MNIST, CIFAR-10, and ImageNet.

4.1 MNIST Results
On the MNIST dataset, our algorithm achieved 99.2% accuracy, which is 2% higher than
the baseline deep learning approach.

4.2 CIFAR-10 Results
On CIFAR-10, we achieved 92.5% accuracy, representing a 5% improvement over the baseline.

4.3 ImageNet Results
On ImageNet, our algorithm achieved 78.3% top-1 accuracy and 94.1% top-5 accuracy,
which is 8% higher than the baseline for top-1 accuracy.

5. Discussion
The results demonstrate the effectiveness of our approach across different types of datasets.
The improvement is particularly significant on complex datasets like ImageNet, where the
combination of deep learning and reinforcement learning provides substantial benefits.

5.1 Computational Efficiency
Our algorithm requires approximately 20% more computation time than baseline deep learning
approaches, but the accuracy improvement justifies this additional cost.

5.2 Scalability
We tested the algorithm's scalability by varying the dataset size and model complexity.
The results show that the algorithm scales well to large datasets and complex models.

6. Conclusion
We presented a novel approach to machine learning that combines deep learning with
reinforcement learning. The proposed algorithm achieves significant accuracy improvements
on three benchmark datasets. Future work will explore applications to other domains such
as natural language processing and robotics.

Acknowledgments
This work was supported by the National Science Foundation under Grant No. 12345.

References
[1] Smith, A. et al. (2020). Deep Learning for Image Classification. ICML 2020.
[2] Johnson, B. et al. (2021). Reinforcement Learning for Sequential Decisions. NeurIPS 2021.
"""


# サンプルチャンクデータ
SAMPLE_CHUNKS = [
    {
        "text": "This paper presents a novel approach to machine learning that improves accuracy by 15%.",
        "section": "abstract",
        "chunk_id": 0,
        "metadata": {
            "arxiv_id": "2301.00001",
            "title": "Example Paper",
            "year": 2023
        }
    },
    {
        "text": "Machine learning has become increasingly important in recent years. However, existing approaches have limitations.",
        "section": "introduction",
        "chunk_id": 0,
        "metadata": {
            "arxiv_id": "2301.00001",
            "title": "Example Paper",
            "year": 2023
        }
    },
    {
        "text": "We propose a new algorithm that combines deep learning with reinforcement learning.",
        "section": "methods",
        "chunk_id": 0,
        "metadata": {
            "arxiv_id": "2301.00001",
            "title": "Example Paper",
            "year": 2023
        }
    },
    {
        "text": "Our experiments show that the proposed algorithm achieves 15% higher accuracy than baseline methods.",
        "section": "results",
        "chunk_id": 0,
        "metadata": {
            "arxiv_id": "2301.00001",
            "title": "Example Paper",
            "year": 2023
        }
    },
    {
        "text": "The results demonstrate the effectiveness of our approach. The improvement is particularly significant on complex datasets.",
        "section": "discussion",
        "chunk_id": 0,
        "metadata": {
            "arxiv_id": "2301.00001",
            "title": "Example Paper",
            "year": 2023
        }
    }
]


# エラーレスポンスのモック
ARXIV_ERROR_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>ArXiv Query Error</title>
  <id>http://arxiv.org/api/query</id>
  <updated>2023-01-01T00:00:00-05:00</updated>
  <opensearch:totalResults xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">0</opensearch:totalResults>
</feed>
"""


GEMINI_ERROR_RESPONSE = {
    "error": {
        "code": 400,
        "message": "Invalid request",
        "status": "INVALID_ARGUMENT"
    }
}


OPENAI_ERROR_RESPONSE = {
    "error": {
        "message": "Invalid API key",
        "type": "invalid_request_error",
        "param": None,
        "code": "invalid_api_key"
    }
}


# ヘルパー関数
def create_mock_arxiv_result(arxiv_id: str, title: str, authors: list[str]) -> dict[str, Any]:
    """モックarXiv検索結果を生成

    Args:
        arxiv_id: arXiv ID
        title: 論文タイトル
        authors: 著者リスト

    Returns:
        モック検索結果
    """
    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": f"Abstract for {title}",
        "year": 2023,
        "categories": ["cs.AI"],
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        "published_date": "2023-01-01T00:00:00Z"
    }


def create_mock_embedding(dimension: int = 768, seed: int = 0) -> list[float]:
    """モックEmbeddingを生成

    Args:
        dimension: Embedding次元数
        seed: ランダムシード

    Returns:
        モックEmbedding
    """
    import random
    random.seed(seed)
    return [random.random() for _ in range(dimension)]


def create_mock_search_result(
    chunk_id: str,
    text: str,
    score: float,
    arxiv_id: str = "2301.00001"
) -> dict[str, Any]:
    """モック検索結果を生成

    Args:
        chunk_id: チャンクID
        text: チャンクテキスト
        score: スコア
        arxiv_id: arXiv ID

    Returns:
        モック検索結果
    """
    return {
        "chunk_id": chunk_id,
        "text": text,
        "score": score,
        "metadata": {
            "arxiv_id": arxiv_id,
            "title": "Example Paper",
            "year": 2023,
            "section": chunk_id.split("_")[1] if "_" in chunk_id else "unknown"
        }
    }
