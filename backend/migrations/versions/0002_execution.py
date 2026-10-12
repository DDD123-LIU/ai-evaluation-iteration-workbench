"""009执行结构的固定SQLite迁移快照；不导入可变应用模型。"""
from alembic import op

revision = '0002_execution'
down_revision = '0001_imports'
branch_labels = None
depends_on = None

DDL = (
    """CREATE TABLE task (
	id VARCHAR(36) NOT NULL,
	kind VARCHAR(16) NOT NULL,
	phase VARCHAR(24) NOT NULL,
	state VARCHAR(16) NOT NULL,
	revision INTEGER NOT NULL,
	cancel_epoch INTEGER NOT NULL,
	started_at VARCHAR(40) NOT NULL,
	automatic_ended_at VARCHAR(40),
	elapsed_ms INTEGER,
	PRIMARY KEY (id),
	CHECK (kind IN ('ordinary','effect')),
	CHECK (state IN ('running','completed','cancelled')),
	CHECK (phase IN ('evaluating','qa_generation','effect_automatic','done')),
	CHECK (revision >= 0 AND cancel_epoch >= 0)
)""",
    """CREATE UNIQUE INDEX one_running_task ON task (state) WHERE state='running'""",
    """CREATE TABLE runtime_slot (
	id INTEGER NOT NULL,
	task_id VARCHAR(36),
	PRIMARY KEY (id),
	CHECK (id=1),
	UNIQUE (task_id),
	FOREIGN KEY(task_id) REFERENCES task (id)
)""",
    """CREATE TABLE task_case (
	task_id VARCHAR(36) NOT NULL,
	case_id VARCHAR(36) NOT NULL,
	ordinal INTEGER NOT NULL,
	PRIMARY KEY (task_id, case_id),
	UNIQUE (task_id, ordinal),
	CHECK (ordinal >= 1),
	FOREIGN KEY(task_id) REFERENCES task (id) ON DELETE CASCADE,
	FOREIGN KEY(case_id) REFERENCES case_record (id)
)""",
    """CREATE TABLE ordinary_task (
	task_id VARCHAR(36) NOT NULL,
	upload_id VARCHAR(36) NOT NULL,
	rule_version_id VARCHAR(36) NOT NULL,
	kb_version_id VARCHAR(36) NOT NULL,
	PRIMARY KEY (task_id),
	FOREIGN KEY(task_id) REFERENCES task (id) ON DELETE CASCADE,
	FOREIGN KEY(upload_id) REFERENCES dialogue_upload (id),
	FOREIGN KEY(rule_version_id) REFERENCES material_version (id),
	FOREIGN KEY(kb_version_id) REFERENCES material_version (id)
)""",
    """CREATE TABLE config_snapshot (
	id VARCHAR(36) NOT NULL,
	task_id VARCHAR(36) NOT NULL,
	stage VARCHAR(24) NOT NULL,
	contract_version TEXT NOT NULL,
	prompt_version TEXT NOT NULL,
	full_prompt TEXT NOT NULL,
	request_model TEXT NOT NULL,
	documented_release TEXT NOT NULL,
	parameters_json TEXT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (task_id, stage),
	FOREIGN KEY(task_id) REFERENCES task (id) ON DELETE CASCADE
)""",
    """CREATE TABLE execution_item (
	id VARCHAR(36) NOT NULL,
	task_id VARCHAR(36) NOT NULL,
	case_id VARCHAR(36) NOT NULL,
	stage VARCHAR(24) NOT NULL,
	side VARCHAR(8) NOT NULL,
	gap_key TEXT NOT NULL,
	state VARCHAR(16) NOT NULL,
	attempt_count INTEGER NOT NULL,
	result_id VARCHAR(36),
	request_json TEXT NOT NULL,
	next_attempt_at VARCHAR(40),
	error_category VARCHAR(16),
	error_detail TEXT,
	PRIMARY KEY (id),
	UNIQUE (task_id, case_id, stage, side, gap_key),
	CHECK (attempt_count BETWEEN 0 AND 3),
	CHECK (stage IN ('evaluation','standard_question','reply_generation')),
	CHECK (side IN ('original','old','new')),
	CHECK (state IN ('pending','running','succeeded','final_failed')),
	FOREIGN KEY(task_id) REFERENCES task (id) ON DELETE CASCADE,
	FOREIGN KEY(case_id) REFERENCES case_record (id)
)""",
    """CREATE TABLE attempt (
	id VARCHAR(36) NOT NULL,
	item_id VARCHAR(36) NOT NULL,
	ordinal INTEGER NOT NULL,
	state VARCHAR(16) NOT NULL,
	request_json TEXT NOT NULL,
	config_id VARCHAR(36) NOT NULL,
	started_at VARCHAR(40) NOT NULL,
	ended_at VARCHAR(40),
	response_envelope_json TEXT,
	raw_content TEXT,
	error_category VARCHAR(16),
	error_detail TEXT,
	PRIMARY KEY (id),
	UNIQUE (item_id, ordinal),
	CHECK (ordinal BETWEEN 1 AND 3),
	FOREIGN KEY(item_id) REFERENCES execution_item (id) ON DELETE CASCADE,
	FOREIGN KEY(config_id) REFERENCES config_snapshot (id)
)""",
)

def upgrade():
    for statement in DDL:
        op.execute(statement)
    op.execute("INSERT INTO runtime_slot(id,task_id) VALUES (1,NULL)")

def downgrade():
    for name in ('attempt', 'execution_item', 'config_snapshot', 'ordinary_task', 'task_case', 'runtime_slot', 'task'):
        op.drop_table(name)
