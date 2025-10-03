from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
import os

from app.core.gemini_client import GeminiClient
from app.core.enhanced_document_parser import EnhancedDocumentParser
from app.core.gemini_extractor import GeminiMetadataExtractor
from app.core.gemini_query_parser import GeminiQueryParser
from app.core.local_file_manager import LocalFileManager
from app.core.cache_manager import CacheManager
from app.core.vector_store import VectorStoreManager
from app.core.retriever import Retriever
from app.core.filter import HardFilter
from app.core.scorer import Scorer
from app.core.ranker import Ranker
from app.core.analyzer import CandidateAnalyzer
from app.core.result_formatter import ResultFormatter
from app.models.metadata import ResumeMetadata, QueryMetadata


class LocalResumeScreener:
    """
    本地简历筛选器 - 主要业务逻辑类
    """
    
    def __init__(self, 
                 resume_directories: List[str] = None,
                 gemini_api_key: str = None,
                 cache_directory: str = "./cache",
                 vector_db_directory: str = "./vector_db"):
        """
        初始化本地简历筛选器
        
        Args:
            resume_directories (List[str]): 简历文件夹路径列表
            gemini_api_key (str): Gemini API密钥
            cache_directory (str): 缓存目录
            vector_db_directory (str): 向量数据库目录
        """
        # 设置环境变量
        if gemini_api_key:
            os.environ["GEMINI_API_KEY"] = gemini_api_key
        
        # 初始化核心组件
        self.cache_manager = CacheManager(cache_directory)
        self.gemini_client = GeminiClient()
        self.document_parser = EnhancedDocumentParser(self.cache_manager)
        self.metadata_extractor = GeminiMetadataExtractor(self.gemini_client, self.cache_manager)
        self.query_parser = GeminiQueryParser(self.gemini_client)
        self.file_manager = LocalFileManager(resume_directories)
        self.vector_store_manager = VectorStoreManager(vector_db_directory)
        self.retriever = Retriever(self.vector_store_manager)
        self.hard_filter = HardFilter()
        self.scorer = Scorer()
        self.ranker = Ranker()
        self.candidate_analyzer = CandidateAnalyzer(self.gemini_client)
        self.result_formatter = ResultFormatter()
        
        # 存储处理过的简历
        self.processed_resumes = {}
        
        logger.info("Initialized LocalResumeScreener")

    def scan_and_process_resumes(self, directories: List[str] = None, recursive: bool = True) -> Dict[str, Any]:
        """
        扫描并处理本地简历文件
        
        Args:
            directories (List[str], optional): 要扫描的目录列表
            recursive (bool): 是否递归扫描子目录
            
        Returns:
            Dict[str, Any]: 处理结果统计
        """
        try:
            # 扫描简历文件
            if directories:
                file_paths = self.file_manager.scan_multiple_directories(directories, recursive)
            else:
                file_paths = self.file_manager.scan_multiple_directories(
                    self.file_manager.watch_directories, recursive)
            
            if not file_paths:
                logger.warning("No resume files found")
                return {"processed": 0, "failed": 0, "total": 0}
            
            processed_count = 0
            failed_count = 0
            
            for file_path in file_paths:
                try:
                    result = self._process_single_resume(file_path)
                    if result:
                        processed_count += 1
                        logger.info(f"Successfully processed: {file_path}")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to process: {file_path}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing {file_path}: {e}")
            
            stats = {
                "processed": processed_count,
                "failed": failed_count,
                "total": len(file_paths),
                "success_rate": processed_count / len(file_paths) if file_paths else 0
            }
            
            logger.info(f"Processing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to scan and process resumes: {e}")
            raise

    def _process_single_resume(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        处理单个简历文件
        
        Args:
            file_path (str): 简历文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 处理结果
        """
        try:
            # 检查文件是否已处理过
            file_info = self.file_manager.get_file_info(file_path)
            if not file_info:
                self.file_manager._update_file_index(file_path)
                file_info = self.file_manager.get_file_info(file_path)
            
            file_hash = file_info.get('hash', '')
            if file_hash in self.processed_resumes:
                logger.info(f"Resume already processed: {file_path}")
                return self.processed_resumes[file_hash]
            
            # 解析文档
            resume_text = self.document_parser.parse_document(file_path)
            if not resume_text.strip():
                logger.warning(f"Empty text extracted from: {file_path}")
                return None
            
            # 提取元数据
            metadata = self.metadata_extractor.extract_metadata(resume_text)
            
            # 生成简历ID
            resume_id = f"resume_{file_hash[:8]}"
            
            # 存储到向量数据库
            self.retriever.add_resume(resume_id, resume_text, metadata.dict())
            
            # 保存处理结果
            result = {
                "id": resume_id,
                "file_path": file_path,
                "file_hash": file_hash,
                "text": resume_text,
                "metadata": metadata.dict(),
                "file_info": file_info
            }
            
            self.processed_resumes[file_hash] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process resume {file_path}: {e}")
            return None

    def screen_resumes(self, query_text: str, top_k: int = 10) -> Dict[str, Any]:
        """
        筛选简历
        
        Args:
            query_text (str): 自然语言查询
            top_k (int): 返回的简历数量
            
        Returns:
            Dict[str, Any]: 筛选结果
        """
        try:
            logger.info(f"Starting resume screening with query: {query_text}")
            
            # 1. 解析查询
            query_metadata = self.query_parser.parse_query(query_text)
            logger.info(f"Parsed query metadata: {query_metadata}")
            
            # 2. 语义检索
            retrieved_resumes = self.retriever.retrieve(query_metadata, n_results=top_k*2)
            logger.info(f"Retrieved {len(retrieved_resumes)} resumes from semantic search")
            
            if not retrieved_resumes:
                logger.warning("No resumes found in semantic search")
                return {
                    "query": query_text,
                    "query_metadata": query_metadata.dict(),
                    "total_candidates": 0,
                    "candidates": [],
                    "message": "未找到匹配的简历"
                }
            
            # 3. 硬性条件过滤
            filtered_resumes = self.hard_filter.filter_resumes(retrieved_resumes, query_metadata)
            logger.info(f"After hard filtering: {len(filtered_resumes)} resumes")
            
            # 4. 多维度评分
            scored_resumes = self.scorer.score_resumes(filtered_resumes, query_metadata)
            logger.info(f"Scored {len(scored_resumes)} resumes")
            
            # 5. 排序
            ranked_resumes = self.ranker.rank_resumes(scored_resumes, query_metadata)
            
            # 6. 取前K个
            top_resumes = ranked_resumes[:top_k]
            
            # 7. 候选人分析
            analyzed_candidates = self.candidate_analyzer.analyze_candidates(top_resumes, query_metadata)
            logger.info(f"Analyzed {len(analyzed_candidates)} candidates")
            
            # 8. 格式化结果
            formatted_results = self.result_formatter.format_results(analyzed_candidates, query_metadata)
            
            # 9. 添加文件路径信息
            self._enrich_results_with_file_info(formatted_results)
            
            return {
                "query": query_text,
                "query_metadata": query_metadata.dict(),
                "total_candidates": len(analyzed_candidates),
                "candidates": formatted_results["candidates"],
                "summary": formatted_results["summary"]
            }
            
        except Exception as e:
            logger.error(f"Failed to screen resumes: {e}")
            raise

    def _enrich_results_with_file_info(self, results: Dict[str, Any]) -> None:
        """
        为结果添加文件路径信息
        
        Args:
            results (Dict[str, Any]): 格式化的结果
        """
        try:
            for candidate in results.get("candidates", []):
                candidate_id = candidate.get("id", "")
                # 查找对应的文件信息
                for file_hash, resume_data in self.processed_resumes.items():
                    if resume_data.get("id") == candidate_id:
                        candidate["file_path"] = resume_data.get("file_path", "")
                        candidate["file_name"] = os.path.basename(resume_data.get("file_path", ""))
                        break
        except Exception as e:
            logger.error(f"Failed to enrich results with file info: {e}")

    def get_resume_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        根据文件路径获取简历信息
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 简历信息
        """
        for resume_data in self.processed_resumes.values():
            if resume_data.get("file_path") == file_path:
                return resume_data
        return None

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        file_stats = self.file_manager.get_stats()
        return {
            "total_files_found": file_stats["total_files"],
            "processed_resumes": len(self.processed_resumes),
            "file_types": file_stats["file_types"],
            "total_size": file_stats["total_size"],
            "avg_size": file_stats["avg_size"]
        }

    def export_results(self, results: Dict[str, Any], output_path: str, format: str = "json") -> None:
        """
        导出筛选结果
        
        Args:
            results (Dict[str, Any]): 筛选结果
            output_path (str): 输出文件路径
            format (str): 导出格式 ("json" 或 "text")
        """
        try:
            if format.lower() == "json":
                self.result_formatter.export_to_json(results, output_path)
            elif format.lower() == "text":
                self.result_formatter.export_to_text(results, output_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Results exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            raise

    def clear_cache(self) -> None:
        """
        清除缓存
        """
        try:
            self.cache_manager.clear()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def reload_resumes(self) -> Dict[str, Any]:
        """
        重新加载所有简历
        
        Returns:
            Dict[str, Any]: 重新加载的统计信息
        """
        try:
            # 清除已处理的简历
            self.processed_resumes.clear()
            
            # 重新扫描和处理
            return self.scan_and_process_resumes()
            
        except Exception as e:
            logger.error(f"Failed to reload resumes: {e}")
            raise