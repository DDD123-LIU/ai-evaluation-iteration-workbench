export type Dimension = "accuracy" | "intent" | "service";
export type Mark = "改善" | "持平" | "变差" | null;
export interface RecordRow {
  id: string;
  filename: string;
  uploaded_at: string;
  row_count: number;
  kind?: string;
  rows?: { source_id: string; title: string; content: string }[];
  cases?: SourceCase[];
}
export interface SourceCase {
  id: string;
  csv_case_id: string;
  question: string;
  original_reply: string;
  history: Message[];
  chat_history?: string;
}
export interface Message {
  role: string;
  content: string;
}
export interface Scores {
  accuracy: { score: number; reason: string };
  intent: { score: number; reason: string };
  service: { score: number; reason: string };
}
export interface Contract {
  scores: Scores;
  primary_cause: string | null;
  secondary_causes: string[];
  has_material_conflict: boolean;
}
export interface Gap {
  id?: string;
  gap: string;
  snippet: string;
  reason: string;
  location: unknown;
}
export interface Evaluation {
  contract: Contract;
  is_badcase: boolean;
  composite_score: string;
  knowledge_gaps: Gap[];
  attempt_count: number;
  trace: unknown;
}
export interface Metrics {
  display: {
    pass_rate: string | null;
    average_score: string | null;
    error_rate: string | null;
  };
  counts: Record<string, number>;
  batch_passed?: boolean;
  alerts?: {
    kind: string;
    metric_name: string;
    display_value: string | null;
    threshold: string;
    task_id: string;
    problem_case_ids: string[];
    target: { filter: string };
  }[];
  raw?: Record<string, { numerator: number; denominator: number } | null>;
}
export interface Task {
  phase_progress?: {
    stage: string;
    side: string;
    total: number;
    succeeded: number;
    final_failed: number;
    running: number;
    pending: number;
    waiting_for_generation: number;
    upstream_generation_failed: number;
  }[];
  id: string;
  kind: string;
  phase: string;
  state: string;
  revision: number;
  started_at: string;
  automatic_ended_at: string | null;
  elapsed_ms: number | null;
  progress: {
    total: number;
    pending: number;
    running: number;
    succeeded: number;
    final_failed: number;
  };
  items: {
    id: string;
    case_id: string;
    stage: string;
    side: string;
    state: string;
    attempt_count: number;
    error_category: string | null;
    error_detail: string | null;
  }[];
  summary?: { status: string; data: Metrics | null };
  source: Record<string, string> | null;
  capabilities: { can_cancel: boolean };
  human_effect_conclusion: string | null;
}
export interface Overview {
  tasks: Task[];
  active_task_id: string | null;
  can_start: boolean;
  model_ready: boolean;
  start_reason: string;
  runtime_error: string | null;
}
export interface CaseRow {
  task_id: string;
  case_id: string;
  case_number: string;
  question: string;
  evaluation: Evaluation | null;
  original_reply?: string;
  history?: Message[];
  final_error: {
    category: string;
    attempt_count: number;
    detail?: string;
  } | null;
}
export interface CaseSummary extends Omit<CaseRow, "evaluation"> {
  evaluation: {
    scores: Record<Dimension, number>;
    is_badcase: boolean;
    composite_score: string;
    primary_cause: string | null;
  } | null;
}
export interface QASummary {
  id: string;
  task_id: string;
  case_id: string;
  standard_question: string;
  original_question: string;
  review_state: string;
  attempt_count: number;
}
export interface QA extends QASummary {
  answer: string;
  category: string;
  revision: number;
  original_reply: string;
  history: Message[];
  knowledge_gap: Gap;
  trace: {
    rule_version_id: string;
    kb_version_id: string;
    [key: string]: unknown;
  };
}
export interface QAList {
  drafts: QASummary[];
  failures: {
    case_id: string;
    error_category: string;
    error_detail: string;
    attempt_count: number;
  }[];
  pending: { case_id: string; state: string }[];
}
export interface Capabilities {
  source_case_number?: string;
  can_edit: boolean;
  can_approve: boolean;
  can_export: boolean;
  reason: string;
}
export interface ExportItem {
  id: string;
  event_id: string;
  qa_id: string;
  qa_revision: number;
  case_id: string;
  source_batch_id: string;
  question: string;
  answer: string;
  source_case_number: string;
  category: string;
  export?: ExportEvent;
}
export interface ExportEvent {
  id: string;
  created_at: string;
  filename: string;
  download_url: string;
  content_hash: string;
  items?: ExportItem[];
}
export interface Supplement {
  id: string;
  new_kb_id: string;
  source_batch_id: string;
  confirmed_at: string;
  old_kb_id?: string;
  rule_version_id?: string;
  upload_id?: string;
  confirmed?: boolean;
  can_validate?: boolean;
  message?: string;
  snapshots?: ExportItem[];
  cases?: SourceCase[];
  source_case_ids?: string[];
}
export interface Stage {
  state: string;
  attempt_count: number;
  reply?: string;
  contract?: Contract;
  is_badcase?: boolean;
  composite_score?: string;
  knowledge_gaps?: Gap[];
  trace?: unknown;
  error_category?: string;
  error_detail?: string;
}
export interface EffectCase {
  case_id: string;
  case_number: string;
  question: string;
  history: Message[];
  old: { generation: Stage; evaluation: Stage };
  new: { generation: Stage; evaluation: Stage };
  comparison: { comparable: boolean; reasons: string[] };
}
export interface Effect {
  task_id: string;
  state: string;
  source: Record<string, string> | null;
  cases: EffectCase[];
  metrics: { status: string; data: Record<"old" | "new", Metrics> | null };
  human_effect_conclusion: string | null;
}
export interface Draw {
  ordinal: number;
  case_id: string;
  kind: string;
  unusable_reasons: string[];
  mark: (Record<Dimension, Mark> & { revision: number }) | null;
}
export interface Sampling {
  status: string;
  population_size?: number;
  target_size?: number;
  valid_count?: number;
  marking_allowed: boolean;
  draws: Draw[];
  human_effect_conclusion: string | null;
}
