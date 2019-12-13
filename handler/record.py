"""
https://flask.palletsprojects.com/en/1.1.x/api/?highlight=route#flask.views.MethodView
https://flask.palletsprojects.com/en/1.1.x/api/#flask.request
https://werkzeug.palletsprojects.com/en/0.16.x/datastructures/#werkzeug.datastructures.FileStorage
https://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.insert_one
https://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.find
https://api.mongodb.com/python/current/api/pymongo/collection.html?highlight=delete#pymongo.collection.Collection.delete_one
"""
import json
from flask.views import MethodView
from flask import request

from components.storage import FileStorages
from connect import databases
from components.auth import authorization, get_user_info
from components.enums import Role


storages = FileStorages()


class RecordsHandler(MethodView):
    """执行记录视图
    """

    permission = {"permission": Role.Other}

    @authorization
    def get(self):
        """
        * @api {get} /record/ 获取执行记录列表
        * @apiPermission Role.Developer AND Owner
        * @apiDescription 用户只能查看自己设定的调度计划生成的记录
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {String} [username] 用户名
        * @apiParam {String} [idn] 用户 ID
        * @apiParam {String} [project] 项目名称
        * @apiParam {Int} [version] 版本号
        * @apiParam {String="cron", "interval", "date"} [mode] 时间类型
        * @apiParam {Int} [limit=0] Limit
        * @apiParam {Int} [skip=0] Skip
        * @apiParam {String="create", "status", "role"} [order=create] 排序字段
        * @apiParam {Int=1, -1} [sort=1] 排序方式
        * @apiParamExample Param-Example
            /record?version=1576206368&order=version&sort=-1
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 200,
              "data": {
                "data": [
                  {
                    "create": "2019-12-13 09:20:00",
                    "duration": "0:0:0",
                    "end": "2019-12-13 09:20:00",
                    "id": "5df2e74005db1557d78b16d7",
                    "idn": "5df0ea19b46116479b46c27c",
                    "inserted": "5df2e70a0286cdc6a686b9df",
                    "jid": "5a36346b-1f28-41de-a94e-b28c550acc42",
                    "job": "3e5aecfb-2f46-42ea-b492-bbcc1e1219ca",
                    "mode": "cron",
                    "project": "videos",
                    "rule": {
                      "hour": "*",
                      "minute": "*",
                      "second": "*/30"
                    },
                    "start": "2019-12-13 09:20:00",
                    "username": "sfhfpc",
                    "version": "1576199082"
                  },
                  {
                    "create": "2019-12-13 09:24:00",
                    "duration": "0:0:0",
                    "end": "2019-12-13 09:24:00",
                    "id": "5df2e83017040767e3bd7076",
                    "idn": "5df0ea19b46116479b46c27c",
                    "inserted": "5df2e70a0286cdc6a686b9df",
                    "jid": "5a36346b-1f28-41de-a94e-b28c550acc42",
                    "job": "8fe33a65-c568-47af-8e0f-911c064d02a3",
                    "mode": "cron",
                    "project": "videos",
                    "rule": {
                      "hour": "*",
                      "minute": "*",
                      "second": "*/30"
                    },
                    "start": "2019-12-13 09:24:00",
                    "username": "sfhfpc",
                    "version": "1576199082"
                  }
                ]
              },
              "message": "success"
            }

        """
        query = {}
        # 检查所有权
        token = request.headers.get("Authorization")
        auth_idn, auth_username, auth_role = get_user_info(token)
        if auth_role != Role.SuperUser.value:
            username = request.args.get('username')
            idn = request.args.get('idn')
        else:
            username = auth_username
            idn = auth_idn
        project = request.args.get('project')
        version = request.args.get('version')
        mode = request.args.get('mode')

        order = request.args.get('order') or "create"
        sor = request.args.get('sort') or 1
        limit = request.args.get('limit') or 0
        skip = request.args.get('skip') or 0
        if project:
            query["project"] = project
        if version:
            query["version"] = version
        if mode:
            query["mode"] = mode
        if username:
            query["username"] = username
        if idn:
            query["idn"] = idn
        # 允许用户自定义查询条件
        result = databases.record.find(query).limit(int(limit)).skip(int(skip)).sort(order, int(sor))
        information = []
        for i in result:
            info = {
                "id": str(i.get('_id')),
                "project": i.get("project"),
                "version": i.get("version"),
                "mode": i.get("mode"),
                "rule": i.get("rule"),
                "job": i.get("job"),
                "jid": i.get("jid"),
                "start": i.get("start"),
                "duration": i.get("duration"),
                "end": i.get("end"),
                "inserted": i.get("inserted"),
                "idn": idn,
                "username": username,
                "create": i.get("create").strftime("%Y-%m-%d %H:%M:%S")}
            information.append(info)
        return {"message": "success",
                "data": information,
                "code": 200}
