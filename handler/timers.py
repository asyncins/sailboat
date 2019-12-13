"""
https://flask.palletsprojects.com/en/1.1.x/api/?highlight=route#flask.views.MethodView
https://flask.palletsprojects.com/en/1.1.x/api/#flask.request
https://werkzeug.palletsprojects.com/en/0.16.x/datastructures/#werkzeug.datastructures.FileStorage
https://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.insert_one
https://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.find
https://api.mongodb.com/python/current/api/pymongo/collection.html?highlight=delete#pymongo.collection.Collection.delete_one
"""
import json
from datetime import datetime
from flask.views import MethodView
from flask import request
from uuid import uuid4
from apscheduler.jobstores.base import JobLookupError

from components.storage import FileStorages
from connect import databases
from common import scheduler
from executor.actuator import performer
from components.auth import authorization, get_user_info
from components.enums import Role, StatusCode

storages = FileStorages()


class TimersHandler(MethodView):

    permission = {"permission": Role.Developer}

    @authorization
    def get(self):
        """
        * @api {get} /timer/ 获取调度计划列表
        * @apiPermission Role.Developer AND Owner
        * @apiDescription 用户只能查看自己设定的调度计划
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
            /timer?project=football&order=version&sort=-1
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 200,
              "data": [
                {
                  "create": "2019-12-13 09:19:06",
                  "id": "5df2e70a0286cdc6a686b9df",
                  "idn": "5df0ea19b46116479b46c27c",
                  "jid": "5a36346b-1f28-41de-a94e-b28c550acc42",
                  "mode": "cron",
                  "project": "videos",
                  "rule": {
                    "hour": "*",
                    "minute": "*",
                    "second": "*/30"
                  },
                  "username": "sfhfpc",
                  "version": "1576199082"
                }
              ],
              "message": "success"
            }
        """
        query = {}
        # 检查所有权
        token = request.headers.get("Authorization")
        auth_idn, auth_username, auth_role = get_user_info(token)
        if auth_role != Role.SuperUser.value:
            username = auth_username
            idn = auth_idn
        else:
            username = request.args.get('username')
            idn = request.args.get('idn')
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
        # 从数据库中取出符合条件的数据
        result = databases.timers.find(query).limit(int(limit)).skip(int(skip)).sort(order, int(sor))
        # 构造返回信息
        information = []
        for i in result:
            info = {
                "id": str(i.get('_id')),
                "project": i.get("project"),
                "version": i.get("version"),
                "mode": i.get("mode"),
                "rule": i.get("rule"),
                "jid": i.get("jid"),
                "idn": i.get("idn"),
                "username": i.get("username"),
                "create": i.get("create").strftime("%Y-%m-%d %H:%M:%S")
            }
            information.append(info)
        return {"message": "success", "data": information, "code": 200}

    @authorization
    def post(self):
        """项目调度
        * @api {post} /timer/ 项目调度
        * @apiPermission Role.Developer AND Owner
        * @apiDescription 用户只能为属于自己的项目设定调度计划
        * @apiParam {String} project 项目名称 - coders
        * @apiParam {String} version 项目版本号 - 1575734359
        * @apiParam {String="cron", "interval", "date"} mode 周期类型参考 APScheduler
        * @apiParam {Dict} rule 周期规则参考 APScheduler
        * @apiParamExample Param-Example
            {
                "project": "lol",
                "version": "1576206368",
                "mode": "cron",
                "rule": {"hour": "*", "minute": "*/15"}
            }
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {
              "code": 4002,
              "data": {},
              "message": "not found"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 201
            {
              "code": 201,
              "data": {
                "inserted": "5df2e70a0286cdc6a686b9df",
                "jid": "5a36346b-1f28-41de-a94e-b28c550acc42",
                "project": "videos",
                "version": "1576199082"
              },
              "message": "success"
            }
        """
        project = request.json.get('project')
        version = request.json.get('version')
        mode = request.json.get('mode')
        rule = request.json.get('rule')
        if not project or not rule or not version:
            return {"message": StatusCode.ParameterError.value[0],
                    "data": {},
                    "code": StatusCode.ParameterError.value[1]
                    }, 400
        if not storages.exists(project, version):
            return {"message": StatusCode.NotFound.value[0],
                    "data": {},
                    "code": StatusCode.NotFound.value[1]
                    }, 400
        # 检查所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        count = 1
        if role != Role.SuperUser.value:
            count = databases.deploy.count_documents(
                {
                    "project": project, "version": version,
                    "idn": idn, "username": username
                }
            )
        if not count:
            return {"message": StatusCode.IsNotYours.value[0],
                    "data": {},
                    "code": StatusCode.IsNotYours.value[1]
                    }, 403
        # 生成唯一值作为任务标识
        jid = str(uuid4())
        # 将信息保存到数据库
        message = {"project": project, "version": version,
                   "mode": mode, "rule": rule,
                   "jid": jid, "idn": idn,
                   "username": username,
                   "create": datetime.now()}
        inserted = databases.timers.insert_one(message).inserted_id
        # 添加任务，这里用双星号传入时间参数
        try:
            scheduler.add_job(performer, mode, id=jid,
                        args=[project, version, mode, rule, jid, str(inserted), idn, username],
                        **rule)
        except ValueError:
            return {"message": StatusCode.ParameterError.value[0],
                    "data": {},
                    "code": StatusCode.ParameterError.value[1]
                    }, 400
        return {"message": "success",
                "data": {"project": project, "version": version, "jid": jid, "inserted": str(inserted)},
                "code": 201}, 201

    def put(self):
        # 暂不开放任务更新接口
        pass

    @authorization
    def delete(self):
        """
        * @api {delete} /timer/ 删除指定任务
        * @apiPermission Role.Developer AND Owner
        * @apiDescription 用户只能删除自己设定的调度计划
        * @apiHeader (Header) {String} Authorization Authorization value.

        * @apiParam {Json} jid 任务 ID
        * @apiParamExample Param-Example
            {"jid": "5a36346b-1f28-41de-a94e-b28c550acc342"}
        * @apiErrorExample {json} Error-Response:
            # status code: 403
            {
              "code": 4002,
              "data": {},
              "message": "is not yours"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 204,
              "data": {
                "Message": "Success",
                "count": 1,
                "create": "2019-19-12/13/19 09:19:06",
                "jid": "5a36346b-1f28-41de-a94e-b28c550acc42",
                "mode": "cron",
                "project": "videos",
                "rule": {
                  "hour": "*",
                  "minute": "*",
                  "second": "*/30"
                },
                "version": "1576199082"
              },
              "message": "success"
            }
        """
        jid = request.json.get('jid')
        if not jid:
            # 确保任务参数存在
            return {"message": StatusCode.ParameterError.value[0],
                    "data": {},
                    "code": StatusCode.ParameterError.value[1]
                    }, 400
        # 检查所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        query = {"jid": jid, "idn": idn, "username": username}
        count = databases.timers.count_documents(query)
        if not count or role != Role.SuperUser.value:
            return {"message": StatusCode.IsNotYours.value[0],
                    "data": {},
                    "code": StatusCode.IsNotYours.value[1]
                    }, 403
        info = databases.timers.find_one(query)
        if not info:
            # 确保数据库中存储着对应任务
            return {"message": StatusCode.NotFound.value[0],
                    "data": {},
                    "code": StatusCode.NotFound.value[1]
                    }, 400
        # 如果指定的任务不存在会引发指定类型的异常
        try:
            # 从数据库和任务列表中移除指定任务
            scheduler.remove_job(jid)
            result = databases.timers.delete_one(query)
            message = {"count": result.deleted_count, "project": info.get("project"),
                    "version": info.get("version"), "jid": jid,
                    "mode": info.get("mode"), "rule": info.get("rule"),
                    "create": info.get("create").strftime("%Y-%M-%D %H:%M:%S"),
                    "Message": "Success"}
            return {"message": "success", "data": message, "code": 204}, 200
        except JobLookupError:
            # 处理因任务不存在引发的异常，将相关提示返回给用户
            return {"message": StatusCode.NotFound.value[0],
                    "data": {},
                    "code": StatusCode.NotFound.value[1]
                    }, 400

