from datetime import datetime
from flask import request, Response
import jwt

from settings import SECRET, ALG
from connect import databases
from components.enums import Status, StatusCode


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
            return {"message": StatusCode.NoAuth.value[0],
                    "data": {},
                    "code": StatusCode.NoAuth.value[1]
                    }, 403
        info = jwt.decode(token, SECRET, algorithms=ALG)
        username = info.get("username")
        password = info.get("password")
        express = info.get("express")
        role = info.get("role")
        if role < permission.value:
            # 通过数学比较符号判断权限级别
            return {"message": StatusCode.NoAuth.value[0],
                    "data": {},
                    "code": StatusCode.NoAuth.value[1]
                    }, 403
        # 判断令牌是否过期
        overdue = is_overdue(express)
        if not overdue:
            return {"message": StatusCode.TokenOverdue.value[0],
                    "data": {},
                    "code": StatusCode.TokenOverdue.value[1]
                    }, 403
        # 查询数据库并进行判断
        exists = databases.user.count_documents(
            {"username": username, "password": password, "status": Status.On.value})
        if not exists:
            return {"message": StatusCode.UserStatusOff.value[0],
                    "data": {},
                    "code": StatusCode.UserStatusOff.value[1]
                    }, 400
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
    return str(idn), username, role


