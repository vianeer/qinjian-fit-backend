from datetime import datetime

from ..extensions import db
from .types import BIGINT_PK


class KnowledgeCategory(db.Model):
    __tablename__ = "knowledge_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(20), nullable=False, default="📚")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    articles = db.relationship("KnowledgeArticle", backref="category", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "article_count": KnowledgeArticle.query.filter_by(
                category_id=self.id, is_published=True
            ).count(),
        }


class KnowledgeArticle(db.Model):
    __tablename__ = "knowledge_articles"

    id = db.Column(BIGINT_PK, primary_key=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("knowledge_categories.id"), nullable=False
    )
    title = db.Column(db.String(150), nullable=False)
    summary = db.Column(db.String(300), nullable=False, default="")
    content = db.Column(db.Text, nullable=False)
    cover_url = db.Column(db.String(500), nullable=False, default="")
    source = db.Column(db.String(80), nullable=False, default="校园健身房")
    view_count = db.Column(db.Integer, nullable=False, default=0)
    is_published = db.Column(db.Boolean, nullable=False, default=True)
    published_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self, include_content=False):
        data = {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "",
            "title": self.title,
            "summary": self.summary,
            "cover_url": self.cover_url,
            "source": self.source,
            "view_count": self.view_count,
            "published_at": self.published_at.isoformat(),
        }
        if include_content:
            data["content"] = self.content
        return data


class KnowledgeTip(db.Model):
    __tablename__ = "knowledge_tips"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "content": self.content}

