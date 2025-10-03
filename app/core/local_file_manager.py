import os
import glob
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
import json
from datetime import datetime


class LocalFileManager:
    """
    本地文件管理器，用于管理本地简历文件
    """
    
    def __init__(self, watch_directories: Optional[List[str]] = None):
        """
        初始化本地文件管理器
        
        Args:
            watch_directories (List[str], optional): 要监控的目录列表
        """
        self.watch_directories = watch_directories or []
        self.supported_extensions = ['.pdf', '.docx', '.doc']
        self.file_index = {}  # 文件索引，存储文件信息
        self.observer = None
        logger.info("Initialized LocalFileManager")

    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[str]:
        """
        扫描目录中的简历文件
        
        Args:
            directory_path (str): 目录路径
            recursive (bool): 是否递归扫描子目录
            
        Returns:
            List[str]: 找到的简历文件路径列表
        """
        try:
            if not os.path.exists(directory_path):
                logger.error(f"Directory not found: {directory_path}")
                return []
            
            file_paths = []
            
            if recursive:
                # 递归扫描所有子目录
                for ext in self.supported_extensions:
                    pattern = os.path.join(directory_path, '**', f'*{ext}')
                    files = glob.glob(pattern, recursive=True)
                    file_paths.extend(files)
            else:
                # 只扫描当前目录
                for ext in self.supported_extensions:
                    pattern = os.path.join(directory_path, f'*{ext}')
                    files = glob.glob(pattern)
                    file_paths.extend(files)
            
            # 更新文件索引
            for file_path in file_paths:
                self._update_file_index(file_path)
            
            logger.info(f"Found {len(file_paths)} resume files in {directory_path}")
            return file_paths
            
        except Exception as e:
            logger.error(f"Failed to scan directory {directory_path}: {e}")
            return []

    def scan_multiple_directories(self, directory_paths: List[str], recursive: bool = True) -> List[str]:
        """
        扫描多个目录中的简历文件
        
        Args:
            directory_paths (List[str]): 目录路径列表
            recursive (bool): 是否递归扫描子目录
            
        Returns:
            List[str]: 所有找到的简历文件路径列表
        """
        all_files = []
        for directory_path in directory_paths:
            files = self.scan_directory(directory_path, recursive)
            all_files.extend(files)
        
        # 去重
        unique_files = list(set(all_files))
        logger.info(f"Found {len(unique_files)} unique resume files across {len(directory_paths)} directories")
        return unique_files

    def _update_file_index(self, file_path: str) -> None:
        """
        更新文件索引信息
        
        Args:
            file_path (str): 文件路径
        """
        try:
            file_stat = os.stat(file_path)
            file_hash = self._calculate_file_hash(file_path)
            
            self.file_index[file_path] = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': file_stat.st_size,
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime),
                'hash': file_hash,
                'extension': Path(file_path).suffix.lower(),
                'last_scanned': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to update file index for {file_path}: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的MD5哈希值
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            str: 文件的MD5哈希值
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 文件信息字典
        """
        return self.file_index.get(file_path)

    def get_all_files(self) -> List[Dict[str, Any]]:
        """
        获取所有已索引的文件信息
        
        Returns:
            List[Dict[str, Any]]: 所有文件信息列表
        """
        return list(self.file_index.values())

    def filter_files_by_extension(self, extension: str) -> List[str]:
        """
        根据文件扩展名过滤文件
        
        Args:
            extension (str): 文件扩展名（如 '.pdf'）
            
        Returns:
            List[str]: 匹配的文件路径列表
        """
        filtered_files = []
        for file_path, file_info in self.file_index.items():
            if file_info.get('extension', '').lower() == extension.lower():
                filtered_files.append(file_path)
        return filtered_files

    def filter_files_by_size(self, min_size: int = 0, max_size: int = float('inf')) -> List[str]:
        """
        根据文件大小过滤文件
        
        Args:
            min_size (int): 最小文件大小（字节）
            max_size (int): 最大文件大小（字节）
            
        Returns:
            List[str]: 匹配的文件路径列表
        """
        filtered_files = []
        for file_path, file_info in self.file_index.items():
            file_size = file_info.get('size', 0)
            if min_size <= file_size <= max_size:
                filtered_files.append(file_path)
        return filtered_files

    def export_file_index(self, output_path: str) -> None:
        """
        导出文件索引到JSON文件
        
        Args:
            output_path (str): 输出文件路径
        """
        try:
            # 转换datetime对象为字符串
            exportable_index = {}
            for file_path, file_info in self.file_index.items():
                exportable_info = file_info.copy()
                if 'modified_time' in exportable_info:
                    exportable_info['modified_time'] = exportable_info['modified_time'].isoformat()
                if 'last_scanned' in exportable_info:
                    exportable_info['last_scanned'] = exportable_info['last_scanned'].isoformat()
                exportable_index[file_path] = exportable_info
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(exportable_index, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported file index to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export file index: {e}")

    def import_file_index(self, input_path: str) -> None:
        """
        从JSON文件导入文件索引
        
        Args:
            input_path (str): 输入文件路径
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                imported_index = json.load(f)
            
            # 转换字符串为datetime对象
            for file_path, file_info in imported_index.items():
                if 'modified_time' in file_info:
                    file_info['modified_time'] = datetime.fromisoformat(file_info['modified_time'])
                if 'last_scanned' in file_info:
                    file_info['last_scanned'] = datetime.fromisoformat(file_info['last_scanned'])
                self.file_index[file_path] = file_info
            
            logger.info(f"Imported file index from {input_path}")
            
        except Exception as e:
            logger.error(f"Failed to import file index: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取文件管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            'total_files': len(self.file_index),
            'file_types': {},
            'total_size': 0,
            'avg_size': 0
        }
        
        # 统计文件类型和大小
        for file_info in self.file_index.values():
            ext = file_info.get('extension', 'unknown')
            stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
            stats['total_size'] += file_info.get('size', 0)
        
        # 计算平均大小
        if stats['total_files'] > 0:
            stats['avg_size'] = stats['total_size'] / stats['total_files']
        
        return stats


class FileWatcher(FileSystemEventHandler):
    """
    文件监控处理器
    """
    
    def __init__(self, file_manager: LocalFileManager):
        self.file_manager = file_manager
        
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if Path(file_path).suffix.lower() in ['.pdf', '.docx', '.doc']:
                logger.info(f"New resume file detected: {file_path}")
                self.file_manager._update_file_index(file_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if file_path in self.file_manager.file_index:
                del self.file_manager.file_index[file_path]
                logger.info(f"Resume file removed: {file_path}")
    
    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if Path(file_path).suffix.lower() in ['.pdf', '.docx', '.doc']:
                logger.info(f"Resume file modified: {file_path}")
                self.file_manager._update_file_index(file_path)