from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from connect import client
from flask_cors import CORS

# 将任务信息存储到 SQLite
# store = {
#     'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
# }

# 将任务信息存储到 MongoDB
store = {"default": MongoDBJobStore(client=client)}
scheduler = BackgroundScheduler(jobstores=store)


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

