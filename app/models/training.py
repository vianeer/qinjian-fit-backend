from datetime import date, datetime

from ..extensions import db
from .types import BIGINT_PK


class TrainingPlan(db.Model):
    __tablename__ = "training_plans"

    id = db.Column(BIGINT_PK, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_date = db.Column(db.Date, nullable=False, default=date.today)
    body_parts = db.Column(db.JSON, nullable=False)
    status = db.Column(
        db.Enum("draft", "in_progress", "completed", "cancelled"),
        nullable=False,
        default="draft",
    )
    total_sets = db.Column(db.SmallInteger, nullable=False, default=0)
    completed_sets = db.Column(db.SmallInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    items = db.relationship(
        "TrainingPlanItem",
        backref="plan",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="TrainingPlanItem.sort_order",
    )
    set_records = db.relationship(
        "TrainingSetRecord",
        backref="plan",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_items=True):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "plan_date": self.plan_date.isoformat(),
            "body_parts": self.body_parts or [],
            "status": self.status,
            "total_sets": self.total_sets,
            "completed_sets": self.completed_sets,
            "progress": round(self.completed_sets / self.total_sets * 100)
            if self.total_sets
            else 0,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class TrainingPlanItem(db.Model):
    __tablename__ = "training_plan_items"

    id = db.Column(BIGINT_PK, primary_key=True)
    plan_id = db.Column(
        BIGINT_PK, db.ForeignKey("training_plans.id"), nullable=False
    )
    equipment_id = db.Column(
        db.Integer, db.ForeignKey("equipment.id"), nullable=False
    )
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    target_sets = db.Column(db.SmallInteger, nullable=False)
    target_reps = db.Column(db.String(20), nullable=False)
    rest_seconds = db.Column(db.SmallInteger, nullable=False)

    equipment = db.relationship("Equipment", lazy=True)

    def completed_set_numbers(self):
        return [
            record.set_number
            for record in TrainingSetRecord.query.filter_by(plan_item_id=self.id)
            .order_by(TrainingSetRecord.set_number)
            .all()
        ]

    def to_dict(self):
        completed = self.completed_set_numbers()
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "equipment_id": self.equipment_id,
            "equipment": self.equipment.to_dict() if self.equipment else None,
            "sort_order": self.sort_order,
            "target_sets": self.target_sets,
            "target_reps": self.target_reps,
            "rest_seconds": self.rest_seconds,
            "completed_set_numbers": completed,
            "completed_count": len(completed),
            "is_completed": len(completed) >= self.target_sets,
        }


class TrainingSetRecord(db.Model):
    __tablename__ = "training_set_records"
    __table_args__ = (
        db.UniqueConstraint("plan_item_id", "set_number", name="uk_plan_item_set"),
    )

    id = db.Column(BIGINT_PK, primary_key=True)
    plan_id = db.Column(
        BIGINT_PK, db.ForeignKey("training_plans.id"), nullable=False
    )
    plan_item_id = db.Column(
        BIGINT_PK, db.ForeignKey("training_plan_items.id"), nullable=False
    )
    set_number = db.Column(db.SmallInteger, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "plan_item_id": self.plan_item_id,
            "set_number": self.set_number,
            "completed_at": self.completed_at.isoformat(),
        }

