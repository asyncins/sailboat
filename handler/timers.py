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
from components.enums import Role

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
        * @apiParam {Dict} [query]  {"project": "fabias"} \
        OR \
        {}
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "data": [
                {
                  "create": "2019-12-07 23:59:25",
                  "id": "5debcc5d4d35f8694c0a833d",
                  "mode": null,
                  "project": "fabias",
                  "rule": "{\"mode\": \"cron\", }",
                  "version": "1575734359",
                  "idn": "897hj5d4d35f8694c0a833d",
                  "username": "nona",
                  "jid": "92836c98-30eb-429c-a29f-60d3a48de5b8"
                },
                {
                  "create": "2019-12-08 16:02:53",
                  "id": "5decae2d14c1b8b9d2945256",
                  "mode": "interval",
                  "project": "fabias",
                  "rule": "198",
                  "version": "1575734359",
                  "idn": "897hj5d4d35f8694c0a833d",
                  "username": "nona",
                  "jid": "92836c98-902j-nm16-a29f-60d3a48d8ij7"
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
        finds = databases.timers.find(query)
        message = {"data": [{
            "id": str(i.get('_id')),
            "project": i.get("project"),
            "version": i.get("version"),
            "mode": i.get("mode"),
            "rule": i.get("rule"),
            "jid": i.get("jid"),
            "idn": i.get("idn"),
            "username": i.get("username"),
            "create": i.get("create").strftime("%Y-%m-%d %H:%M:%S")}
            for i in finds]}
        return message

    @authorization
    def post(self):
        """项目调度
        * @api {post} /timer/ 项目调度
        * @apiPermission Role.Developer AND Owner
        * @apiDescription 用户只能为属于自己的项目设定调度计划
        * @apiParam {String} project 项目名称 - coders
        * @apiParam {String} version 项目版本号 - 1575734359
        * @apiParam {String} mode 周期类型 - date/interval/cron
        * @apiParam {Dict} rule 周期规则 - {"hour": "*", "minute": "*", "second": "*/20"}
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {"Message": "Fail", "Reason": "Missing Parameter"}
        * @apiSuccessExample {json} Success-Response:
            # status code: 201
            {
              "Message": "Success",
              "inserted": "5df1b353dd7474fd64a41fd5",
              "jid": "fc750591-70d7-42fb-a599-ded02815ec23",
              "project": "fabias",
              "version": "1575734359"
            }
        """
        project = request.json.get('project')
        version = request.json.get('version')
        mode = request.json.get('mode')
        rule = request.json.get('rule')
        if not project or not rule or not version:
            return {"Message": "Fail", "Reason": "Missing Parameter"}, 400
        if not storages.exists(project, version):
            return {"Message": "Fail", "Reason": "File Not Found"}, 400
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
            return {"Message": "Fail", "Reason": "The project is not yours"}, 403
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
                        **json.loads(rule))
        except ValueError:
            return {"Message": "Fail", "Reason": "Parameter Error"}, 400
        return {"project": project, "version": version, "jid": jid, "inserted": str(inserted), "Message": "Success"}, 201

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
        * @apiParam {String} jid 任务编号 \
        0285c010-5dc4-4e6c-80e2-40db0ed5c3f8
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {"Message": "Fail", "Reason": "Missing Parameter"}
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
            'count': 1,
            'project': 'fabias',
            'version': '1575734359',
            'jid': '0ef5c607-cc90-49d6-bc9c-649621a2ddd8',
            'mode': 'cron',
            'rule': '{"hour": "*", "minute": "*", "second": "*/50"}',
            'create': '2019-40-12/12/19 11:40:28',
            'Message': 'Success'
            }
        """
        jid = request.json.get('jid')
        if not jid:
            # 确保任务参数存在
            return {"Message": "Fail", "Reason": "Missing Parameter"}, 400
        # 检查所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        query = {"jid": jid, "idn": idn, "username": username}
        count = databases.timers.count_documents(query)
        if not count or role != Role.SuperUser.value:
            return {"Message": "Fail", "Reason": "The timer is not yours."}, 403
        info = databases.timers.find_one(query)
        if not info:
            # 确保数据库中存储着对应任务
            return {"Message": "Fail", "Reason": "Job %s Not Found In Database" % jid}, 400
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
            return message
        except JobLookupError:
            # 处理因任务不存在引发的异常，将相关提示返回给用户
            return {"Message": "Fail", "Reason": "Job %s Not Found In JobStores" % jid}, 400

