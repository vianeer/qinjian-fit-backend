from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(50), nullable=False, default="管理员")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(128), unique=True, nullable=False)
    nickname = db.Column(db.String(50), nullable=False, default="校园健身用户")
    avatar_url = db.Column(
        db.String(500),
        nullable=False,
        default="https://placehold.co/200x200/png?text=Avatar",
    )
    age = db.Column(db.SmallInteger)
    height = db.Column(db.Numeric(5, 2))
    weight = db.Column(db.Numeric(5, 2))
    gender = db.Column(db.Enum("male", "female", "other"))
    fitness_goal = db.Column(db.Enum("muscle_gain", "fat_loss", "shaping"))
    profile_completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    training_plans = db.relationship(
        "TrainingPlan", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def bmi(self):
        if not self.height or not self.weight:
            return None
        height_m = float(self.height) / 100
        return round(float(self.weight) / (height_m * height_m), 1)

    def to_dict(self):
        return {
            "id": self.id,
            "openid": self.openid,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "age": self.age,
            "height": float(self.height) if self.height is not None else None,
            "weight": float(self.weight) if self.weight is not None else None,
            "gender": self.gender,
            "fitness_goal": self.fitness_goal,
            "profile_completed": bool(self.profile_completed),
            "bmi": self.bmi,
        }
