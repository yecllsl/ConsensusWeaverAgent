"""根级 pytest 配置，提供项目路径到 sys.path"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，使测试可以导入项目模块
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
