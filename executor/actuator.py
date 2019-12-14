import os
import sys
import logging
import subprocess
from datetime import datetime
from uuid import uuid4
import logging

from settings import LOGPATH, RIDEPATH
from connect import databases
from supervise.alarms import DingAlarm


def delta_format(delta):
    """时间差格式化
    将时间差格式转换为时分秒"""
    seconds = delta.seconds
    minutes, second = divmod(seconds, 60)
    hour, minute = divmod(minutes, 60)
    return "%s:%s:%s" % (hour, minute, second)


def time_format(start_time, end_time):
    """时间格式化
    将时间格式转换为年月日时分秒
    """
    duration = delta_format(end_time - start_time)
    start = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end = end_time.strftime("%Y-%m-%d %H:%M:%S")
    return start, end, duration


def performer(*args, **kwargs):
    """调用执行器
    获取 stdout stderr
    生成日志文件名
    将日志写入文件
    将执行信息、执行结果结果，包括启动时间和结束时间和运行时长存入数据库
    """
    job = str(uuid4())

    project, version, mode, rule, jid, idn, username = args
    logging.warning("args:\n", args)
    # 开启子进程调用执行器
    instructions = ['-m', RIDEPATH, project, version]
    start = datetime.now()
    sub = subprocess.Popen(instructions, executable=sys.executable,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = sub.communicate()
    end = datetime.now()
    out, err = "", ""
    try:
        out = stdout.decode("utf8")
        err = stderr.decode("utf8")
    except Exception as exc:
        logging.warning(exc)
    start, end, duration = time_format(start, end)
    if not os.path.exists(LOGPATH):
        os.makedirs(LOGPATH)
    room = os.path.join(LOGPATH, project)
    if not os.path.exists(room):
        os.makedirs(room)
    log = os.path.join(room, "%s.log" % job)
    with open(log, 'w') as file:
        # 将子进程输出写入日志文件
        file.write(out)
        file.write(err)
    # 构造执行记录并存储到数据库
    message = {"project": project, "version": version,
               "mode": mode, "rule": rule,
               "job": job,
               "start": start, "end": end,
               "duration": duration, "jid": jid,
               "idn": idn, "username": username,
               "create": datetime.now()}
    databases.record.insert_one(message).inserted_id

    if err:
        # 如果项目运行期间有异常产生则触发异常监控和警报器
        DingAlarm().receive(err, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message)
