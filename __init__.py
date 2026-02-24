import os
import sys


def setup_project_path():
    """统一补全项目路径，确保绝对导入生效"""
    # 获取common.py所在目录（my_package）
    package_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(package_root)
    # 项目根目录（my_project）
    project_root = os.path.dirname(package_root)
    # 仅当路径未加入时才添加，避免重复
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


setup_project_path()
