import os
import json
from json.decoder import JSONDecodeError
from flask.views import MethodView
from flask import request
import jwt

from settings import LOGPATH
from components.auth import authorization, get_user_info
from components.enums import Role
from settings import SECRET, ALG
from connect import databases


class LogHandler(MethodView):

    permission = {"permission": Role.Developer}

    @authorization
    def get(self):
        """
        * @api {get} /logs 获取指定日志的信息
        * @apiPermission Role.Developer AND Owner
        * @apiDescription 用户只能查看自己设定的调度计划生成的日志
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {String} project  coders
        * @apiParam {String} job 1c06cca5-a165-48b6-8f28-bdfdcf51ceda
        @apiErrorExample {json} Error-Response:
            # status code: 400
            {"Message": "Fail", "Reason": "Missing Parameter"}
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {
              "content": "Traceback (most recent call last):\n  File \"/Users/async/Documents/Onedrive/进阶宝典/Pheibook/sailboat/executor/boat.py\", line 46, in <module>\n    main(project, version)\n  File \"/Users/async/Documents/Onedrive/进阶宝典/Pheibook/sailboat/executor/boat.py\", line 40, in main\n    spider = import_module(MODULERNAME)\n  File \"/Users/async/anaconda3/envs/slp/lib/python3.6/importlib/__init__.py\", line 126, in import_module\n    return _bootstrap._gcd_import(name[level:], package, level)\n  File \"<frozen importlib._bootstrap>\", line 994, in _gcd_import\n  File \"<frozen importlib._bootstrap>\", line 971, in _find_and_load\n  File \"<frozen importlib._bootstrap>\", line 953, in _find_and_load_unlocked\nModuleNotFoundError: No module named 'sail'\n",
              "size": "743 byte"
            }
        """
        project = request.form.get("project")
        job = request.form.get("job")
        if not project or not job:
            return {"Message": "Fail", "Reason": "Missing Parameter"}, 400
        filename = os.path.join(LOGPATH, project, "%s.log" % job)
        if not os.path.exists(filename):
            return {"Message": "Fail", "Reason": "File Not Found"}, 400
        # 检查所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        count = 1
        if role != Role.SuperUser.value:
            count = databases.record.count_documents({{"idn": idn, "username": username}})
        if not count:
            return {"Message": "Fail", "Reason": "The log file is not yours"}, 403
        with open(filename, "r") as file:
            content = file.read()
        # 计算日志文件大小
        unit = "byte"
        size = os.path.getsize(filename)
        if size > 1024:
            unit = "kb"
            size = size // 1024
        if size > 1024:
            unit = "mb"
            size = size // 1024
        return {"size": "%s %s" % (size, unit), "content": content}

    @authorization
    def delete(self):
        """
        * @api {delete} /logs/ 删除指定日志
        * @apiPermission Role.Superuser
        * @apiDescription 管理员才能删除日志
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Json} querys 删除指定文件 [{"project": "fabias", "job": "19ca5bec-a009-4c29-96af-fe9973ecd9d3"}]
        * @apiErrorExample {json} Error-Response:
            # status code: 400
            {
              "Message": "Fail",
              "Reason": "File Not Found"
            }
        * @apiSuccessExample {json} Success-Response:
            # status code: 200
            {'Message': 'Success', 'Count': 1,
            'path': ['fabias/19ca5bec-a009-4c29-96af-fe9973ecd9d3.log']}
        """
        try:
            # 确保参数格式正确
            querys = json.loads(request.form.get("querys"))
            token = request.headers.get("Authorization")
            idn, username, role = get_user_info(token)
            if role != Role.SuperUser.value:
                return {"Message": "Fail", "Reason": "No Auth"}, 403
        except JSONDecodeError:
            return {"Message": "Fail", "Reason": "JSONDecode Error"}, 400
        if not isinstance(querys, list):
            return {"Message": "Fail", "Reason": "Parameter Type Error"}, 400
        for query in querys:
            # 检查文件是否均存在
            project = query.get("project")
            job = query.get("job")
            if not project or not job:
                return {"Message": "Fail", "Reason": "Parameter Error"}, 400
            filename = os.path.join(LOGPATH, project, "%s.log" % job)
        if not os.path.exists(filename):
            return {"Message": "Fail", "Reason": "File Not Found"}, 400
        result = []
        for query in querys:
            # 确保文件均存在才删除
            project = query.get("project")
            job = query.get("job")
            if "." in project or "/" in project or "." in job or "/" in job:
                # . or / 防止恶意参数删除系统目录
                return {"Message": "Fail", "Reason": "Path Error"}, 400
            filename = os.path.join(LOGPATH, project, "%s.log" % job)
            os.remove(filename)
            drop = "%s/%s.log" % (project, job)
            result.append(drop)
        return {"Message": "Success", "Count": len(result),
                "path": result}

