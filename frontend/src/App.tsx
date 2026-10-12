import { useEffect, useState } from "react";
import {
  ApiError,
  clearPending,
  data,
  fileDigest,
  pending,
  operationIsSending,
  request,
  useLoad,
  write,
} from "./api";
import { ErrorBox, Link, go, useAction } from "./components";
import {
  Batch,
  Batches,
  CaseDetail,
  Effects,
  Exports,
  Materials,
  QAEditor,
  QAIndex,
  Supplements,
} from "./pages";
import type { Overview } from "./types";

function Recovery() {
  const [operation, setOperation] = useState(pending()),
    [notCommitted, setNotCommitted] = useState(false),
    [sending, setSending] = useState(operationIsSending());
  const action = useAction();
  useEffect(() => {
    const update = () => {
      setOperation(pending());
      setSending(operationIsSending());
      setNotCommitted(false);
    };
    window.addEventListener("pending-operation", update);
    return () => window.removeEventListener("pending-operation", update);
  }, []);
  if (!operation || sending) return null;
  return (
    <aside className="recovery">
      <h2>原操作结果待核查</h2>
      <p>操作编号 {operation.operation_id}。请先查询，避免重复保存。</p>
      <button
        disabled={action.busy}
        onClick={() =>
          void action.run(async () => {
            try {
              const result = await data<{
                result_type: string;
                result_id: string;
              }>("/operations/" + operation.operation_id);
              const target: Record<string, string> = {
                task: "/batches/",
                qa: "/qa/",
                export: "/exports/",
                supplement: "/supplements/",
                material: "/materials/",
              };
              if (result.result_type === "task") {
                const task = await data<{ kind: string }>(
                  "/tasks/" + result.result_id,
                );
                target.task =
                  task.kind === "effect" ? "/effects/" : "/batches/";
              }
              clearPending();
              if (target[result.result_type])
                go(target[result.result_type] + result.result_id);
              else location.reload();
            } catch (e) {
              if (e instanceof ApiError && e.status === 404) {
                setNotCommitted(true);
                return;
              }
              throw e;
            }
          })
        }
      >
        查询原操作结果
      </button>
      {notCommitted && (
        <>
          <p>后端确认原操作未提交。</p>
          {operation.body ? (
            <button
              onClick={() =>
                void action.run(async () => {
                  await write(
                    operation.path,
                    operation.body!,
                    operation.method,
                    true,
                  );
                  location.reload();
                })
              }
            >
              使用原操作编号重发
            </button>
          ) : (
            <p>
              原上传文件不保存在浏览器中。请重新选择原文件后，使用下方入口重传。
            </p>
          )}
          {!operation.body && (
            <RetryUpload
              operationId={operation.operation_id}
              original={operation.upload}
            />
          )}
          <button onClick={clearPending}>放弃未提交的原操作</button>
        </>
      )}
      <ErrorBox error={action.error} />
    </aside>
  );
}
function RetryUpload({
  operationId,
  original,
}: {
  operationId: string;
  original?: { kind: string; filename: string; sha256: string };
}) {
  const [file, setFile] = useState<File | null>(null),
    [kind, setKind] = useState(original?.kind || "dialogues");
  const action = useAction();
  return (
    <div>
      <select
        aria-label="原上传类型"
        value={kind}
        disabled={!!original}
        onChange={(e) => setKind(e.target.value)}
      >
        <option value="dialogues">对话</option>
        <option value="rules">规则</option>
        <option value="knowledge">知识库</option>
      </select>
      <input
        aria-label="原上传文件"
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
      />
      <button
        disabled={!file || action.busy}
        onClick={() =>
          void action.run(async () => {
            if (original && (await fileDigest(file!)) !== original.sha256)
              throw new Error("文件内容与原上传不同。请重新选择原文件。");
            const form = new FormData();
            form.append("kind", kind);
            form.append("file", file!, original?.filename || file!.name);
            form.append("operation_id", operationId);
            await request("/uploads", { method: "POST", body: form });
            clearPending();
            location.reload();
          })
        }
      >
        重传原文件
      </button>
      <ErrorBox error={action.error} />
    </div>
  );
}
export default function App() {
  const [route, setRoute] = useState(location.hash.slice(1) || "/batches");
  useEffect(() => {
    const update = () =>
      queueMicrotask(() => setRoute(location.hash.slice(1) || "/batches"));
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  const overview = useLoad(
    () => data<Overview>("/workbench"),
    "overview",
    true,
  );
  const availableOverview =
    overview.value && overview.error
      ? {
          ...overview.value,
          can_start: false,
          start_reason: "任务窗口状态暂不可读，请等待重新查询",
        }
      : overview.value;
  const url = new URL(route, "http://localhost"),
    parts = url.pathname.split("/").filter(Boolean),
    [section, id, child, caseId] = parts;
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          质量工作台<small>AI评测 · 人工确认 · 来源追溯</small>
        </div>
        <nav aria-label="主要导航">
          {[
            ["materials", "资料与版本"],
            ["batches", "评测批次"],
            ["qa", "QA审核与导出"],
            ["supplements", "补充与效果"],
          ].map(([key, title]) => (
            <a
              className={section === key ? "active" : ""}
              href={"#/" + key}
              key={key}
            >
              {title}
            </a>
          ))}
          <Link to="/effects">效果任务历史</Link>
          <Link to="/exports">导出历史快照</Link>
        </nav>
        <p className="sidebar-note">
          单机工作台
          <br />
          模型辅助，业务判断由本人确认
        </p>
      </aside>
      <main>
        <header className="topbar">
          <span>本地工作空间</span>
          <span>
            {overview.error
              ? "模型状态暂不可读"
              : !overview.value
                ? "正在读取模型状态"
                : overview.value.model_ready
                  ? "模型已配置"
                  : "模型未配置 · 可浏览历史"}
          </span>
          {overview.value?.active_task_id && (
            <Link
              to={
                overview.value.tasks.find(
                  (t) => t.id === overview.value!.active_task_id,
                )?.kind === "effect"
                  ? "/effects/" + overview.value.active_task_id
                  : "/batches/" + overview.value.active_task_id
              }
            >
              正在运行的任务
            </Link>
          )}
        </header>
        <ErrorBox error={overview.error} />
        {overview.error && overview.value && (
          <p className="notice">
            以下保留最近一次读取的历史结果。当前任务窗口尚未核实，暂不能启动新任务。
          </p>
        )}
        {overview.value?.runtime_error && (
          <div role="alert" className="error">
            任务执行器状态：{overview.value.runtime_error}
          </div>
        )}
        <Recovery />
        <div className="content">
          {section === "materials" ? (
            <Materials id={id} />
          ) : section === "batches" ? (
            child === "cases" && caseId ? (
              <CaseDetail taskId={id} id={caseId} />
            ) : id ? (
              <Batch
                id={id}
                filter={url.searchParams.get("filter") || "all"}
                overview={availableOverview}
                refresh={overview.reload}
              />
            ) : (
              <Batches overview={availableOverview} refresh={overview.reload} />
            )
          ) : section === "qa" ? (
            id ? (
              <QAEditor key={id} id={id} />
            ) : (
              <QAIndex
                batch={url.searchParams.get("batch") || ""}
                overview={availableOverview}
              />
            )
          ) : section === "exports" ? (
            <Exports id={id} />
          ) : section === "supplements" ? (
            <Supplements
              id={id}
              overview={availableOverview}
              refresh={overview.reload}
            />
          ) : section === "effects" ? (
            <Effects
              id={id}
              overview={availableOverview}
              refresh={overview.reload}
            />
          ) : (
            <>
              <h1>入口不存在</h1>
              <Link to="/batches">返回评测批次</Link>
            </>
          )}
        </div>
        <footer>
          模型评分与业务效果需要分别验证。人工审核和效果判断由本人确认。
        </footer>
      </main>
    </div>
  );
}
