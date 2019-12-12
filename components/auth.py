from datetime import datetime
from flask import request, Response
import jwt

from settings import SECRET, ALG
from connect import databases
from components.enums import Status


def is_overdue(express):
    """判断是否过期"""
    end = datetime.strptime(express, "%Y-%m-%d %H:%M:%S")
    delta = datetime.now() - end
    if delta.days < 0 or delta.seconds < 0:
        # 时间差值出现负数则视为过期
        return True
    else:
        return False


def authorization(func):
    """鉴权装饰器"""
    def wrapper(*args, **kw):
        # 获取为接口设定的权限
        permission = args[0].permission.get("permission")
        token = request.headers.get("Authorization")
        if not token:
            return {"Message": "Fail", "Reason": "No Auth"}, 403
        info = jwt.decode(token, SECRET, algorithms=ALG)
        username = info.get("username")
        password = info.get("password")
        express = info.get("express")
        role = info.get("role")
        if role < permission.value:
            # 通过数学比较符号判断权限级别
            return {"Message": "Fail", "Reason": "Insufficient Permission"}, 403
        # 判断令牌是否过期
        overdue = is_overdue(express)
        if not overdue:
            return {"Message": "Fail", "Reason": "Token Overdue"}, 403
        # 查询数据库并进行判断
        exists = databases.user.count_documents(
            {"username": username, "password": password, "status": Status.On.value})
        if not exists:
            return {"Message": "Fail", "Reason": "User Not Found or Status Off"}, 403
        return func(*args, **kw)
    return wrapper


def get_user_info(token):
    """从签名中获取用户信息"""
    info = jwt.decode(token, SECRET, algorithms=ALG)
    username = info.get("username")
    password = info.get("password")
    express = info.get("express")
    role = info.get("role")
    overdue = is_overdue(express)
    if not overdue:
        return False
    exists = databases.user.count_documents(
        {"username": username, "password": password, "status": Status.On.value})
    if not exists:
        return False
    idn = databases.user.find_one({"username": username, "password": password}).get("_id")
    return (str(idn), username, role)

