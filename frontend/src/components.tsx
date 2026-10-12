import { useState, type ReactNode } from "react";
import { ApiError, upload } from "./api";
import type { Contract, Gap, Message, Metrics, RecordRow, Task } from "./types";

export const dimensions = {
  accuracy: "信息准确性",
  intent: "意图理解",
  service: "服务质量",
} as const;
const labels: Record<string, string> = {
  running: "运行中",
  completed: "自动阶段完成",
  cancelled: "已取消",
  evaluating: "评测",
  qa_generation: "QA生成",
  effect_automatic: "旧新生成与评测",
  done: "结束",
  pending_review: "待审核",
  approved: "已通过",
  pending_confirmation: "待确认",
  validation_failed: "验证失败",
  not_passed: "不通过",
  passed: "通过",
  automatic_pending: "自动阶段未完成",
  succeeded: "成功",
  final_failed: "最终失败",
  pending: "待处理",
  waiting_for_generation: "等待生成",
  upstream_generation_failed: "上游生成失败",
  CALL_ERROR: "调用失败",
  PARSE_ERROR: "解析异常",
  INCOMPLETE_RESULT: "结果不完整",
};
export const label = (value: string | null | undefined) =>
  value ? labels[value] || value : "尚未取得";
export const go = (path: string) => {
  location.hash = path;
};
export const time = (value: string | null | undefined) =>
  value
    ? new Date(value).toLocaleString("zh-CN", {
        timeZone: "Asia/Shanghai",
        hour12: false,
      }) + " (Asia/Shanghai)"
    : "尚未取得";
