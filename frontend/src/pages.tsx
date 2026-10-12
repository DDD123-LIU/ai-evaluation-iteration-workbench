import { useEffect, useState } from "react";
import { allItems, data, useLoad, write } from "./api";
import {
  Badge,
  Empty,
  ErrorBox,
  History,
  Json,
  Link,
  MetricsView,
  Progress,
  Scores,
  SectionTitle,
  Upload,
  dimensions,
  go,
  label,
  time,
  useAction,
} from "./components";
import type {
  Capabilities,
  CaseRow,
  CaseSummary,
  Dimension,
  Draw,
  Effect,
  ExportEvent,
  ExportItem,
  Mark,
  Overview,
  QA,
  QAList,
  RecordRow,
  Sampling,
  Supplement,
  Task,
} from "./types";

function Loading({ loading }: { loading: boolean }) {
  return loading ? <p role="status">正在读取持久记录…</p> : null;
}
function VersionSelect({
  title,
  rows,
  value,
  onChange,
}: {
  title: string;
  rows: RecordRow[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label>
      {title}
      <select
        aria-label={title}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">请选择历史版本</option>
        {rows.map((r) => (
          <option key={r.id} value={r.id}>
            {r.filename} · {time(r.uploaded_at)} · {r.row_count}条 ·{" "}
            {r.id.slice(0, 8)}
          </option>
        ))}
      </select>
    </label>
  );
}
function MaterialsData() {
  return Promise.all([
    allItems<RecordRow>("/materials?kind=rules"),
    allItems<RecordRow>("/materials?kind=knowledge"),
    allItems<RecordRow>("/uploads"),
  ]);
}
export function Materials({ id }: { id?: string }) {
  const rows = useLoad(MaterialsData, "materials"),
    detail = useLoad(
      () => (id ? data<RecordRow>("/materials/" + id) : Promise.resolve(null)),
      "material:" + id,
    );
  return (
    <>
      <SectionTitle eyebrow="历史原文与来源" title="资料与版本" />
      <p>导入失败不建立新版本。历史版本保留。上传知识库不等于确认实际补充。</p>
      <div className="columns">
        {["rules", "knowledge"].map((kind) => (
          <Upload
            key={kind}
            kind={kind}
            onSaved={(r) => {
              rows.reload();
              go("/materials/" + r.id);
            }}
          />
        ))}
      </div>
      <ErrorBox error={rows.error} />
      <Loading loading={rows.loading} />
      {rows.value &&
        rows.value.slice(0, 2).map((list, i) => (
          <section key={i}>
            <h2>{i === 0 ? "规则历史版本" : "知识库历史版本"}</h2>
            {!list.length ? (
              <Empty />
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>文件</th>
                      <th>时间</th>
                      <th>条数</th>
                      <th>版本</th>
                    </tr>
                  </thead>
                  <tbody>
                    {list.map((r) => (
                      <tr key={r.id}>
                        <td>
                          <Link to={"/materials/" + r.id}>{r.filename}</Link>
                        </td>
                        <td>{time(r.uploaded_at)}</td>
                        <td>{r.row_count}</td>
                        <td className="mono">{r.id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        ))}
      {id && (
        <section>
          <h2>完整资料内容</h2>
          <ErrorBox error={detail.error} />
          <Loading loading={detail.loading} />
          {detail.value && (
            <>
              <a href={"/api/v1/materials/" + id + "/file"} download>
                下载原文件
              </a>
              <Json title="版本原始记录" value={detail.value} />
              {detail.value.rows?.map((r, i) => (
                <article key={i}>
                  <h3>
                    {r.source_id} · {r.title}
                  </h3>
                  <p className="full">{r.content}</p>
                </article>
              ))}
            </>
          )}
        </section>
      )}
    </>
  );
}
export function Batches({
  overview,
  refresh,
}: {
  overview: Overview | null;
  refresh: () => void;
}) {
  const resources = useLoad(MaterialsData, "batch-resources");
  const [uploadId, setUpload] = useState(""),
    [rule, setRule] = useState(""),
    [kb, setKB] = useState("");
  const action = useAction();
  return (
    <>
      <SectionTitle eyebrow="质量检查" title="评测批次" />
      <details className="panel" open>
        <summary>上传对话并发起评测</summary>
        <Upload
          kind="dialogues"
          onSaved={(r) => {
            resources.reload();
            setUpload(r.id);
          }}
        />
        <ErrorBox error={resources.error} />
        {resources.value && (
          <div className="form-grid">
            <VersionSelect
              title="对话上传记录"
              rows={resources.value[2]}
              value={uploadId}
              onChange={setUpload}
            />
            <VersionSelect
              title="原规则版本"
              rows={resources.value[0]}
              value={rule}
              onChange={setRule}
            />
            <VersionSelect
              title="知识库版本"
              rows={resources.value[1]}
              value={kb}
              onChange={setKB}
            />
          </div>
        )}
        <p>{overview?.start_reason || "读取任务窗口状态中…"}</p>
        <button
          disabled={
            !overview?.can_start || !uploadId || !rule || !kb || action.busy
          }
          onClick={() =>
            void action.run(async () => {
              const t = await write<Task>("/evaluation-tasks", {
                upload_id: uploadId,
                rule_version_id: rule,
                kb_version_id: kb,
              });
              refresh();
              go("/batches/" + t.id);
            })
          }
        >
          开始评测
        </button>
        <ErrorBox error={action.error} />
      </details>
      <h2>批次历史</h2>
      {overview &&
        !overview.tasks.filter((t) => t.kind === "ordinary").length && (
          <Empty>暂无评测批次。先导入三类CSV。</Empty>
        )}
      {overview?.tasks
        .filter((t) => t.kind === "ordinary")
        .map((t) => (
          <article className="task-card" key={t.id}>
            <div className="row">
              <Link to={"/batches/" + t.id}>批次 {t.id.slice(0, 8)}</Link>
              <Badge value={t.state} />
              <span>{time(t.started_at)}</span>
            </div>
            <MetricsView status={t.summary?.status} metrics={t.summary?.data} />
            <Progress task={t} />
            {t.summary?.data && (
              <p>批次结论：{t.summary.data.batch_passed ? "通过" : "不通过"}</p>
            )}
            <Alerts task={t} />
          </article>
        ))}
    </>
  );
}
function Alerts({ task }: { task: Task }) {
  return (
    <div className="row">
      {task.summary?.data?.alerts?.map((a) => (
        <Link
          key={a.kind}
          to={"/batches/" + task.id + "?filter=" + a.target.filter}
        >
          {a.kind === "quality" ? "质量预警 → Badcase" : "异常预警 → 最终异常"}
          （{a.problem_case_ids.length}）
          <small>
            {" "}
            · {a.metric_name}实际 {a.display_value ?? "无数据"} · 阈值{" "}
            {a.threshold}（按未舍入值判断）
          </small>
        </Link>
      ))}
    </div>
  );
}
export function Batch({
  id,
  filter,
  overview,
  refresh,
}: {
  id: string;
  filter: string;
  overview: Overview | null;
  refresh: () => void;
}) {
  const t = overview?.tasks.find((t) => t.id === id);
  const cases = useLoad(
      () => data<CaseSummary[]>("/tasks/" + id + "/cases?filter=" + filter),
      id + ":" + filter,
      true,
    ),
    qa = useLoad(() => data<QAList>("/tasks/" + id + "/qa"), id + ":qa", true);
  const action = useAction();
  return (
    <>
      <SectionTitle
        eyebrow="批次结果与实际进度"
        title={"批次 " + id.slice(0, 8)}
      />
      {t && (
        <>
          <Progress task={t} />
          <MetricsView metrics={t.summary?.data} status={t.summary?.status} />
          {t.summary?.data && (
            <p>批次结论：{t.summary.data.batch_passed ? "通过" : "不通过"}</p>
          )}
          <Alerts task={t} />
          <div className="row">
            <Link to={"/qa?batch=" + id}>QA草稿、补答与审核</Link>
            <button
              disabled={!t.capabilities.can_cancel || action.busy}
              onClick={() => {
                if (
                  window.confirm(
                    "取消将整批作废。停止新调用和重试，迟到回复丢弃。确认取消？",
                  )
                )
                  void action.run(async () => {
                    await write("/tasks/" + id + "/cancel", {
                      expected_revision: t.revision,
                    });
                    refresh();
                    cases.reload();
                  });
              }}
            >
              取消整批
            </button>
            {t.phase === "qa_generation" && (
              <small>QA全部成功或最终失败前不可取消，也不释放任务窗口。</small>
            )}
          </div>
          <Json title="批次资料版本" value={t.source} />
        </>
      )}
      <ErrorBox error={action.error} />
      <nav className="tabs">
        {[
          ["all", "全部case"],
          ["badcase", "Badcase"],
          ["errors", "最终异常"],
        ].map(([v, n]) => (
          <Link key={v} to={"/batches/" + id + "?filter=" + v}>
            {n}
          </Link>
        ))}
      </nav>
      <ErrorBox error={cases.error} />
      <Loading loading={cases.loading} />
      {cases.value && !cases.value.length && <Empty>当前集合无数据</Empty>}
      {cases.value && !!cases.value.length && (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>案例</th>
                <th>问题摘要</th>
                <th>回复合格状态</th>
                <th>三维分数</th>
                <th>主因／异常</th>
              </tr>
            </thead>
            <tbody>
              {cases.value.map((c) => (
                <tr key={c.case_id}>
                  <td>
                    <Link to={"/batches/" + id + "/cases/" + c.case_id}>
                      {c.case_number}
                    </Link>
                  </td>
                  <td className="summary-text">{c.question}</td>
                  <td>
                    {c.evaluation
                      ? c.evaluation.is_badcase
                        ? "Badcase"
                        : "合格"
                      : c.final_error
                        ? "最终异常"
                        : t?.state === "cancelled"
                          ? "已作废"
                          : "待结果"}
                  </td>
                  <td>
                    {c.evaluation
                      ? Object.values(c.evaluation.scores).join(" / ")
                      : "—"}
                  </td>
                  <td>
                    {c.evaluation?.primary_cause ||
                      c.final_error?.category ||
                      "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <h2>QA生成异常</h2>
      <ErrorBox error={qa.error} />
      {qa.value?.failures.length ? (
        qa.value.failures.map((f, i) => (
          <article key={i}>
            <Link to={"/batches/" + id + "/cases/" + f.case_id}>来源case</Link>
            <p>
              {f.error_category} · 实际调用 {f.attempt_count} 次
            </p>
            <p className="full">{f.error_detail}</p>
            <p>生成失败不可审核，不影响成功评测结果。</p>
          </article>
        ))
      ) : (
        <Empty>没有已记录的QA生成失败</Empty>
      )}
    </>
  );
}
export function CaseDetail({ taskId, id }: { taskId: string; id: string }) {
  const result = useLoad(
    () => data<CaseRow>("/tasks/" + taskId + "/cases/" + id),
    taskId + id,
    true,
  );
  const c = result.value;
  return (
    <>
      <SectionTitle
        eyebrow="完整评测依据"
        title={"案例 " + (c?.case_number || "详情")}
      />
      <Link to={"/batches/" + taskId}>返回原批次</Link>
      <Loading loading={result.loading} />
      <ErrorBox error={result.error} />
      {c && (
        <>
          <h2>完整用户问题</h2>
          <p className="full">{c.question}</p>
          <h2>完整待评回复</h2>
          <p className="full">{c.original_reply}</p>
          <History messages={c.history} />
          {c.evaluation ? (
            <>
              <Scores
                contract={c.evaluation.contract}
                composite={c.evaluation.composite_score}
                badcase={c.evaluation.is_badcase}
                gaps={c.evaluation.knowledge_gaps}
              />
              <p>实际评测调用 {c.evaluation.attempt_count} 次</p>
              <Json
                title="完整模型、Prompt、资料与响应追溯"
                value={c.evaluation.trace}
              />
            </>
          ) : (
            <Empty>
              {c.final_error
                ? "技术最终异常，不作为Badcase"
                : "尚无有效评分。取消结果不参与指标。"}
            </Empty>
          )}
          {c.final_error && (
            <Json title="最终异常与实际次数" value={c.final_error} />
          )}
        </>
      )}
    </>
  );
}
export function QAIndex({
  batch,
  overview,
}: {
  batch: string;
  overview: Overview | null;
}) {
  const [selected, setSelected] = useState<Record<string, number>>({});
  const rows = useLoad(
    async () => {
      if (!batch) return null;
      const q = await data<QAList>("/tasks/" + batch + "/qa");
      return {
        ...q,
        details: await Promise.all(
          q.drafts.map(async (row) => ({
            qa: await data<QA>("/qa/" + row.id),
            cap: await data<Capabilities>(
              "/workbench/qa/" + row.id + "/capabilities",
            ),
          })),
        ),
      };
    },
    "qa-list:" + batch,
    true,
  );
  const action = useAction();
  useEffect(() => setSelected({}), [batch]);
  return (
    <>
      <SectionTitle eyebrow="人工确认" title="QA审核与导出" />
      <p className="notice">
        模型仅辅助生成标准问。答案由本人填写和确认。模型结果不能替代审核。
      </p>
      <label>
        来源批次
        <select
          aria-label="QA来源批次"
          value={batch}
          onChange={(e) => go("/qa?batch=" + e.target.value)}
        >
          <option value="">请选择批次</option>
          {overview?.tasks
            .filter((t) => t.kind === "ordinary")
            .map((t) => (
              <option key={t.id} value={t.id}>
                {t.id.slice(0, 8)} · {time(t.started_at)}
              </option>
            ))}
        </select>
      </label>
      <Link to="/exports">查看不可变导出历史</Link>
      <Loading loading={rows.loading} />
      <ErrorBox error={rows.error} />
      {!batch && <Empty>请选择普通评测批次</Empty>}
      {rows.value && !rows.value.details.length && (
        <Empty>没有可审核草稿</Empty>
      )}
      {rows.value?.details.map(({ qa, cap }) => (
        <article className="row" key={qa.id}>
          <input
            type="checkbox"
            aria-label={"选择QA " + qa.id}
            checked={!!selected[qa.id]}
            disabled={!cap.can_export || action.busy}
            onChange={(e) =>
              setSelected((prev) => {
                const next = { ...prev };
                if (e.target.checked) next[qa.id] = qa.revision;
                else delete next[qa.id];
                return next;
              })
            }
          />
          <div>
            <Link to={"/qa/" + qa.id}>{qa.standard_question}</Link>
            <p className="summary-text">原问题：{qa.original_question}</p>
          </div>
          <Badge value={qa.review_state} />
          <span>{qa.answer ? "已补答" : "答案为空"}</span>
        </article>
      ))}
      <button
        disabled={!Object.keys(selected).length || action.busy}
        onClick={() =>
          void action.run(async () => {
            const record = await write<ExportEvent>("/exports", {
              selected_qa_ids: Object.keys(selected),
              expected_qa_revisions: selected,
            });
            setSelected({});
            go("/exports/" + record.id);
          })
        }
      >
        导出选中已通过QA（{Object.keys(selected).length}）
      </button>
      <ErrorBox error={action.error} />
      {rows.value?.failures.map((f, i) => (
        <article className="error" key={i}>
          QA生成失败：{f.case_id} · {f.error_category} · {f.attempt_count}次{" "}
          <p>{f.error_detail}</p>
        </article>
      ))}
    </>
  );
}
export function QAEditor({ id }: { id: string }) {
  const resource = useLoad(
    async () => ({
      qa: await data<QA>("/qa/" + id),
      cap: await data<Capabilities>("/workbench/qa/" + id + "/capabilities"),
    }),
    "qa:" + id,
  );
  const [question, setQuestion] = useState(""),
    [answer, setAnswer] = useState(""),
    [confirmed, setConfirmed] = useState(false);
  const action = useAction();
  const qa = resource.value?.qa,
    dirty = !!qa && (question !== qa.standard_question || answer !== qa.answer);
  useEffect(() => {
    if (qa) {
      setQuestion(qa.standard_question);
      setAnswer(qa.answer);
      setConfirmed(false);
    }
  }, [qa]);
  useEffect(() => {
    if (!dirty) return;
    const originalHash = location.hash;
    let leaving = false;
    const guard = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    const click = (e: MouseEvent) => {
      if ((e.target as Element).closest("a")) {
        if (!window.confirm("尚有未保存修改。放弃修改并离开？")) {
          e.preventDefault();
          e.stopPropagation();
        } else leaving = true;
      }
    };
    const hash = () => {
      if (
        location.hash !== originalHash &&
        !leaving &&
        !window.confirm("尚有未保存修改。放弃修改并离开？")
      )
        history.replaceState(null, "", originalHash);
    };
    window.addEventListener("beforeunload", guard);
    window.addEventListener("hashchange", hash);
    document.addEventListener("click", click, true);
    return () => {
      window.removeEventListener("beforeunload", guard);
      window.removeEventListener("hashchange", hash);
      document.removeEventListener("click", click, true);
    };
  }, [dirty]);
  return (
    <>
      <SectionTitle eyebrow="标准问与参考答案" title="人工补答与审核" />
      <ErrorBox error={resource.error} />
      <Loading loading={resource.loading} />
      {qa && (
        <>
          <Badge value={qa.review_state} />
          <Link to={"/qa?batch=" + qa.task_id}>返回来源批次QA</Link>
          <p className="notice">
            标准问和reason由模型辅助生成。请本人核对来源、填写答案并明确审核。
          </p>
          <label>
            标准问
            <textarea
              aria-label="标准问"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </label>
          <label>
            参考答案
            <textarea
              aria-label="参考答案"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
            />
          </label>
          <p>问题分类：{qa.category}</p>
          <p>
            来源案例：
            <Link to={"/batches/" + qa.task_id + "/cases/" + qa.case_id}>
              {resource.value?.cap.source_case_number ?? qa.case_id}
            </Link>
          </p>
          <div className="row">
            <button
              disabled={action.busy}
              onClick={() =>
                void action.run(async () => {
                  await write(
                    "/qa/" + id,
                    { expected_revision: qa.revision, question, answer },
                    "PATCH",
                  );
                  resource.reload();
                })
              }
            >
              保存内容
            </button>
            <button
              disabled={!dirty || action.busy}
              onClick={() => {
                setQuestion(qa.standard_question);
                setAnswer(qa.answer);
              }}
            >
              取消编辑
            </button>
            <label>
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              本人已核对四项内容，确认通过
            </label>
            <button
              disabled={
                dirty ||
                !confirmed ||
                !resource.value?.cap.can_approve ||
                action.busy
              }
              onClick={() =>
                void action.run(async () => {
                  await write("/qa/" + id + "/approve", {
                    expected_revision: qa.revision,
                    confirm: true,
                  });
                  resource.reload();
                })
              }
            >
              确认审核通过
            </button>
          </div>
          <p>
            {dirty
              ? "修改须先保存；实际修改保存后回到待审核。"
              : resource.value?.cap.reason}
          </p>
          <ErrorBox error={action.error} />
          <h2>原问题与完整回复</h2>
          <p className="full">{qa.original_question}</p>
          <p className="full">{qa.original_reply}</p>
          <History messages={qa.history} />
          <h2>原样复用的缺失证据</h2>
          <p className="full">{qa.knowledge_gap.snippet}</p>
          <p className="full">reason：{qa.knowledge_gap.reason}</p>
          <Json title="缺失点与定位" value={qa.knowledge_gap} />
          <Json title="资料、Prompt与模型追溯" value={qa.trace} />
        </>
      )}
    </>
  );
}
function Snapshot({ item }: { item: ExportItem }) {
  return (
    <article className="snapshot">
      <h3>{item.question}</h3>
      <p className="full">参考答案：{item.answer}</p>
      <p>
        来源案例编号：{item.source_case_number} · 问题分类：{item.category}
      </p>
      <p>
        快照 {item.id} · QA版本 {item.qa_revision}
      </p>
      <Link to={"/qa/" + item.qa_id}>查看当前QA（历史内容不随编辑改变）</Link>
      <Json title="快照完整来源" value={item} />
    </article>
  );
}
export function Exports({ id }: { id?: string }) {
  const list = useLoad(() => allItems<ExportEvent>("/exports"), "exports"),
    detail = useLoad(
      () => (id ? data<ExportEvent>("/exports/" + id) : Promise.resolve(null)),
      "export:" + id,
    );
  return (
    <>
      <SectionTitle eyebrow="不可变历史内容" title="导出历史快照" />
      <p>每次导出独立保存。后续编辑不会覆盖历史内容。</p>
      <ErrorBox error={list.error} />
      <Loading loading={list.loading} />
      {list.value && !list.value.length && <Empty>暂无导出记录</Empty>}
      {list.value?.map((r) => (
        <article className="row" key={r.id}>
          <Link to={"/exports/" + r.id}>{r.id.slice(0, 8)}</Link>
          <span>{time(r.created_at)}</span>
          <a href={"/api/v1/exports/" + r.id + "/file"} download>
            下载原CSV
          </a>
        </article>
      ))}
      {id && (
        <section>
          <h2>本次实际导出集合</h2>
          <ErrorBox error={detail.error} />
          <Loading loading={detail.loading} />
          {detail.value && (
            <>
              <p>
                {time(detail.value.created_at)} · 哈希{" "}
                {detail.value.content_hash}
              </p>
              <a href={"/api/v1/exports/" + id + "/file"} download>
                下载本次CSV
              </a>
              {detail.value.items?.map((item) => (
                <Snapshot item={item} key={item.id} />
              ))}
            </>
          )}
        </section>
      )}
    </>
  );
}
export function Supplements({
  id,
  overview,
  refresh,
}: {
  id?: string;
  overview: Overview | null;
  refresh: () => void;
}) {
  const list = useLoad(
      () => allItems<Supplement>("/supplements"),
      "supplements",
    ),
    detail = useLoad(
      () =>
        id ? data<Supplement>("/supplements/" + id) : Promise.resolve(null),
      "supplement:" + id,
    );
  const resources = useLoad(MaterialsData, "supplement-resources");
  const [batch, setBatch] = useState(""),
    [kb, setKB] = useState(""),
    [selected, setSelected] = useState<string[]>([]),
    [confirmed, setConfirmed] = useState(false);
  const exports = useLoad(
    async () =>
      batch
        ? await Promise.all(
            (
              await allItems<ExportEvent>("/exports?source_batch_id=" + batch)
            ).map((r) => data<ExportEvent>("/exports/" + r.id)),
          )
        : [],
    "supplement-exports:" + batch,
  );
  const action = useAction();
  const s = detail.value;
  useEffect(() => {
    setSelected([]);
    setConfirmed(false);
  }, [batch]);
  return (
    <>
      <SectionTitle eyebrow="本人实际采用的来源" title="知识库实际补充" />
      <p className="notice">
        先在工作台外编辑知识库CSV。上传新版本后，选择实际采用的具体历史快照。本人确认后才能效果验证。
      </p>
      {!id && (
        <>
          <Upload
            kind="knowledge"
            onSaved={(r) => {
              resources.reload();
              setKB(r.id);
            }}
          />
          <label>
            原评测批次
            <select
              aria-label="补充原批次"
              value={batch}
              onChange={(e) => setBatch(e.target.value)}
            >
              <option value="">请选择原批次</option>
              {overview?.tasks
                .filter((t) => t.kind === "ordinary")
                .map((t) => (
                  <option value={t.id} key={t.id}>
                    {t.id.slice(0, 8)}
                  </option>
                ))}
            </select>
          </label>
          {resources.value && (
            <VersionSelect
              title="实际补充后的知识库版本"
              rows={resources.value[1]}
              value={kb}
              onChange={setKB}
            />
          )}
          <ErrorBox error={resources.error} />
          <ErrorBox error={exports.error} />
          <Loading loading={exports.loading} />
          {batch && exports.value && !exports.value.length && (
            <Empty>该批次没有可关联的历史导出快照</Empty>
          )}
          {exports.value?.map((event) => (
            <section key={event.id}>
              <h3>
                导出 {event.id.slice(0, 8)} · {time(event.created_at)}
              </h3>
              {event.items?.map((item) => (
                <div key={item.id}>
                  <label>
                    <input
                      type="checkbox"
                      aria-label={"采用快照 " + item.id}
                      checked={selected.includes(item.id)}
                      onChange={(e) =>
                        setSelected((prev) =>
                          e.target.checked
                            ? [...prev, item.id]
                            : prev.filter((v) => v !== item.id),
                        )
                      }
                    />
                    实际采用此具体快照
                  </label>
                  <Snapshot item={item} />
                </div>
              ))}
            </section>
          ))}
          <label>
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            本人确认所选内容已实际加入所选新知识库版本
          </label>
          <button
            disabled={
              !batch || !kb || !selected.length || !confirmed || action.busy
            }
            onClick={() =>
              void action.run(async () => {
                const record = await write<Supplement>("/supplements", {
                  source_batch_id: batch,
                  new_kb_id: kb,
                  export_item_ids: selected,
                  confirm: true,
                });
                list.reload();
                go("/supplements/" + record.id);
              })
            }
          >
            保存实际补充确认
          </button>
        </>
      )}
      <ErrorBox error={action.error} />
      {id && (
        <>
          <ErrorBox error={detail.error} />
          <Loading loading={detail.loading} />
          {s && (
            <>
              <h2>已确认补充记录</h2>
              <p>
                {time(s.confirmed_at)} · {s.message}
              </p>
              <p>
                可验证case：{s.source_case_ids?.length ?? 0}（后台去重来源）
              </p>
              <div className="chain">
                <Link to={"/materials/" + s.new_kb_id}>新知识库</Link> →
                具体历史快照 → QA → 来源case →{" "}
                <Link to={"/batches/" + s.source_batch_id}>原批次</Link> →{" "}
                <Link to={"/materials/" + s.rule_version_id}>原规则</Link> /{" "}
                <Link to={"/materials/" + s.old_kb_id}>旧知识库</Link>
              </div>
              {s.snapshots?.map((item) => (
                <Snapshot item={item} key={item.id} />
              ))}
              {s.cases?.map((c) => (
                <article key={c.id}>
                  <Link to={"/batches/" + s.source_batch_id + "/cases/" + c.id}>
                    {c.csv_case_id} · {c.question}
                  </Link>
                </article>
              ))}
              {!s.can_validate && <Empty>无可验证案例，不创建验证任务</Empty>}
              <p>{overview?.start_reason}</p>
              <button
                disabled={
                  !s.can_validate || !overview?.can_start || action.busy
                }
                onClick={() => {
                  if (
                    window.confirm(
                      "将对所选来源case重新生成旧新回复并分别评测。真实调用会产生费用。确认开始？",
                    )
                  )
                    void action.run(async () => {
                      const t = await write<Task>(
                        "/supplements/" + id + "/effect-tasks",
                        {},
                      );
                      refresh();
                      go("/effects/" + t.id);
                    });
                }}
              >
                开始效果验证
              </button>
              <h3>本补充记录的效果任务</h3>
              {overview?.tasks
                .filter(
                  (t) => t.kind === "effect" && t.source?.supplement_id === id,
                )
                .map((t) => (
                  <p key={t.id}>
                    <Link to={"/effects/" + t.id}>
                      {t.id.slice(0, 8)} · {label(t.state)} · 人工结论{" "}
                      {label(t.human_effect_conclusion)}
                    </Link>
                  </p>
                ))}
              <Json title="完整补充关系与版本" value={s} />
            </>
          )}
        </>
      )}
      <h2>补充历史</h2>
      <ErrorBox error={list.error} />
      {list.value && !list.value.length && (
        <Empty>暂无本人确认的补充记录</Empty>
      )}
      {list.value?.map((r) => (
        <article key={r.id}>
          <Link to={"/supplements/" + r.id}>
            {r.id.slice(0, 8)} · {time(r.confirmed_at)}
          </Link>
        </article>
      ))}
    </>
  );
}
function DrawEditor({
  draw,
  taskId,
  allowed,
  onSaved,
}: {
  draw: Draw;
  taskId: string;
  allowed: boolean;
  onSaved: () => void;
}) {
  const initial = () => ({
    accuracy: draw.mark?.accuracy ?? null,
    intent: draw.mark?.intent ?? null,
    service: draw.mark?.service ?? null,
  });
  const [marks, setMarks] = useState<Record<Dimension, Mark>>(initial);
  const action = useAction();
  useEffect(() => setMarks(initial()), [draw.mark?.revision]);
  return (
    <article className="draw">
      <h3>
        {draw.kind === "initial" ? "初抽" : "补抽"} #{draw.ordinal} ·{" "}
        {draw.case_id}
      </h3>
      {draw.unusable_reasons.length ? (
        <div className="error">
          不能用于人工比较：{draw.unusable_reasons.join("；")}。失败轨迹保留。
        </div>
      ) : (
        <>
          <div className="form-grid">
            {Object.entries(dimensions).map(([key, title]) => (
              <label key={key}>
                {title}
                <select
                  aria-label={draw.case_id + " " + title}
                  value={marks[key as Dimension] ?? ""}
                  disabled={!allowed || action.busy}
                  onChange={(e) =>
                    setMarks((prev) => ({
                      ...prev,
                      [key]: e.target.value || null,
                    }))
                  }
                >
                  <option value="">尚未标记</option>
                  {["改善", "持平", "变差"].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <button
            disabled={!allowed || action.busy}
            onClick={() =>
              void action.run(async () => {
                await write(
                  "/effect-tasks/" + taskId + "/sampling/" + draw.case_id,
                  { expected_revision: draw.mark?.revision ?? 0, ...marks },
                  "PATCH",
                );
                onSaved();
              })
            }
          >
            保存本case人工标记
          </button>
          <ErrorBox error={action.error} />
        </>
      )}
    </article>
  );
}
export function Effects({
  id,
  overview,
  refresh,
}: {
  id?: string;
  overview: Overview | null;
  refresh: () => void;
}) {
  const effect = useLoad(
      () => (id ? data<Effect>("/effect-tasks/" + id) : Promise.resolve(null)),
      "effect:" + id,
      true,
    ),
    sampling = useLoad(
      () =>
        id
          ? data<Sampling>("/effect-tasks/" + id + "/sampling")
          : Promise.resolve(null),
      "sampling:" + id,
      true,
    );
  const action = useAction();
  const t = overview?.tasks.find((t) => t.id === id),
    e = effect.value;
  return (
    <>
      <SectionTitle
        eyebrow="两侧依据与本人效果判断"
        title="效果对比与人工抽检"
      />
      {!id && (
        <>
          <p>请从已确认补充记录详情发起。自动阶段结束后，人工抽检独立继续。</p>
          <Link to="/supplements">进入实际补充记录</Link>
          {overview?.tasks
            .filter((t) => t.kind === "effect")
            .map((t) => (
              <article key={t.id}>
                <Link to={"/effects/" + t.id}>
                  {t.id.slice(0, 8)} · {time(t.started_at)}
                </Link>{" "}
                <Badge value={t.state} /> 人工效果结论：
                {label(t.human_effect_conclusion)}
              </article>
            ))}
        </>
      )}
      {id && (
        <>
          <ErrorBox error={effect.error} />
          <Loading loading={effect.loading} />
          {t && (
            <>
              <Progress task={t} />
              <button
                disabled={!t.capabilities.can_cancel || action.busy}
                onClick={() => {
                  if (window.confirm("取消后整个效果任务作废。确认取消？"))
                    void action.run(async () => {
                      await write("/tasks/" + id + "/cancel", {
                        expected_revision: t.revision,
                      });
                      refresh();
                      effect.reload();
                      sampling.reload();
                    });
                }}
              >
                取消效果任务
              </button>
              <ErrorBox error={action.error} />
            </>
          )}
          {e && (
            <>
              <div className="columns">
                {(["old", "new"] as const).map((side) => (
                  <section key={side}>
                    <h2>{side === "old" ? "旧知识库侧" : "新知识库侧"}</h2>
                    <MetricsView
                      status={e.metrics.status}
                      metrics={e.metrics.data?.[side]}
                    />
                  </section>
                ))}
              </div>
              <Json title="两侧同范围输入版本" value={e.source} />
              {e.cases.map((c) => (
                <details className="panel" key={c.case_id}>
                  <summary>
                    {c.case_number} · {c.question} ·{" "}
                    {c.comparison.comparable ? "可比较" : "不可比较"} · 新回复
                    {c.new.evaluation.is_badcase
                      ? "Badcase"
                      : c.new.evaluation.state === "succeeded"
                        ? "合格"
                        : "尚无成功评分"}
                  </summary>
                  <h3>完整问题</h3>
                  <p className="full">{c.question}</p>
                  <History messages={c.history} />
                  {!c.comparison.comparable && (
                    <p className="error">{c.comparison.reasons.join("；")}</p>
                  )}
                  <div className="columns">
                    {(["old", "new"] as const).map((side) => (
                      <section key={side}>
                        <h3>{side === "old" ? "旧侧" : "新侧"}重新生成回复</h3>
                        <p className="full">
                          {c[side].generation.reply ??
                            label(c[side].generation.state)}
                        </p>
                        <p>
                          生成实际次数 {c[side].generation.attempt_count} ·
                          评测实际次数 {c[side].evaluation.attempt_count}
                        </p>
                        {c[side].evaluation.contract && (
                          <Scores
                            contract={c[side].evaluation.contract!}
                            composite={c[side].evaluation.composite_score}
                            badcase={c[side].evaluation.is_badcase}
                            gaps={c[side].evaluation.knowledge_gaps}
                          />
                        )}
                        <Json
                          title="生成结果、异常及配置追溯"
                          value={c[side].generation}
                        />
                        <Json
                          title="评测依据与异常"
                          value={c[side].evaluation}
                        />
                      </section>
                    ))}
                  </div>
                </details>
              ))}
            </>
          )}
          <section>
            <h2>本人抽检与效果结论</h2>
            <p className="notice">
              模型只辅助生成和评分。请本人比较两侧完整依据。新回复合格状态与人工效果结论分别维护。
            </p>
            <ErrorBox error={sampling.error} />
            <Loading loading={sampling.loading} />
            {sampling.value && (
              <>
                <p>
                  参与 {sampling.value.population_size ?? "尚未固定"} · 目标{" "}
                  {sampling.value.target_size ?? "尚未固定"} · 有效抽检{" "}
                  {sampling.value.valid_count ?? 0}
                </p>
                <p>
                  人工效果结论：
                  <Badge value={sampling.value.status} />
                </p>
                {sampling.value.status === "validation_failed" && (
                  <p className="error">
                    成功且可比较的抽检样本不足。验证失败，不降低抽检目标。
                  </p>
                )}
                {sampling.value.draws.map((d) => (
                  <DrawEditor
                    key={d.case_id}
                    draw={d}
                    taskId={id}
                    allowed={sampling.value!.marking_allowed}
                    onSaved={() => {
                      sampling.reload();
                      effect.reload();
                      refresh();
                    }}
                  />
                ))}
                <Json
                  title="完整固定参与范围与抽样轨迹"
                  value={sampling.value}
                />
              </>
            )}
          </section>
        </>
      )}
    </>
  );
}
