import hashlib
import hmac
import time
import base64
import json
import logging
from urllib.parse import quote_plus
import requests
from interface import Alarm

from supervise.monitors import MarkdownMonitor


class DingAlarm(Alarm):

    def __init__(self):
        self.access_key = "dingoawo3a8tpzidbmrsyq"
        self.secret = "F2T-NvXsHubUNHhvQkfggRUpLeFsOKvpRYv7YEtUAroVtUG2R1PbIQCaDcDgiGQS"
        self.token = "https://oapi.dingtalk.com/robot/send?access_token=b96364e106ad36c5a793c2c8a1b3979a5d9c5087f6985446d6824ad74735b828"
        self.header = {"Content-Type": "application/json;charset=UTF-8"}
        self.monitor = MarkdownMonitor()

    def receive(self, txt, occurrence, timer):
        """接收者
        接收异常信息，将其进行处理后交给发送者"""
        content = self.monitor.push(txt, occurrence, timer)
        self.sender(content)

    @staticmethod
    def _sign(timestamps, secret, mode=False):
        """钉钉签名计算
        根据钉钉文档指引计算签名信息
        文档参考
        https://docs.python.org/3.6/library/hmac.html
        https://docs.python.org/3.6/library/urllib.parse.html#urllib.parse.quote
        https://ding-doc.dingtalk.com/doc#/faquestions/hxs5v9
        """
        if not isinstance(timestamps, str):
            # 如果钉钉机器人的安全措施为密钥，那么按照文档指引传入的是字符串，反之为数字
            # 加密时需要转成字节，所以这里要确保时间戳为字符串
            timestamps = str(timestamps)
        mav = hmac.new(secret.encode("utf8"), digestmod=hashlib.sha256)
        mav.update(timestamps.encode("utf8"))
        result = mav.digest()
        # 对签名值进行 Base64 编码
        signature = base64.b64encode(result).decode("utf8")
        if mode:
            # 可选择是否将签名值进行 URL 编码
            signature = quote_plus(signature)
        return signature

    def sender(self, message):
        """发送者
        将重组后的信息发送到端"""
        timestamps = int(time.time()) * 1000
        sign = self._sign(timestamps, self.secret, True)
        # 根据钉钉文档构造链接
        url = self.token + "&timestamp=%s&sign=%s" % (timestamps, sign)
        # 通过钉钉机器人将消息发送到钉钉群
        resp = requests.post(url, headers=self.header, json=message)
        # 根据返回的错误码判断消息发送状态
        err = json.loads(resp.text)
        if err.get("errcode"):
            logging.warning(err)
            return False
        else:
            logging.info("Message Sender Success")
            return True

