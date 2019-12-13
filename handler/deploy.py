"""
https://flask.palletsprojects.com/en/1.1.x/api/?highlight=route#flask.views.MethodView
https://flask.palletsprojects.com/en/1.1.x/api/#flask.request
https://werkzeug.palletsprojects.com/en/0.16.x/datastructures/#werkzeug.datastructures.FileStorage
https://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.insert_one
https://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.find
https://api.mongodb.com/python/current/api/pymongo/collection.html?highlight=delete#pymongo.collection.Collection.delete_one
"""
import time
import json
from datetime import datetime
from flask.views import MethodView
from flask import request

from components.storage import FileStorages
from connect import databases
from components.auth import authorization, get_user_info
from components.enums import Role, StatusCode


storages = FileStorages()


class DeployHandler(MethodView):

    permission = {"permission": Role.Developer}

    @authorization
    def get(self):
        """
        * @api {get} /deploy/ 获取项目列表
        * @apiPermission Role.Developer AND Owner
        * @apiDescription 用户只能查看自己上传的项目
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Json} query 可自定义查询参数 \
        {
        "query":
            {"project": "sail"},
            "limit": 2,
            "skip": 3
        } \
        OR \
        {
        "query":
            {},
            "limit": 2,
            "skip": 3
        }
        * @apiParam {Int} [limit] Limit
        * @apiParam {Int} [skip] Skip
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 200,
              "data": {
                "data": [
                  {
                    "create": "2019-12-13 09:04:15",
                    "id": "5df2e38fed21d4d2879a762a",
                    "idn": "5df0ea19b46116479b46c27c",
                    "project": "football",
                    "username": "sfhfpc",
                    "version": "1576199055"
                  },
                  {
                    "create": "2019-12-13 09:04:42",
                    "id": "5df2e3aaed21d4d2879a762c",
                    "idn": "5df0ea19b46116479b46c27c",
                    "project": "videos",
                    "username": "sfhfpc",
                    "version": "1576199082"
                  }
                ]
              },
              "message": "success"
            }
        """
        query = request.json.get('query')
        limit = request.json.get('limit') or 0
        skip = request.json.get('skip') or 0
        # 检查所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        if role != Role.SuperUser.value:
            query["idn"] = idn
            query["username"] = username
        # 允许用户自定义查询条件
        finds = databases.deploy.find(query).limit(limit).skip(skip)
        message = {"data": [{
            "id": str(i.get('_id')),
            "project": i.get("project"),
            "version": i.get("version"),
            "idn": i.get("idn"),
            "username": i.get("username"),
            "create": i.get("create").strftime("%Y-%m-%d %H:%M:%S")}
            for i in finds]}
        return {"message": "success", "data": message, "code": 200}

    @authorization
    def post(self):
        """项目部署
        * @api {post} /deploy/ 项目部署
        * @apiPermission Role.Developer
        * @apiParam {String} project 项目名称
        * @apiParam {File} file 文件
        * @apiParam {String} [remark] 备注
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {
              "code": 4001,
              "data": {},
              "message": "missing parameter"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 201
            {
              "code": 201,
              "data": {
                "_id": "5df2e3637e0e5bf80cc5263e",
                "create": "Fri, 13 Dec 2019 09:03:31 GMT",
                "idn": "5df0ea19b46116479b46c27c",
                "project": "coders",
                "remark": "足球队",
                "username": "sfhfpc",
                "version": "1576199011"
              },
              "message": "success"
            }
        """
        project = request.form.get('project')
        remark = request.form.get('remark')
        file = request.files.get('file')
        if not project or not file:
            # 确保参数和值存在
            return {"message": StatusCode.MissingParameter.value[0],
                    "data": {},
                    "code": StatusCode.MissingParameter.value[1]
                    }, 400
        filename = file.filename
        if not filename.endswith('.egg'):
            # 确保文件类型正确
            return {"message": StatusCode.NotFound.value[0],
                    "data": {},
                    "code": StatusCode.NotFound.value[1]
                    }, 400
        version = int(time.time())
        content = file.stream.read()
        # 将文件存储到服务端
        result = storages.put(project, version, content)
        if not result:
            # 存储失败则返回相关提示
            return {"message": StatusCode.OperationError.value[0],
                    "data": {},
                    "code": StatusCode.OperationError.value[1]
                    }, 400
        # 文件存储成功后在数据库中存储相关信息并返回给用户
        # 增加所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        message = {"project": project,
                   "version": str(version),
                   "remark": remark or "Nothing",
                   "idn": idn,
                   "username": username,
                   "create": datetime.now()}
        databases.deploy.insert_one(message).inserted_id
        message["_id"] = str(message.pop("_id"))
        return {"message": "success",
                "data": message,
                "code": 201}, 201

    @authorization
    def delete(self):
        """
        * @api {delete} /deploy/ 删除项目
        * @apiPermission Role.Developer AND Owner
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Json} query 删除指定文件 {"query": {"project": "sail", "version": "1576199082"}} \
        OR \
        删除指定目录及目录下所有文件  {"query": {"project": "football"}}
        * @apiErrorExample {json} Error-Response:
            # status code: 403
            {
              "code": 4002,
              "data": {},
              "message": "is not yours"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 200

            # 0 代表删除数量，B 代表文件不存在无需删除
            {
              "code": 204,
              "data": {
                "count": 0,
                "deleted": "B",
                "query": {
                  "idn": "5df0ea19b46116479b46c27c",
                  "project": "sail",
                  "username": "sfhfpc",
                  "version": "1576199061"
                }
              },
              "message": "success"
            }

            OR
            # 1 代表删除数量，A 代表文件存在
            {
              "code": 204,
              "data": {
                "count": 1,
                "deleted": "A",
                "query": {
                  "idn": "5df0ea19b46116479b46c27c",
                  "project": "sail",
                  "username": "sfhfpc",
                  "version": "1576199061"
                }
              },
              "message": "success"
            }
        """
        query = request.json.get('query')

        if query:
            project = query.get("project") or ""
            version = query.get("version") or ""
            if not project or "." in project or "/" in project or "." in version or "/" in version:
                # . or / 防止恶意参数删除系统目录
                return {"message": StatusCode.PathError.value[0],
                        "data": {},
                        "code": StatusCode.PathError.value[1]
                        }, 400
            # 检查所有权
            token = request.headers.get("Authorization")
            idn, username, role = get_user_info(token)
            query["idn"] = idn
            query["username"] = username
            count = databases.deploy.count_documents(query)
            if not count or role != Role.SuperUser.value:
                return {"message": StatusCode.IsNotYours.value[0],
                        "data": {},
                        "code": StatusCode.IsNotYours.value[1]
                        }, 403
            deleted = storages.delete(project, version)
        else:
            query = {}
        # 允许用户自定义删除条件
        result = databases.deploy.delete_one(query)
        count = result.deleted_count
        return {"message": "success",
                "data": {"count": count, "deleted": deleted, "query": query},
                "code": 204
                }