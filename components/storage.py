import os
import logging
import shutil
from settings import FILEPATH, TEMPATH


class FileStorages:

    @staticmethod
    def put(project, version, content):
        """文件存储
        """
        # 根据项目名称生成路径
        room = os.path.join(FILEPATH, project)
        if not os.path.exists(room):
            # 如果目录不存在则创建
            os.makedirs(room)
        # 拼接文件完整路径，以时间戳作为文件名
        filename = os.path.join(room, "%s.egg" % str(version))
        try:
            with open(filename, 'wb') as file:
                # 写入文件
                file.write(content)
        except Exception as exc:
            # 异常处理，打印异常信息
            logging.warning(exc)
            return False
        return True

    def get(self):
        pass

    @staticmethod
    def delete(project, version):
        """文件删除状态
        A - 文件或目录存在且成功删除
        B - 文件或目录不存在，无需删除
        """
        sign = 'B'
        room = os.path.join(FILEPATH, project)
        if project and version:
            # 删除指定文件
            filename = os.path.join(room, "%s.egg" % str(version))
            if os.path.exists(filename):
                sign = 'A'
                os.remove(filename)
        if project and not version:
            # 删除指定目录
            if os.path.exists(room):
                sign = 'A'
                shutil.rmtree(room)
        return sign

    @staticmethod
    def copy_to_temporary(project, version):
        """根据参数将指定文件拷贝到指定目录
        """
        before = os.path.join(FILEPATH, project, "%s.egg" % version)
        after = os.path.join(TEMPATH, "%s.egg" % version)
        if not os.path.exists(before):
            logging.warning("File %s Not Exists" % before)
            return None
        if not os.path.exists(TEMPATH):
            os.makedirs(TEMPATH)
        # 文件拷贝
        shutil.copyfile(before, after)
        return after

    @staticmethod
    def exists(project, version):
        file = os.path.join(FILEPATH, project, "%s.egg" % version)
        if not os.path.exists(file):
            return False
        return True
