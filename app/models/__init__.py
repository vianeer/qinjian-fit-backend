"""统一导出模型，便于 create_all、种子脚本和其他模块使用。"""

from .diet import DietMeal, DietTemplate
from .equipment import Equipment, EquipmentCategory, EquipmentOccupancyReport
from .knowledge import KnowledgeArticle, KnowledgeCategory, KnowledgeTip
from .training import TrainingPlan, TrainingPlanItem, TrainingSetRecord
from .user import Admin, User

__all__ = [
    "Admin",
    "User",
    "EquipmentCategory",
    "Equipment",
    "EquipmentOccupancyReport",
    "TrainingPlan",
    "TrainingPlanItem",
    "TrainingSetRecord",
    "DietTemplate",
    "DietMeal",
    "KnowledgeCategory",
    "KnowledgeArticle",
    "KnowledgeTip",
]
