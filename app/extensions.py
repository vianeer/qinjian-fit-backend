from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

# 扩展对象仅在这里初始化，避免模型和视图之间循环 import。
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
