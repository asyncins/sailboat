import hashlib
import hmac
import base64
from urllib.parse import quote_plus


def md5_encode(value):
    """ MD5 消息摘要"""
    h = hashlib.md5()
    h.update(value.encode("utf8"))
    res = h.hexdigest()
    return res


def make_ding_sign(timestamps, secret, mode=False):
    """钉钉签名计算
    根据钉钉文档指引计算签名信息
    文档参考
    https://docs.python.org/3.6/library/hmac.html
    https://docs.python.org/3.6/library/urllib.parse.html#urllib.parse.quote
    https://ding-doc.dingtalk.com/doc#/faquestions/hxs5v9
    """
    print("tmps:", timestamps)
    if not isinstance(timestamps, str):
        timestamps = str(timestamps)
    mav = hmac.new(secret.encode("utf8"), digestmod=hashlib.sha256)
    mav.update(timestamps.encode("utf8"))
    result = mav.digest()
    signature = base64.b64encode(result).decode("utf8")
    if mode:
        signature = quote_plus(signature)
    return signature
