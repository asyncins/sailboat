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
        * @apiParam {Dict} [query]  {"project": "fabias"} OR {}
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "data": [
                {
                  "create": "2019-12-07 23:59:56",
                  "duration": "0:0:0",
                  "end": "2019-12-07 23:59:56",
                  "id": "5debcc7c4d35f8694c0a833e",
                  "inserted": "5debcc5d4d35f8694c0a833d",
                  "jid": null,
                  "job": "3da6718e-2e05-4324-bd24-1e8aec57355f",
                  "mode": null,
                  "project": "asyncins",
                  "rule": "{\"mode\": \"cron\", }",
                  "start": "2019-12-07 23:59:55",
                  "version": "1575734359",
                  "idn": "5df0ea19b46116479b46c27c",
                  "username": "sfhfpc"
                },
                {
                  "create": "2019-12-08 00:00:26",
                  "duration": "0:0:0",
                  "end": "2019-12-08 00:00:26",
                  "id": "5debcc9a4d35f8694c0a833f",
                  "inserted": "5debcc5d4d35f8694c0a833d",
                  "jid": null,
                  "job": "600a4eee-991d-4a7f-8b1b-827abe1507eb",
                  "mode": null,
                  "project": "fabias",
                  "rule": "{\"mode\": \"cron\", }",
                  "start": "2019-12-08 00:00:25",
                  "version": "1575734359",
                  "idn": "5df0ea19b46116479b46c27c",
                  "username": "sfhfpc"
                }
            ]
        }

        """
        query = request.json.get('query')
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
        finds = databases.record.find(query)
        message = {"data": [{
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
            for i in finds]}
        return message