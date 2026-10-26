import random

from flask import Blueprint, request

from ..extensions import db
from ..models import KnowledgeArticle, KnowledgeCategory, KnowledgeTip
from ..utils import fail, ok

knowledge_bp = Blueprint("knowledge_api", __name__)


@knowledge_bp.get("/categories")
def categories():
    items = KnowledgeCategory.query.order_by(
        KnowledgeCategory.sort_order.asc(), KnowledgeCategory.id.asc()
    ).all()
    return ok([item.to_dict() for item in items])


@knowledge_bp.get("/articles")
def articles():
    category_id = request.args.get("category_id", type=int)
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 10, type=int), 1), 50)

    query = KnowledgeArticle.query.filter_by(is_published=True)
    if category_id:
        query = query.filter_by(category_id=category_id)

    pagination = query.order_by(KnowledgeArticle.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return ok(
        {
            "items": [item.to_dict() for item in pagination.items],
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@knowledge_bp.get("/articles/<int:article_id>")
def article_detail(article_id):
    article = KnowledgeArticle.query.filter_by(
        id=article_id, is_published=True
    ).first()
    if not article:
        return fail("知识文章不存在", 404)

    article.view_count += 1
    db.session.commit()
    return ok(article.to_dict(include_content=True))


@knowledge_bp.get("/tips")
def tips():
    limit = min(max(request.args.get("limit", 10, type=int), 1), 50)
    # 在 Python 层随机打乱，避免依赖特定数据库的随机排序函数。
    items = KnowledgeTip.query.filter_by(is_enabled=True).all()
    random.shuffle(items)
    items = items[:limit]
    return ok([item.to_dict() for item in items])


