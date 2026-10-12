"""旧新效果固定版本及生成原文；仅增表，不创建抽检模块。"""
from alembic import op
import sqlalchemy as sa

revision = '0008_effects'
down_revision = '0007_supplements'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('effect_task',
        sa.Column('task_id', sa.String(36), sa.ForeignKey('task.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('supplement_id', sa.String(36), sa.ForeignKey('supplement.id'), nullable=False),
        sa.Column('source_batch_id', sa.String(36), sa.ForeignKey('task.id'), nullable=False),
        sa.Column('old_kb_id', sa.String(36), sa.ForeignKey('material_version.id'), nullable=False),
        sa.Column('new_kb_id', sa.String(36), sa.ForeignKey('material_version.id'), nullable=False),
        sa.Column('rule_version_id', sa.String(36), sa.ForeignKey('material_version.id'), nullable=False))
    op.create_table('generation_result',
        sa.Column('item_id', sa.String(36), sa.ForeignKey('execution_item.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('reply', sa.Text(), nullable=False))


def downgrade():
    op.drop_table('generation_result')
    op.drop_table('effect_task')
