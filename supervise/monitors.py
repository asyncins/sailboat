from datetime import datetime
from interface import Monitor


class MarkdownMonitor(Monitor):

    def __init__(self):
        self.keyword = "Alarm"
        self.err_image = "http://can.sfhfpc.com/sfhfpc/20191210133853.png"
        self.traceback_image = "http://can.sfhfpc.com/sfhfpc/20191210133616.png"

    def push(self, txt, occurrence, timer):
        """接收器
        被捕获到的异常信息将会送到这里"""

        # 将信息按行分割
        message = []
        line = ""
        for i in txt:
            if i != "\n":
                line += i
            else:
                message.append(line)
                line = ""
        err, traceback, res = self.extractor(message)
        content = self.recombination(err, traceback, res, occurrence, timer)
        return content

    def extractor(self, message):
        """拆分车间
        根据需求拆分异常信息"""
        result = []
        err_number = 0
        traceback_number = 0
        for k, v in enumerate(message):
            # 异常分类
            if "ERROR" in v:
                # 列别数量统计
                err_number += 1
                # 放入信息队列
                result.append(v)
            if "Traceback" in v:
                # 类别数量统计
                traceback_number += 1
                # 放入信息队列
                result += message[k:]
        return err_number, traceback_number, result

    def recombination(self, err, traceback, res, occurrence, timer):
        """重组车间
        异常信息将在这里重组"""
        title = "Traceback" if traceback else "Error"
        image = self.traceback_image if traceback else self.err_image
        err_message = "\n\n > ".join(res)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 按照钉钉文档中的 Markdown 格式示例构造信息
        article = "#### TOTAL -- Error Number: {}, Traceback Number: {} \n".format(err, traceback) + \
                  "> ![screenshot]({}) \n\n".format(image) + \
                  "> **Error message** \n\n" + \
                  "> {} \n\n".format(err_message) + \
                  "> -------- \n\n" + \
                  "> **Timer**\n\n> {} \n\n".format(timer) +\
                  "> -------- \n\n" + \
                  "> **Other information** \n\n" + \
                  "> Occurrence Time: {} \n\n".format(occurrence) + \
                  "> Send Time: {} \n\n".format(now) + \
                  "> Message Type: {}".format(self.keyword)

        content = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": article}
        }
        return content
