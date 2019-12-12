from abc import ABC, abstractmethod


class Monitor(ABC):
    """异常监控"""

    @abstractmethod
    def push(self):
        """接收器
        被捕获到的异常信息将会送到这里"""

    @abstractmethod
    def extractor(self):
        """拆分车间
        根据需求拆分异常信息"""

    @abstractmethod
    def recombination(self):
        """重组车间
        异常信息将在这里重组"""


class Alarm(ABC):
    """警报器"""

    @abstractmethod
    def __init__(self):
        """初始配置"""

    def receive(self):
        """接收者
        接收异常信息，将其进行处理后交给发送者"""

    @abstractmethod
    def sender(self):
        """发送者
        将重组后的信息发送到端"""