"""共识分析器（新版本）

本模块实现了共识分析器，使用新的数据仓库架构和事务管理。
"""

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List

import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.infrastructure.data.retry_handler import RetryHandler
from src.infrastructure.data.transaction_manager import TransactionManager
from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.logging.logger import get_logger
from src.models.entities import AnalysisResult

# 添加常见的NLTK数据路径
common_data_paths = [
    os.path.expanduser("~/.nltk_data"),
    os.path.join(sys.prefix, "nltk_data"),
    os.path.join(os.environ.get("APPDATA", ""), "nltk_data"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "nltk_data"),
]

for path in common_data_paths:
    if path and os.path.exists(path):
        if path not in nltk.data.path:
            nltk.data.path.append(path)


@dataclass
class ConsensusAnalysisResult:
    """共识分析结果"""

    session_id: int
    similarity_matrix: List[List[float]]
    consensus_scores: Dict[str, float]
    key_points: List[Dict[str, Any]]
    differences: List[Dict[str, Any]]
    comprehensive_summary: str
    final_conclusion: str


class ConsensusAnalyzerV2:
    """共识分析器（新版本）

    使用新的数据仓库架构和事务管理，提供更好的数据一致性保证。
    """

    def __init__(
        self,
        llm_service: LLMService,
        transaction_manager: TransactionManager,
    ):
        self.llm_service = llm_service
        self.transaction_manager = transaction_manager
        self.logger = get_logger()
        self.retry_handler = RetryHandler(max_retries=3, base_delay=1.0)
        self._init_nltk()

    def _init_nltk(self):
        """初始化NLTK组件"""
        try:
            self.stop_words = set(stopwords.words("english"))
            self.lemmatizer = WordNetLemmatizer()
            self.vectorizer = TfidfVectorizer(
                tokenizer=self._custom_tokenizer,
                stop_words="english",
                max_features=1000,
            )
        except Exception as e:
            self.logger.warning(f"NLTK初始化失败: {e}")
            self.stop_words = set()
            self.lemmatizer = None
            self.vectorizer = None

    def _custom_tokenizer(self, text: str) -> List[str]:
        """自定义文本分词器"""
        try:
            tokens = word_tokenize(text.lower())
            if self.lemmatizer:
                tokens = [
                    self.lemmatizer.lemmatize(token)
                    for token in tokens
                    if token.isalpha() and token not in self.stop_words
                ]
            else:
                tokens = [token for token in tokens if token.isalpha()]
            return tokens
        except Exception:
            return text.lower().split()

    async def analyze_consensus(
        self, session_id: int, question: str, tool_results: List[Dict[str, Any]]
    ) -> ConsensusAnalysisResult:
        """分析多个工具结果的共识（使用事务管理）"""
        self.logger.info(
            f"开始共识分析，会话ID: {session_id}, 结果数量: {len(tool_results)}"
        )

        try:
            # 过滤成功的工具结果
            successful_results = [
                result for result in tool_results if result.get("success", False)
            ]

            if len(successful_results) < 2:
                self.logger.warning(
                    f"成功结果不足，无法进行共识分析，会话ID: {session_id}"
                )
                return self._create_default_result(session_id)

            # 计算相似度矩阵
            similarity_matrix = self._calculate_similarity_matrix(successful_results)

            # 计算共识得分
            consensus_scores = self._calculate_consensus_scores(
                successful_results, similarity_matrix
            )

            # 提取核心
            key_points = self._extract_key_points(successful_results)

            # 识别分歧点
            differences = self._identify_differences(successful_results)

            # 生成综合总结
            comprehensive_summary = self._generate_comprehensive_summary(
                question, successful_results, key_points, differences
            )

            # 生成最终结论
            final_conclusion = self._generate_final_conclusion(
                comprehensive_summary, consensus_scores
            )

            # 使用事务保存分析结果
            await self._save_analysis_result_with_transaction(
                session_id=session_id,
                similarity_matrix=similarity_matrix.tolist(),
                consensus_scores=consensus_scores,
                key_points=key_points,
                differences=differences,
                comprehensive_summary=comprehensive_summary,
                final_conclusion=final_conclusion,
            )

            result = ConsensusAnalysisResult(
                session_id=session_id,
                similarity_matrix=similarity_matrix.tolist(),
                consensus_scores=consensus_scores,
                key_points=key_points,
                differences=differences,
                comprehensive_summary=comprehensive_summary,
                final_conclusion=final_conclusion,
            )

            self.logger.info(f"共识分析完成，会话ID: {session_id}")

            return result
        except Exception as e:
            self.logger.error(f"共识分析失败: {e}")
            raise

    async def _save_analysis_result_with_transaction(
        self,
        session_id: int,
        similarity_matrix: List[List[float]],
        consensus_scores: Dict[str, float],
        key_points: List[Dict[str, Any]],
        differences: List[Dict[str, Any]],
        comprehensive_summary: str,
        final_conclusion: str,
    ) -> None:
        """使用事务保存分析结果"""
        async with self.transaction_manager.begin_transaction() as uow:
            entity = AnalysisResult(
                session_id=session_id,
                similarity_matrix=similarity_matrix,
                consensus_scores=consensus_scores,
                key_points=key_points,
                differences=differences,
                comprehensive_summary=comprehensive_summary,
                final_conclusion=final_conclusion,
            )

            await uow.analysis_results.add(entity)
            await uow.commit()

    def _calculate_similarity_matrix(
        self, tool_results: List[Dict[str, Any]]
    ) -> np.ndarray:
        """计算工具结果之间的相似度矩阵"""
        try:
            answers = [result.get("answer", "") for result in tool_results]

            if not self.vectorizer:
                return np.ones((len(answers), len(answers)))

            tfidf_matrix = self.vectorizer.fit_transform(answers)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            return similarity_matrix
        except Exception as e:
            self.logger.error(f"计算相似度矩阵失败: {e}")
            return np.ones((len(tool_results), len(tool_results)))

    def _calculate_consensus_scores(
        self, tool_results: List[Dict[str, Any]], similarity_matrix: np.ndarray
    ) -> Dict[str, float]:
        """计算每个工具的共识得分"""
        try:
            scores = {}
            for i, result in enumerate(tool_results):
                tool_name = result.get("tool_name", f"tool_{i}")
                avg_similarity = np.mean(similarity_matrix[i])
                scores[tool_name] = float(avg_similarity)
            return scores
        except Exception as e:
            self.logger.error(f"计算共识得分失败: {e}")
            return {}

    def _extract_key_points(
        self, tool_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """从工具结果中提取核心观点"""
        try:
            key_points = []
            for result in tool_results:
                tool_name = result.get("tool_name", "unknown")
                answer = result.get("answer", "")
                if answer:
                    key_points.append(
                        {
                            "source": tool_name,
                            "point": answer[:200],
                        }
                    )
            return key_points
        except Exception as e:
            self.logger.error(f"提取核心观点失败: {e}")
            return []

    def _identify_differences(
        self, tool_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别工具结果之间的分歧点"""
        try:
            differences = []
            if len(tool_results) < 2:
                return differences

            for i in range(len(tool_results)):
                for j in range(i + 1, len(tool_results)):
                    tool1 = tool_results[i].get("tool_name", "unknown")
                    tool2 = tool_results[j].get("tool_name", "unknown")
                    answer1 = tool_results[i].get("answer", "")
                    answer2 = tool_results[j].get("answer", "")

                    if answer1 and answer2 and answer1 != answer2:
                        differences.append(
                            {
                                "tools": [tool1, tool2],
                                "description": f"{tool1}和{tool2}的结果存在差异",
                            }
                        )
            return differences
        except Exception as e:
            self.logger.error(f"识别分歧点失败: {e}")
            return []

    def _generate_comprehensive_summary(
        self,
        question: str,
        tool_results: List[Dict[str, Any]],
        key_points: List[Dict[str, Any]],
        differences: List[Dict[str, Any]],
    ) -> str:
        """生成综合总结"""
        try:
            summary_parts = [
                f"问题: {question}",
                f"共分析了 {len(tool_results)} 个工具的结果",
            ]

            if key_points:
                summary_parts.append("核心观点:")
                for point in key_points[:3]:
                    summary_parts.append(f"- {point['source']}: {point['point']}")

            if differences:
                summary_parts.append("主要分歧:")
                for diff in differences[:2]:
                    summary_parts.append(f"- {diff['description']}")

            return "\n".join(summary_parts)
        except Exception as e:
            self.logger.error(f"生成综合总结失败: {e}")
            return f"分析问题: {question}"

    def _generate_final_conclusion(
        self, summary: str, consensus_scores: Dict[str, float]
    ) -> str:
        """生成最终结论"""
        try:
            if not consensus_scores:
                return "由于数据不足，无法生成可靠的结论。"

            avg_score = sum(consensus_scores.values()) / len(consensus_scores)

            if avg_score > 0.7:
                conclusion = "各工具结果高度一致，结论可信度高。"
            elif avg_score > 0.5:
                conclusion = "各工具结果基本一致，但存在一定差异。"
            else:
                conclusion = "各工具结果存在较大差异，建议进一步验证。"

            return conclusion
        except Exception as e:
            self.logger.error(f"生成最终结论失败: {e}")
            return "无法生成结论。"

    def _create_default_result(self, session_id: int) -> ConsensusAnalysisResult:
        """创建默认结果"""
        return ConsensusAnalysisResult(
            session_id=session_id,
            similarity_matrix=[[1.0]],
            consensus_scores={},
            key_points=[],
            differences=[],
            comprehensive_summary="数据不足，无法进行共识分析。",
            final_conclusion="无法生成结论。",
        )
