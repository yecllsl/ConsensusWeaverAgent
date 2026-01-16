from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.infrastructure.data.data_manager import DataManager
from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.logging.logger import get_logger

# 确保NLTK资源已下载
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

@dataclass
class ConsensusAnalysisResult:
    session_id: int
    similarity_matrix: List[List[float]]
    consensus_scores: Dict[str, float]
    key_points: List[Dict[str, Any]]
    differences: List[Dict[str, Any]]
    comprehensive_summary: str
    final_conclusion: str

class ConsensusAnalyzer:
    def __init__(self, llm_service: LLMService, data_manager: DataManager):
        self.llm_service = llm_service
        self.data_manager = data_manager
        self.logger = get_logger()
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

    def analyze_consensus(self, session_id: int, question: str, tool_results: List[Dict[str, Any]]) -> ConsensusAnalysisResult:
        """分析共识度"""
        self.logger.info(f"开始共识分析，会话ID: {session_id}")
        
        try:
            # 过滤成功的结果
            successful_results = [result for result in tool_results if result['success']]
            if not successful_results:
                self.logger.error("没有成功的工具结果可分析")
                raise ValueError("没有成功的工具结果可分析")
            
            # 计算相似度矩阵
            similarity_matrix = self._calculate_similarity_matrix(successful_results)
            
            # 计算共识度评分
            consensus_scores = self._calculate_consensus_scores(successful_results, similarity_matrix)
            
            # 提取核心观点
            key_points = self._extract_key_points(successful_results)
            
            # 识别分歧点
            differences = self._identify_differences(successful_results)
            
            # 生成综合总结
            comprehensive_summary = self._generate_comprehensive_summary(question, successful_results, key_points, differences)
            
            # 生成最终结论
            final_conclusion = self._generate_final_conclusion(comprehensive_summary, consensus_scores)
            
            # 保存分析结果到数据库
            self.data_manager.save_analysis_result(
                session_id=session_id,
                similarity_matrix=similarity_matrix.tolist(),
                consensus_scores=consensus_scores,
                key_points=key_points,
                differences=differences,
                comprehensive_summary=comprehensive_summary,
                final_conclusion=final_conclusion
            )
            
            result = ConsensusAnalysisResult(
                session_id=session_id,
                similarity_matrix=similarity_matrix.tolist(),
                consensus_scores=consensus_scores,
                key_points=key_points,
                differences=differences,
                comprehensive_summary=comprehensive_summary,
                final_conclusion=final_conclusion
            )
            
            self.logger.info(f"共识分析完成，会话ID: {session_id}")
            
            return result
        except Exception as e:
            self.logger.error(f"共识分析失败: {e}")
            raise

    def _calculate_similarity_matrix(self, tool_results: List[Dict[str, Any]]) -> np.ndarray:
        """计算答案间的相似度矩阵"""
        # 提取所有答案文本
        answers = [result['answer'] for result in tool_results]
        
        # 使用TF-IDF向量化
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(answers)
        
        # 计算余弦相似度矩阵
        similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        return similarity_matrix

    def _calculate_consensus_scores(self, tool_results: List[Dict[str, Any]], similarity_matrix: np.ndarray) -> Dict[str, float]:
        """计算每个答案的共识度评分"""
        consensus_scores = {}
        
        for i, result in enumerate(tool_results):
            # 计算该答案与其他所有答案的平均相似度
            avg_similarity = np.mean(similarity_matrix[i])
            
            # 转换为0-100分
            score = float(avg_similarity * 100)
            
            consensus_scores[result['tool_name']] = round(score, 2)
        
        return consensus_scores

    def _extract_key_points(self, tool_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取核心观点"""
        try:
            # 构建提示
            answers_text = "\n\n".join([f"工具 {result['tool_name']} 的回答: {result['answer']}" for result in tool_results])
            
            prompt = f"""
            请从以下多个工具的回答中提取核心观点：
            
            {answers_text}
            
            核心观点是指多个回答中共同提到的重要信息点。
            
            请以JSON格式返回提取的核心观点，每个观点应包含：
            - content: 观点内容
            - sources: 提到该观点的工具名称列表
            
            请确保提取的观点准确、简洁，并标注所有相关的来源工具。
            """
            
            response = self.llm_service.generate_response(prompt)
            key_points = eval(response)  # 注意：在生产环境中应使用更安全的JSON解析
            
            return key_points
        except Exception as e:
            self.logger.error(f"提取核心观点失败: {e}")
            # 回退到简单的文本分析
            return self._simple_key_point_extraction(tool_results)

    def _simple_key_point_extraction(self, tool_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """简单的核心观点提取（作为LLM提取的回退）"""
        all_words = []
        
        # 预处理所有答案
        for result in tool_results:
            words = self._preprocess_text(result['answer'])
            all_words.extend(words)
        
        # 计算词频
        from collections import Counter
        word_freq = Counter(all_words)
        
        # 提取高频词作为核心观点
        top_words = [word for word, freq in word_freq.most_common(10)]
        
        # 构建核心观点
        key_points = []
        for word in top_words:
            sources = [result['tool_name'] for result in tool_results if word in self._preprocess_text(result['answer'])]
            key_points.append({
                "content": word,
                "sources": sources
            })
        
        return key_points

    def _identify_differences(self, tool_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别分歧点"""
        try:
            # 构建提示
            answers_text = "\n\n".join([f"工具 {result['tool_name']} 的回答: {result['answer']}" for result in tool_results])
            
            prompt = f"""
            请识别以下多个工具回答中的分歧点：
            
            {answers_text}
            
            分歧点是指不同回答之间相互矛盾或存在明显差异的信息点。
            
            请以JSON格式返回识别的分歧点，每个分歧点应包含：
            - content: 分歧内容
            - sources: 存在分歧的工具名称列表
            
            请确保识别的分歧点准确，并标注所有相关的来源工具。
            """
            
            response = self.llm_service.generate_response(prompt)
            differences = eval(response)  # 注意：在生产环境中应使用更安全的JSON解析
            
            return differences
        except Exception as e:
            self.logger.error(f"识别分歧点失败: {e}")
            return []

    def _generate_comprehensive_summary(self, question: str, tool_results: List[Dict[str, Any]], key_points: List[Dict[str, Any]], differences: List[Dict[str, Any]]) -> str:
        """生成综合总结"""
        try:
            # 构建提示
            key_points_text = "\n\n".join([f"- {point['content']}（来源：{', '.join(point['sources'])}）" for point in key_points])
            differences_text = "\n\n".join([f"- {point['content']}（来源：{', '.join(point['sources'])}）" for point in differences]) if differences else "无明显分歧"
            
            prompt = f"""
            请根据以下信息生成一份综合总结：
            
            问题：{question}
            
            核心观点：
            {key_points_text}
            
            分歧点：
            {differences_text}
            
            请生成一份结构清晰、逻辑连贯的综合总结，涵盖所有核心观点和分歧点，并保持客观中立。
            """
            
            return self.llm_service.generate_response(prompt)
        except Exception as e:
            self.logger.error(f"生成综合总结失败: {e}")
            return "综合总结生成失败"

    def _generate_final_conclusion(self, comprehensive_summary: str, consensus_scores: Dict[str, float]) -> str:
        """生成最终结论"""
        try:
            # 构建提示
            scores_text = "\n".join([f"- {tool}: {score}分" for tool, score in consensus_scores.items()])
            
            prompt = f"""
            请根据以下综合总结和共识度评分生成最终结论：
            
            综合总结：
            {comprehensive_summary}
            
            共识度评分：
            {scores_text}
            
            请生成一份简洁明了的最终结论，指出最可靠的信息，并根据共识度评分给出建议。
            """
            
            return self.llm_service.generate_response(prompt)
        except Exception as e:
            self.logger.error(f"生成最终结论失败: {e}")
            return "最终结论生成失败"

    def _preprocess_text(self, text: str) -> List[str]:
        """预处理文本"""
        # 分词
        words = word_tokenize(text.lower())
        
        # 过滤停用词和非字母字符
        filtered_words = [word for word in words if word.isalpha() and word not in self.stop_words]
        
        # 词形还原
        lemmatized_words = [self.lemmatizer.lemmatize(word) for word in filtered_words]
        
        return lemmatized_words

    def get_analysis_result(self, session_id: int) -> Optional[ConsensusAnalysisResult]:
        """获取会话的分析结果"""
        db_result = self.data_manager.get_analysis_result(session_id)
        if not db_result:
            return None
        
        return ConsensusAnalysisResult(
            session_id=db_result.session_id,
            similarity_matrix=db_result.similarity_matrix,
            consensus_scores=db_result.consensus_scores,
            key_points=db_result.key_points,
            differences=db_result.differences,
            comprehensive_summary=db_result.comprehensive_summary,
            final_conclusion=db_result.final_conclusion
        )
