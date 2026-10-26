from datetime import datetime

from ..extensions import db
from .types import BIGINT_PK


class EquipmentCategory(db.Model):
    __tablename__ = "equipment_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    slug = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    equipment_list = db.relationship("Equipment", backref="category", lazy=True)

    def to_dict(self, include_count=False):
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "sort_order": self.sort_order,
        }
        if include_count:
            data["equipment_count"] = (
                Equipment.query.filter_by(category_id=self.id, is_active=True).count()
            )
        return data


class Equipment(db.Model):
    __tablename__ = "equipment"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("equipment_categories.id"), nullable=False
    )
    name = db.Column(db.String(80), nullable=False)
    cover_url = db.Column(db.String(500), nullable=False, default="")
    image_urls = db.Column(db.JSON)
    description = db.Column(db.Text, nullable=False)
    action_key_points = db.Column(db.Text, nullable=False)
    force_points = db.Column(db.Text, nullable=False)
    common_mistakes = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(500), nullable=False, default="")
    recommended_sets = db.Column(db.SmallInteger, nullable=False, default=3)
    recommended_reps = db.Column(db.String(20), nullable=False, default="12")
    rest_seconds = db.Column(db.SmallInteger, nullable=False, default=60)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # 训练流程自动占用字段：仅扩展现有 equipment 表，不创建新表。
    occupy_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    occupy_start_time = db.Column(db.DateTime, nullable=True)
    occupy_status = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 历史上报表保留用于管理员异常排查，但不再参与小程序占用状态计算。
    occupancy_reports = db.relationship(
        "EquipmentOccupancyReport",
        backref="equipment",
        lazy=True,
        cascade="all, delete-orphan",
    )
    occupy_user = db.relationship(
        "User", foreign_keys=[occupy_user_id], lazy="joined"
    )

    @property
    def occupy_status_text(self):
        """列表和详情统一展示：空闲 / 占用（XX同学训练中）。"""
        if not self.occupy_status:
            return "空闲"
        nickname = self.occupy_user.nickname if self.occupy_user else "其他同学"
        if not nickname.endswith("同学"):
            nickname = f"{nickname}同学"
        return f"占用（{nickname}训练中）"

    def to_dict(self, include_details=False):
        data = {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "",
            "name": self.name,
            "cover_url": self.cover_url,
            "description": self.description,
            "recommended_sets": self.recommended_sets,
            "recommended_reps": self.recommended_reps,
            "rest_seconds": self.rest_seconds,
            "occupy_user_id": self.occupy_user_id,
            "occupy_start_time": self.occupy_start_time.isoformat()
            if self.occupy_start_time
            else None,
            "occupy_status": int(self.occupy_status or 0),
            "occupy_status_text": self.occupy_status_text,
        }
        if include_details:
            data.update(
                {
                    "image_urls": self.image_urls or [],
                    "action_key_points": self.action_key_points,
                    "force_points": self.force_points,
                    "common_mistakes": self.common_mistakes,
                    "video_url": self.video_url,
                    "ai_placeholder": {
                        "enabled": False,
                        "message": "后续可接入 AI 全身照动作姿态展示，当前暂不实现 AI 识别逻辑",
                    },
                }
            )
        return data


class EquipmentOccupancyReport(db.Model):
    __tablename__ = "equipment_occupancy_reports"

    id = db.Column(BIGINT_PK, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    equipment_id = db.Column(
        db.Integer, db.ForeignKey("equipment.id"), nullable=False
    )
    status = db.Column(
        db.Enum("available", "busy", "maintenance"), nullable=False
    )
    note = db.Column(db.String(200), nullable=False, default="")
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "equipment_id": self.equipment_id,
            "user_id": self.user_id,
            "status": self.status,
            "note": self.note,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


