from datetime import datetime

from ..extensions import db


class DietTemplate(db.Model):
    __tablename__ = "diet_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    fitness_goal = db.Column(
        db.Enum("muscle_gain", "fat_loss", "shaping"), nullable=False
    )
    gender = db.Column(db.Enum("male", "female", "other"))
    body_part = db.Column(db.String(30))
    meal_count = db.Column(db.SmallInteger, nullable=False, default=3)
    total_calories = db.Column(db.SmallInteger, nullable=False)
    tips = db.Column(db.String(500), nullable=False, default="")
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    meals = db.relationship(
        "DietMeal",
        backref="template",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="DietMeal.sort_order",
    )

    def to_dict(self, include_meals=True):
        data = {
            "id": self.id,
            "name": self.name,
            "fitness_goal": self.fitness_goal,
            "gender": self.gender,
            "body_part": self.body_part,
            "meal_count": self.meal_count,
            "total_calories": self.total_calories,
            "tips": self.tips,
            "is_enabled": bool(self.is_enabled),
        }
        if include_meals:
            data["meals"] = [meal.to_dict() for meal in self.meals]
        return data


class DietMeal(db.Model):
    __tablename__ = "diet_meals"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer, db.ForeignKey("diet_templates.id"), nullable=False
    )
    meal_type = db.Column(
        db.Enum("breakfast", "lunch", "dinner", "snack"), nullable=False
    )
    food_items = db.Column(db.JSON, nullable=False)
    target_calories = db.Column(db.SmallInteger, nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        labels = {
            "breakfast": "早餐",
            "lunch": "午餐",
            "dinner": "晚餐",
            "snack": "加餐",
        }
        return {
            "id": self.id,
            "meal_type": self.meal_type,
            "meal_name": labels.get(self.meal_type, self.meal_type),
            "food_items": self.food_items or [],
            "target_calories": self.target_calories,
            "sort_order": self.sort_order,
        }
