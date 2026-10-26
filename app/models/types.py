from ..extensions import db

# SQLite 只有 INTEGER PRIMARY KEY 才会自动生成主键。
# 在 SQLite 上使用 INTEGER，在其他数据库上仍保持 BIGINT。
BIGINT_PK = db.BigInteger().with_variant(db.Integer, "sqlite")
