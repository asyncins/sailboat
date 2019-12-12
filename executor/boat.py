import os
import sys
from importlib import import_module

from components.storage import FileStorages
from settings import MODULERNAME


storages = FileStorages()


class Helmsman:
    """为文件导入和执行创造条件的上下文管理器"""
    def __init__(self, project, version):
        self.project = project
        self.version = version
        self.storage = storages
        self.temp_file = ""

    def __enter__(self):
        """上文"""
        # 将文件拷贝到临时区
        target = self.storage.copy_to_temporary(project, version)
        self.temp_file = target
        if target:
            # 将文件路径添加到 sys.path
            sys.path.insert(0, target)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """下文"""
        if os.path.exists(self.temp_file):
            # 清理临时区中对应的文件
            os.remove(self.temp_file)


def main(project, version):
    helmsman = Helmsman(project, version)
    with helmsman:
        # 从指定的文件中导入模块并执行指定方法
        spider = import_module(MODULERNAME)
        spider.main()


if __name__ == "__main__":
    project, version = sys.argv[-2], sys.argv[-1]
    main(project, version)
