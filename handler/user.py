import os
import json
from datetime import datetime, timedelta
from flask.views import MethodView
from flask import request
import jwt
from bson import ObjectId

from connect import databases
from components.urils import md5_encode
from settings import SECRET
from components.auth import authorization, get_user_info
from components.enums import Role, Status, StatusCode


class RegisterHandler(MethodView):

    def post(self):
        """
        * @api {post} /reg/ 用户注册
        * @apiPermission Role.Anonymous
        * @apiParam {String} username  用户名
        * @apiParam {String} password  密码
        * @apiParam {String} nick  昵称
        * @apiParam {String} email  邮箱
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {
              "code": 4003,
              "data": {},
              "message": "parameter error"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 201
            {
              "code": 201,
              "data": {
                "create": "Fri, 13 Dec 2019 08:15:16 GMT",
                "email": "asycins@aliyun.com",
                "id": "5df2d814f007418369463308",
                "nick": "小奎因",
                "password": "e10adc3949ba59abbe56e057f20f883e",
                "role": 10,
                "status": 0,
                "username": "asyncins"
              },
              "message": "success"
            }
        """
        username = request.json.get("username")
        pwd = request.json.get("password")
        nick = request.json.get("nick")
        email = request.json.get("email")
        if not username or not pwd or not nick or not email or "@" not in email:
            return {"message": StatusCode.ParameterError.value[0],
                    "data": {},
                    "code": StatusCode.ParameterError.value[1]
                    }, 400
        password = md5_encode(pwd)
        count = databases.user.count_documents({})
        if not count:
            # 首次注册的账户为超级管理员，启动激活
            role = Role.SuperUser.value
            message = {"username": username, "password": password,
                       "nick": nick, "email": email,
                       "role": role, "status": Status.On.value}
        else:
            # 非首次注册账户默认为开发者，且未激活
            role = Role.Developer.value
            message = {"username": username, "password": password,
                       "nick": nick, "email": email,
                       "role": role, "status": Status.Off.value}
        message["create"] = datetime.now()
        # 将信息写入数据库并将相应信息返回给用户
        inserted = databases.user.insert_one(message).inserted_id
        message["id"] = str(inserted)
        message["username"] = username
        message["email"] = email
        message["role"] = role
        message.pop("_id")
        return {"message": "success", "data": message, "code": 201}, 201


