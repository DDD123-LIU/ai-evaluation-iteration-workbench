"""使用启动阶段已配置的SQLite连接，禁止另起默认连接。"""
from alembic import context
from app.models.imports import Base

connection = context.config.attributes["connection"]
context.configure(connection=connection, target_metadata=Base.metadata)
with context.begin_transaction():
    context.run_migrations()
