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
from components.auth import authorization
from components.enums import Role, Status


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
              "Message": "Fail",
              "Reason": "Missing Parameter"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 201
            {
              "Message": "Success",
              "email": "5@foxmail.com",
              "id": "5df0ea19b46116479b46c27c",
              "role": 100,
              "username": "sfhfpc"
            }
        """
        username = request.json.get("username")
        pwd = request.json.get("password")
        nick = request.json.get("nick")
        email = request.json.get("email")
        if not username or not pwd or not nick or not email or "@" not in email:
            return {"Message": "Fail", "Reason": "Missing Parameter"}, 400
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
        return {"Message": "Success", "id": str(inserted),
                "username": username, "email": email,
                "role": role}, 201


class UserHandler(MethodView):

    permission = {"permission": Role.SuperUser}

    @authorization
    def get(self):
        """
        * @api {get} /user/ 获取用户列表
        * @apiPermission Role.Superuser
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Dict} [query]  {"username": "sfhfpc"}
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "result": {
                "create": "2019-12-08 15:10:41",
                "email": "sfhfpc@foxmail.com",
                "id": "5deca1f1df418f1d2261f4d7",
                "role": 100,
                "status": 1,
                "username": "sfhfpc"
              }
            }
        """
        query = request.json.get('query')
        if query:
            query = json.loads(query)
        else:
            query = {}
        # 允许用户自定义查询条件
        finds = databases.user.find(query)
        info = [{
            "id": str(i.get('_id')),
            "username": i.get("username"),
            "email": i.get("email"),
            "role": i.get("role"),
            "status": i.get("status"),
            "create": i.get("create").strftime("%Y-%m-%d %H:%M:%S")}
            for i in finds][0]
        message = {"result": info}
        return message

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
              "Message": "Fail",
              "Reason": "User Not Found or Status Off"
            }

            OR

            # status code: 400
            {
              "Count": 0,
              "Message": "Fail"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 203
            {
              "Count": 1,
              "Message": "Success"
            }
        """
        idn = request.json.get("id")
        status = request.json.get("status")
        role = request.json.get("role")
        if role and int(role) not in Role._value2member_map_:
            return {"Message": "Fail", "Reason": "Value Error"}, 400
        if status and int(status) not in Status._value2member_map_:
            return {"Message": "Fail", "Reason": "Value Error"}, 400
        user = databases.user.find_one({"_id": ObjectId(idn)})
        if not status:
            status = user.get("status")
        if not role:
            role = user.get("role")
        result = databases.user.update_one({"_id": ObjectId(idn)}, {'$set': {"status": int(status), "role": int(role)}})
        # 根据更新结果选择返回信息
        message, status = ("Success", 203) if result.modified_count else ("Fail", 400)
        return {"Message": message, "Count": result.modified_count}, status

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
              "Message": "Fail",
              "Reason": "User Not Found or Status Off"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "Count": 1,
              "Message": "Success"
            }
        """
        idn = request.json.get("id")
        result = databases.user.delete_one({"_id": ObjectId(idn)})
        # 根据删除结果选择返回信息
        message, status = ("Success", 200) if result.deleted_count else ("Fail", 400)
        return {"Message": message, "Count": result.deleted_count}, status


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
              "Message": "Fail",
              "Reason": "User Not Found"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "Message": "Success",
              "Token": "token_first.token_second.token_three"
            }
        """
        username = request.json.get("username")
        pwd = request.json.get("password")
        password = md5_encode(pwd)

        result = databases.user.find_one({"username": username, "password": password})
        if not result:
            return {"Message": "Fail", "Reason": "User Not Found"}, 400
        status = result.get("status")
        if not status:
            return {"Message": "Fail", "Reason": "User Status Off"}, 400

        # 构造生成 Token 所用到的元素，Token 默认一小时过期
        exp = datetime.now() + timedelta(hours=1)
        express = exp.strftime("%Y-%m-%d %H:%M:%S")
        payload = {"username": username, "password": password,
                   "status": status, "role": result.get("role"),
                   "express": express}
        token = str(jwt.encode(payload, SECRET, algorithm='HS256'), "utf8")
        return {"Message": "Success", "Token": token}