"""
https://flask.palletsprojects.com/en/1.1.x/api/?highlight=route#flask.views.MethodView
"""
import psutil
from pymongo import DESCENDING
from flask.views import MethodView
from connect import databases, client
from components.auth import authorization
from components.enums import Role, StatusCode


class IndexHandler(MethodView):

    permission = {"permission": Role.Other}

    @authorization
    def get(self):
        """
        * @api {get} /work 工作台信息
        * @apiPermission Role.Other
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiSuccess {Int} deploys 项目总数
        * @apiSuccess {Int} jobs 任务总数
        * @apiSuccess {Int} records 执行记录总数
        * @apiSuccess {Int} timers 调度总数
        * @apiSuccess {Int} users 用户总数
        * @apiSuccess {Int} cpu_count 中央处理器核心数量
        * @apiSuccess {Int} cpu_logical_count 中央处理器物理核心数量
        * @apiSuccess {Int} cpu_use_percent 中央处理器使用率
        * @apiSuccess {Int} memory_total 内存总量
        * @apiSuccess {Int} usememory_use_percentrs 内存使用率
        * @apiSuccess {List} difference 未调用过的项目
        * @apiSuccess {Dict} max_count 调用最多的项目和次数
        * @apiSuccess {Dict} duration 运行时长最长的调度计划信息
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "code": 200,
              "data": {
                "hardware": {
                  "cpu_count": 4,
                  "cpu_logical_count": 4,
                  "cpu_use_percent": 25.1,
                  "memory_total": 16,
                  "memory_use_percent": 68.6
                },
                "most": [
                  {
                    "difference": [],
                    "duration": {},
                    "max_count": {}
                  },
                  400
                ],
                "total": {
                  "deploys": 1,
                  "jobs": 0,
                  "records": 0,
                  "timers": 0,
                  "users": 3
                }
              },
              "message": "success"
            }
        """
        total = self.quantity_total()
        hardware = self.hardware_resource()
        most = self.quantity_most()
        return {"message": "success",
                "data": {"total": total, "hardware": hardware, "most": most},
                "code": 200}

    @staticmethod
    def quantity_total():
        """数据库各项数量统计
        部署项目数
        调度计划数
        执行记录数
        任务队列数
        """
        deploys = databases.deploy.count_documents({})
        timers = databases.timer.count_documents({})
        records = databases.record.count_documents({})
        users = databases.user.count_documents({})
        jobs = client.apscheduler.jobs.count_documents({})
        message = {"deploys": deploys, "timers": timers,
                   "records": records, "users": users,
                   "jobs": jobs}
        return message

    @staticmethod
    def hardware_resource():
        """服务器资源信息
        内存相关信息，单位：GB
        中央处理器相关信息
        """
        memory_view = psutil.virtual_memory()
        # 内存总量，单位：GB
        memory_total = memory_view.total // pow(1024, 3)
        # 内存使用量，单位：GB
        memory_free = memory_view.free // pow(1024, 3)
        # 内存使用率
        memory_use_percent = memory_view.percent

        # 中央处理器核心数
        cpu_count = psutil.cpu_count()
        # 中央处理器逻辑核心数
        cpu_logical_count = psutil.cpu_count(logical=True)
        # 中央处理器使用率
        cpu_use_percent = psutil.cpu_percent()

        message = {"memory_total": memory_total, "memory_use_percent": memory_use_percent,
                   "cpu_count": cpu_count, "cpu_logical_count": cpu_logical_count,
                   "cpu_use_percent": cpu_use_percent}
        return message

    @staticmethod
    def quantity_most():
        """指标之最
        """
        # 运行时长之最
        k = databases.record.count_documents({})
        if not k:
            return {"duration": {}, "max_count": {}, "difference": []}, 400
        duration = databases.record.find_one({}, sort=[('duration', DESCENDING)])
        # 通过聚合操作将字段值进行分类并统计，并将统计数量按降序排序
        pipeline = [
            {"$group": {"_id": "$project", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        command_cursor = databases.record.aggregate(pipeline)
        # 弹出第一条记录，由于降序排序，所以被弹出的就是出现次数最多的记录
        max_count = command_cursor.next()

        pipeline = [
            {"$group": {"_id": "$project", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        invoke = set(i.get("_id") for i in databases.deploy.aggregate(pipeline))
        invoked = set(k.get("_id") for k in command_cursor)
        # 求差集得出未被调用过的项目集合
        difference = tuple(invoked.difference(invoke))
        drop = duration.pop("_id")
        message = {"duration": duration, "max_count": max_count, "difference": difference}
        return message






