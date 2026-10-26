from flask import Blueprint

from .auth import auth_bp
from .diet import diet_bp
from .equipment import equipment_bp
from .knowledge import knowledge_bp
from .training import training_bp

api_bp = Blueprint("api", __name__)

# 各业务模块使用独立 Blueprint，便于测试和后续拆分。
api_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_bp.register_blueprint(equipment_bp, url_prefix="/equipment")
api_bp.register_blueprint(training_bp, url_prefix="/training")
api_bp.register_blueprint(diet_bp, url_prefix="/diet")
api_bp.register_blueprint(knowledge_bp, url_prefix="/knowledge")


@api_bp.get("/health")
def health():
    return {"code": 200, "message": "ok", "data": {"service": "campus-gym-api"}}
