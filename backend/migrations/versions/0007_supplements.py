"""补充确认与具体历史快照关联；仅增表，保留旧资料与导出字节。"""
from alembic import op
import sqlalchemy as sa

revision = '0007_supplements'
down_revision = '0006_qa_exports'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('supplement', sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('new_kb_id', sa.String(36), sa.ForeignKey('material_version.id'), nullable=False),
        sa.Column('source_batch_id', sa.String(36), sa.ForeignKey('ordinary_task.task_id'), nullable=False),
        sa.Column('confirmed_at', sa.String(40), nullable=False))
    op.create_table('supplement_item',
        sa.Column('supplement_id', sa.String(36), sa.ForeignKey('supplement.id'), primary_key=True),
        sa.Column('export_item_id', sa.String(36), sa.ForeignKey('export_item.id'), primary_key=True))


def downgrade():
    op.drop_table('supplement_item')
    op.drop_table('supplement')