class UserHandler(MethodView):

    permission = {"permission": Role.SuperUser}

    @authorization
    def get(self):
        """
        * @api {get} /user/ 获取用户列表
        * @apiPermission Role.Superuser
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Json} query 可自定义查询参数 \
        {
            "query": {"username": "sfhfpc"},
            "limit": 2,
            "skip": 3
        } \
        OR \
        {
            "query": {},
            "limit": 2,
            "skip": 3
        }
        * @apiParam {Int} [limit] Limit
        * @apiParam {Int} [skip] Skip
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 200,
              "data": [
                {
                  "create": "2019-12-11 21:07:37",
                  "email": "5@foxmail.com",
                  "id": "5df0ea19b46116479b46c27c",
                  "role": 100,
                  "status": 1,
                  "username": "sfhfpc"
                },
                {
                  "create": "2019-12-13 08:15:16",
                  "email": "asycins@aliyun.com",
                  "id": "5df2d814f007418369463308",
                  "role": 10,
                  "status": 0,
                  "username": "asyncins"
                }
              ],
              "message": "success"
            }
        """
        query = request.json.get('query')
        limit = request.json.get('limit') or 0
        skip = request.json.get('skip') or 0
        # 允许用户自定义查询条件
        finds = databases.user.find(query).limit(limit).skip(skip)
        info = [{
            "id": str(i.get('_id')),
            "username": i.get("username"),
            "email": i.get("email"),
            "role": i.get("role"),
            "status": i.get("status"),
            "create": i.get("create").strftime("%Y-%m-%d %H:%M:%S")}
            for i in finds]
        return {"message": "success", "data": info, "code": 200}, 200

    @authorization
    def put(self):
        """
        * @api {put} /user/ 用户信息更新
        * @apiPermission Role.Superuser
        * @apiDescription 仅允许修改状态和角色
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Int} idn  账户 ID
        * @apiParam {String} [status]  账户状态
        * @apiParam {Int} [role]  用户角色:0,1,10,100
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {
              "code": 4003,
              "data": {},
              "message": "parameter error"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 200,
              "data": {
                "count": 1
              },
              "message": "success"
            }
        """
        idn = request.json.get("id")
        status = request.json.get("status")
        role = request.json.get("role")
        if role and int(role) not in Role._value2member_map_:
            return {"message": StatusCode.ParameterError.value[0],
                    "data": {},
                    "code": StatusCode.ParameterError.value[1]
                    }, 400
        if status and int(status) not in Status._value2member_map_:
            return {"message": StatusCode.ParameterError.value[0],
                    "data": {},
                    "code": StatusCode.ParameterError.value[1]
                    }, 400
        user = databases.user.find_one({"_id": ObjectId(idn)})
        if not status:
            status = user.get("status")
        if not role:
            role = user.get("role")
        result = databases.user.update_one({"_id": ObjectId(idn)}, {'$set': {"status": int(status), "role": int(role)}})
        # 根据更新结果选择返回信息
        message, status = ("success", 200) if result.modified_count else ("fail", 400)
        return {"message": message, "data": {"count": result.modified_count}, "code": status}, status

    @authorization
    def delete(self):
        """
        * @api {delete} /user/ 删除指定用户
        * @apiPermission Role.Superuser
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Int} idn  账户 ID
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {
              "code": 400,
              "data": {
                "count": 0
              },
              "message": "fail"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 200,
              "data": {
                "count": 1
              },
              "message": "success"
            }
        """
        idn = request.json.get("id")
        result = databases.user.delete_one({"_id": ObjectId(idn)})
        # 根据删除结果选择返回信息
        message, status = ("success", 200) if result.deleted_count else ("fail", 400)
        return {"message": message, "data": {"count": result.deleted_count}, "code": status}, status


class LoginHandler(MethodView):

    def post(self):
        """
        * @api {post} /login/ 用户登录
        * @apiPermission Role.Anonymous
        * @apiParam {String} username 用户名
        * @apiParam {String} password 密码
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {
              "code": 4005,
              "data": {},
              "message": "not found"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 200,
              "data": {
                "idn": "5df0ea19b46116479b46c27c",
                "role": 100,
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6InNmaGZwYyIsInBhc3N3b3JkIjoiZTEwYWRjMzk0OWJhNTlhYmJlNTZlMDU3ZjIwZjg4M2UiLCJzdGF0dXMiOjEsInJvbGUiOjEwMCwiZXhwcmVzcyI6IjIwMTktMTItMTMgMTY6MDU6MjcifQ.KiPJvuQwKeZHof8CoAoppxNTsjNgCjpkkJT2Pi48XOs",
                "username": "sfhfpc"
              },
              "message": "success"
            }
        """
        username = request.json.get("username")
        pwd = request.json.get("password")
        password = md5_encode(pwd)
        # 支持用户名或邮箱登录
        query = {"username": username, "password": password}
        name_exit = databases.user.count_documents(query)
        if not name_exit:
            query = {"email": username, "password": password}
        result = databases.user.find_one(query)
        if not result:
            return {"message": StatusCode.NotFound.value[0],
                    "data": {},
                    "code": StatusCode.NotFound.value[1]
                    }, 400
        status = result.get("status")
        if not status:
            return {"message": StatusCode.UserStatusOff.value[0],
                    "data": {},
                    "code": StatusCode.UserStatusOff.value[1]
                    }, 400
        # 构造生成 Token 所用到的元素，Token 默认八小时过期
        exp = datetime.now() + timedelta(hours=8)
        express = exp.strftime("%Y-%m-%d %H:%M:%S")
        payload = {"username": username, "password": password,
                   "status": status, "role": result.get("role"),
                   "express": express}
        token = str(jwt.encode(payload, SECRET, algorithm='HS256'), "utf8")
        idn, username, role = get_user_info(token)
        return {"message": "success",
                "data": {"idn": idn, "username": username, "role": role, "token": token},
                "code": 200}
