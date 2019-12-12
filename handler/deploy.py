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
from components.enums import Role


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
        * @apiParam {Dict} [query]  {"project": "fabias"}
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "data": [
                {
                  "create": "2019-12-07 23:59:19",
                  "id": "5debcc574d35f8694c0a833c",
                  "project": "fabias",
                  "version": 1575734359,
                  "username": "sfhfpc",
                  "idn": "5df0ea19b46116479b46c27c"
                }
              ]
            }
        """
        query = request.form.get('query')
        if query:
            query = json.loads(query)
        else:
            query = {}
        # 检查所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        if role != Role.SuperUser.value:
            query["idn"] = idn
            query["username"] = username
        # 允许用户自定义查询条件
        finds = databases.deploy.find(query)
        message = {"data": [{
            "id": str(i.get('_id')),
            "project": i.get("project"),
            "version": i.get("version"),
            "idn": i.get("idn"),
            "username": i.get("username"),
            "create": i.get("create").strftime("%Y-%m-%d %H:%M:%S")}
            for i in finds]}
        return message

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
              "Message": "Fail",
              "Reason": "Missing Parameter"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 201
            {
              "Message": "Success",
              "inserted": "5df0edda35653521799761f0",
              "project": "coders",
              "version": 1576070618
            }
        """
        project = request.form.get('project')
        remark = request.form.get('remark')
        file = request.files.get('file')
        if not project or not file:
            # 确保参数和值存在
            return {"Message": "Fail", "Reason": "Missing Parameter"}, 400
        filename = file.filename
        if not filename.endswith('.egg'):
            # 确保文件类型正确
            return {"Message": "Fail", "Reason": "No EGG"}, 400
        version = int(time.time())
        content = file.stream.read()
        # 将文件存储到服务端
        result = storages.put(project, version, content)
        if not result:
            # 存储失败则返回相关提示
            return {"Message": "Fail", "Reason": "Exception Storing File"}, 400
        # 文件存储成功后在数据库中存储相关信息并返回给用户
        # 增加所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        message = {"project": project, "version": str(version),
                   "remark": remark or "Nothing",
                   "idn": idn, "username": username,
                   "create": datetime.now()}
        inserted = databases.deploy.insert_one(message).inserted_id
        return {"project": project, "version": str(version), "inserted": str(inserted), "Message": "Success"}, 201

    @authorization
    def delete(self):
        """
        * @api {delete} /deploy/ 删除项目
        * @apiPermission Role.Developer AND Owner
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Dict} query 删除指定文件 {"project": "coders", "version": "1576071191"} \
        OR \
        删除指定目录及目录下所有文件  {"project": "coders"}
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {"Message": "Fail", "Reason": "Path Error"}
        * @apiSuccessExample {json} Success-Response:
            # status code: 200

            # 0 代表删除数量，B 代表文件不存在无需删除
            {
              "count": 0,
              "deleted": "B",
              "query": {
                "idn": "5df0ea19b46116479b46c27c",
                "project": "coders",
                "username": "sfhfpc",
                "version": "1576125591"
              }
            }

            OR

            # 1 代表删除数量，A 代表文件存在
            {
              "count": 1,
              "deleted": "A",
              "query": {
                "idn": "5df0ea19b46116479b46c27c",
                "project": "coders",
                "username": "sfhfpc",
                "version": "1576125591"
              }
            }
        """
        query = request.form.get('query')

        if query:
            query = json.loads(query)
            project = query.get("project") or ""
            version = query.get("version") or ""
            if not project or "." in project or "/" in project or "." in version or "/" in version:
                # . or / 防止恶意参数删除系统目录
                return {"Message": "Fail", "Reason": "Path Error"}, 400
            # 检查所有权
            token = request.headers.get("Authorization")
            idn, username, role = get_user_info(token)
            query["idn"] = idn
            query["username"] = username
            count = databases.deploy.count_documents(query)
            if not count or role != Role.SuperUser.value:
                return {"Message": "Fail", "Reason": "The project is not yours."}, 403
            deleted = storages.delete(project, version)
        else:
            query = {}
        # 允许用户自定义删除条件
        result = databases.deploy.delete_one(query)
        count = result.deleted_count
        return {"count": count, "deleted": deleted, "query": query}