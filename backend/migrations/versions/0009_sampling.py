"""E14增量迁移；既有G/E、快照与资料保持。"""
from alembic import op
import sqlalchemy as sa

revision = '0009_sampling'
down_revision = '0008_effects'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sampling_run',
        sa.Column('effect_task_id', sa.String, sa.ForeignKey('effect_task.task_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('population_size', sa.Integer, nullable=False), sa.Column('target_size', sa.Integer, nullable=False),
        sa.Column('population_json', sa.Text, nullable=False), sa.Column('status', sa.String, nullable=False),
        sa.Column('created_at', sa.String, nullable=False))
    op.create_table('draw',
        sa.Column('effect_task_id', sa.String, sa.ForeignKey('sampling_run.effect_task_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('draw_ordinal', sa.Integer, primary_key=True),
        sa.Column('case_id', sa.String, sa.ForeignKey('case_record.id'), nullable=False),
        sa.Column('kind', sa.String, nullable=False), sa.Column('unusable_reason', sa.Text, nullable=False),
        sa.UniqueConstraint('effect_task_id', 'case_id'))
    op.create_table('human_mark',
        sa.Column('effect_task_id', sa.String, sa.ForeignKey('sampling_run.effect_task_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('case_id', sa.String, sa.ForeignKey('case_record.id'), primary_key=True),
        sa.Column('accuracy', sa.String), sa.Column('intent', sa.String), sa.Column('service', sa.String),
        sa.Column('revision', sa.Integer, nullable=False),
        *(sa.CheckConstraint(f"{key} IS NULL OR {key} IN ('改善','持平','变差')") for key in ('accuracy', 'intent', 'service')))
    op.create_table('sampling_receipt',
        sa.Column('operation_id', sa.String, sa.ForeignKey('operation_commit.operation_id'), primary_key=True),
        sa.Column('result_json', sa.Text, nullable=False))


def downgrade():
    for name in ('sampling_receipt', 'human_mark', 'draw', 'sampling_run'):
        op.drop_table(name)