export function Link({ to, children }: { to: string; children: ReactNode }) {
  return <a href={"#" + to}>{children}</a>;
}
export function Badge({ value }: { value: string }) {
  return <span className={"badge " + value}>{label(value)}</span>;
}
export function Empty({ children = "暂无数据" }: { children?: ReactNode }) {
  return <div className="empty">{children}</div>;
}
export function ErrorBox({ error }: { error: Error | null }) {
  if (!error) return null;
  return (
    <div role="alert" className="error">
      <strong>{error.message}</strong>
      {error instanceof ApiError && (
        <>
          <p>
            {error.failure.code} ·{" "}
            {error.failure.commit_state === "unknown"
              ? "结果暂不能确认；如有写入，请核查原操作"
              : "未确认成功，请按提示处理"}
          </p>
          {error.failure.field_errors?.map((row, i) => (
            <pre key={i}>{JSON.stringify(row, null, 2)}</pre>
          ))}
        </>
      )}
    </div>
  );
}
export function Json({ title, value }: { title: string; value: unknown }) {
  return (
    <details>
      <summary>{title}</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}
export function History({ messages }: { messages: Message[] | undefined }) {
  return (
    <section>
      <h3>完整聊天上下文</h3>
      {messages?.map((row, i) => (
        <div className="message" key={i}>
          <span>
            {row.role === "user"
              ? "用户"
              : row.role === "assistant"
                ? "AI"
                : row.role}
          </span>
          <p className="full">{row.content}</p>
        </div>
      ))}
    </section>
  );
}
export function Scores({
  contract,
  composite,
  badcase,
  gaps,
}: {
  contract: Contract;
  composite?: string;
  badcase?: boolean;
  gaps?: Gap[];
}) {
  return (
    <section>
      <div className="score-grid">
        {Object.entries(dimensions).map(([key, title]) => {
          const score = contract.scores[key as keyof typeof dimensions];
          return (
            <article key={key}>
              <p>{title}</p>
              <strong>
                {score.score} <small>/ 5</small>
              </strong>
              <p className="full">{score.reason}</p>
            </article>
          );
        })}
      </div>
      <p>
        综合分：{composite ?? "尚未取得"}　回复合格状态：
        {badcase ? "Badcase" : "合格"}
      </p>
      <p>主因：{contract.primary_cause ?? "不适用"}</p>
      <p>次因：{contract.secondary_causes.join("、") || "无"}</p>
      <p>资料冲突：{contract.has_material_conflict ? "是" : "否"}</p>
      {gaps?.map((gap, i) => (
        <article className="gap" key={gap.id || i}>
          <h4>{gap.gap}</h4>
          <p className="full">来源片段：{gap.snippet}</p>
          <p className="full">reason：{gap.reason}</p>
          <Json title="片段定位" value={gap.location} />
        </article>
      ))}
    </section>
  );
}
export function MetricsView({
  metrics,
  status = "available",
}: {
  metrics: Metrics | null | undefined;
  status?: string;
}) {
  return (
    <div className="metrics">
      {(["pass_rate", "average_score", "error_rate"] as const).map((key, i) => (
        <article key={key}>
          <p>{["通过率", "平均分", "异常率"][i]}</p>
          <strong>
            {status === "cancelled"
              ? "已作废"
              : !metrics
                ? "统计待完成"
                : (metrics.display[key] ?? "无数据")}
          </strong>
          {metrics && <small>数据来自后台持久结果</small>}
          {metrics?.raw?.[key] && (
            <small>
              分子 {metrics.raw[key]!.numerator} / 分母{" "}
              {metrics.raw[key]!.denominator}
            </small>
          )}
        </article>
      ))}
    </div>
  );
}
export function Progress({ task }: { task: Task }) {
  return (
    <section className="progress">
      <div>
        <Badge value={task.state} /> <span>{label(task.phase)}</span>
        <span>
          {" "}
          调用单元：已成功 {task.progress.succeeded} · 最终失败{" "}
          {task.progress.final_failed} · 处理中 {task.progress.running} · 待处理{" "}
          {task.progress.pending}
        </span>
      </div>
      {task.phase_progress?.map((row) => (
        <p key={row.stage + row.side}>
          {row.side === "old" ? "旧侧 " : row.side === "new" ? "新侧 " : ""}
          {row.stage === "evaluation"
            ? "评测"
            : row.stage === "standard_question"
              ? "QA生成"
              : "回复生成"}
          ：应处理 {row.total} · 成功 {row.succeeded} · 最终失败{" "}
          {row.final_failed} · 处理中 {row.running} · 待处理 {row.pending}
          {row.waiting_for_generation > 0 &&
            ` · 等待生成 ${row.waiting_for_generation}`}
          {row.upstream_generation_failed > 0 &&
            ` · 上游生成失败 ${row.upstream_generation_failed}`}
        </p>
      ))}
      <p>
        自动阶段实际耗时：
        {task.elapsed_ms === null
          ? "尚未结束"
          : `${(task.elapsed_ms / 1000).toFixed(2)} 秒`}{" "}
        <small>耗时为实际记录，性能标准尚未验证</small>
      </p>
      <Json title="各阶段实际次数与状态" value={task.items} />
    </section>
  );
}
export function Upload({
  kind,
  onSaved,
}: {
  kind: string;
  onSaved: (value: RecordRow) => void;
}) {
  const [file, setFile] = useState<File | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState<Error | null>(null);
  const names: Record<string, string> = {
    dialogues: "对话",
    rules: "规则",
    knowledge: "知识库",
  };
  return (
    <section className="upload">
      <h3>上传{names[kind]} CSV</h3>
      <p>
        中文固定表头与顺序。UTF-8 可带
        BOM。引号包裹多行文本。对话每批最多100条。
      </p>
      <a href={"/api/v1/templates/" + kind} download={`${kind}-template.csv`}>
        下载{names[kind]}模板
      </a>
      <label>
        {names[kind]}文件
        <input
          type="file"
          accept=".csv"
          aria-label={names[kind] + "文件"}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      <button
        disabled={!file || busy}
        onClick={async () => {
          setBusy(true);
          setError(null);
          try {
            const row = await upload<RecordRow>(kind, file!);
            onSaved(row);
          } catch (e) {
            setError(e as Error);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "校验及保存中…" : "导入" + names[kind]}
      </button>
      <ErrorBox error={error} />
    </section>
  );
}
export function SectionTitle({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-title">
      <div>
        <span>{eyebrow}</span>
        <h1>{title}</h1>
      </div>
      {children}
    </header>
  );
}
export function useAction() {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<Error | null>(null);
  return {
    busy,
    error,
    run: async (action: () => Promise<void>) => {
      setBusy(true);
      setError(null);
      try {
        await action();
      } catch (e) {
        setError(e as Error);
      } finally {
        setBusy(false);
      }
    },
  };
}
