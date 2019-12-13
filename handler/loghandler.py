import os
import json
from json.decoder import JSONDecodeError
from flask.views import MethodView
from flask import request

from settings import LOGPATH
from components.auth import authorization, get_user_info
from components.enums import Role, StatusCode
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
        * @apiParam {String} project 项目名称
        * @apiParam {String} job Job
        * @apiParamExample Param-Example
            /logs?project=videos&Job=3e5aecfb-2f46-42ea-b492-bbcc1e1219ca
        @apiErrorExample {json} Error-Response:
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
                "content": "Traceback (most recent call last):\n  File \"/Users/async/Documents/GithubProject/sailboat/executor/boat.py\", line 46, in <module>\n    main(project, version)\n  File \"/Users/async/Documents/GithubProject/sailboat/executor/boat.py\", line 40, in main\n    spider = import_module(MODULERNAME)\n  File \"/Users/async/anaconda3/envs/slp/lib/python3.6/importlib/__init__.py\", line 126, in import_module\n    return _bootstrap._gcd_import(name[level:], package, level)\n  File \"<frozen importlib._bootstrap>\", line 994, in _gcd_import\n  File \"<frozen importlib._bootstrap>\", line 971, in _find_and_load\n  File \"<frozen importlib._bootstrap>\", line 953, in _find_and_load_unlocked\nModuleNotFoundError: No module named 'sail'\n",
                "size": "709 byte"
              },
              "message": "success"
            }
        """
        project = request.args.get("project")
        job = request.args.get("job")
        if not project or not job:
            return {"message": StatusCode.MissingParameter.value[0],
                    "data": {},
                    "code": StatusCode.MissingParameter.value[1]
                    }, 400
        filename = os.path.join(LOGPATH, project, "%s.log" % job)
        if not os.path.exists(filename):
            return {"message": StatusCode.NotFound.value[0],
                    "data": {},
                    "code": StatusCode.NotFound.value[1]
                    }, 400
        # 检查所有权
        token = request.headers.get("Authorization")
        idn, username, role = get_user_info(token)
        count = 1
        if role != Role.SuperUser.value:
            count = databases.record.count_documents({{"idn": idn, "username": username}})
        if not count:
            return {"message": StatusCode.IsNotYours.value[0],
                    "data": {},
                    "code": StatusCode.IsNotYours.value[1]
                    }, 403
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
        return {"message": "success",
                "data": {"size": "%s %s" % (size, unit), "content": content},
                "code": 200}

    @authorization
    def delete(self):
        """
        * @api {delete} /logs/ 删除多个指定的日志文件
        * @apiPermission Role.Superuser
        * @apiDescription 管理员才能删除日志
        * @apiHeader (Header) {String} Authorization Authorization value.
        * @apiParam {Json} query 批量删除（指定的）日志文件
        @apiParamExample Param-Example:
            # 删除指定文件
            {
                "querys": [
                    {
                        "project": "videos",
                        "job": "3e5aecfb-2f46-42ea-b492-bbcc1e1219ca"
                    },
                    {
                        "project": "football",
                        "job": "5i8a9cfb-2f46-42ea-b492-b07c1e1201h6"
                    }
                ]
            }
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
                "count": 1,
                "path": [
                  "videos/3e5aecfb-2f46-42ea-b492-bbcc1e1219ca.log"
                ]
              },
              "message": "success"
            }
        """
        try:
            # 确保参数格式正确
            querys = request.json.get("querys")
            token = request.headers.get("Authorization")
            idn, username, role = get_user_info(token)
            if role != Role.SuperUser.value:
                return {"message": StatusCode.NoAuth.value[0],
                        "data": {},
                        "code": StatusCode.NoAuth.value[1]
                        }, 403
        except JSONDecodeError:
            return {"message": StatusCode.JsonDecodeError.value[0],
                    "data": {},
                    "code": StatusCode.JsonDecodeError.value[1]
                    }, 400
        if not isinstance(querys, list):
            return {"message": StatusCode.ParameterError.value[0],
                    "data": {},
                    "code": StatusCode.ParameterError.value[1]
                    }, 400
        for query in querys:
            # 检查文件是否均存在
            project = query.get("project")
            job = query.get("job")
            if not project or not job:
                return {"message": StatusCode.ParameterError.value[0],
                        "data": {},
                        "code": StatusCode.ParameterError.value[1]
                        }, 400
            filename = os.path.join(LOGPATH, project, "%s.log" % job)
        if not os.path.exists(filename):
            return {"message": StatusCode.NotFound.value[0],
                    "data": {},
                    "code": StatusCode.NotFound.value[1]
                    }, 400
        result = []
        for query in querys:
            # 确保文件均存在才删除
            project = query.get("project")
            job = query.get("job")
            if "." in project or "/" in project or "." in job or "/" in job:
                # . or / 防止恶意参数删除系统目录
                return {"message": StatusCode.PathError.value[0],
                        "data": {},
                        "code": StatusCode.PathError.value[1]
                        }, 400
            filename = os.path.join(LOGPATH, project, "%s.log" % job)
            os.remove(filename)
            drop = "%s/%s.log" % (project, job)
            result.append(drop)
        return {"message": "success",
                "data": {"path": result, "count": len(result)},
                "code": 200}
