import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";
import { ApiError } from "./api";
import { MetricsView, Scores, History, ErrorBox, Progress } from "./components";
import { QAEditor } from "./pages";
import type { Contract, Task } from "./types";
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
describe("权威后端结果展示", () => {
  it("资源加载期间显示真实加载反馈", () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => new Promise(() => {}),
    );
    render(<QAEditor id="loading" />);
    expect(screen.getByRole("status")).toHaveTextContent("正在读取持久记录");
  });
  it("零成功保留无数据，不显示0分", () => {
    render(
      <MetricsView
        metrics={{
          display: {
            pass_rate: null,
            average_score: null,
            error_rate: "100.00%",
          },
          counts: {},
        }}
      />,
    );
    expect(screen.getAllByText("无数据")).toHaveLength(2);
    expect(screen.getByText("100.00%")).toBeInTheDocument();
  });
  it("取消显示作废", () => {
    render(<MetricsView metrics={null} status="cancelled" />);
    expect(screen.getAllByText("已作废")).toHaveLength(3);
  });
  it("运行中不提前给出指标", () => {
    render(<MetricsView metrics={null} status="pending" />);
    expect(screen.getAllByText("统计待完成")).toHaveLength(3);
  });
  it("使用后台显示值", () => {
    render(
      <MetricsView
        metrics={{
          display: {
            pass_rate: "94.99%",
            average_score: "4.33",
            error_rate: "5.00%",
          },
          counts: {},
        }}
      />,
    );
    expect(screen.getByText("94.99%")).toBeInTheDocument();
    expect(screen.getByText("4.33")).toBeInTheDocument();
  });
  it("完整理由及证据可查看", () => {
    const c: Contract = {
      scores: {
        accuracy: { score: 5, reason: "完整准确理由" },
        intent: { score: 5, reason: "完整意图理由" },
        service: { score: 3, reason: "完整服务理由" },
      },
      primary_cause: "回复内容敷衍",
      secondary_causes: [],
      has_material_conflict: false,
    };
    render(
      <Scores
        contract={c}
        composite="4.33"
        badcase
        gaps={[
          {
            gap: "缺失点",
            snippet: "原句",
            reason: "证据理由",
            location: { start: 0 },
          },
        ]}
      />,
    );
    expect(screen.getByText("完整服务理由")).toBeInTheDocument();
    expect(screen.getByText(/Badcase/)).toBeInTheDocument();
    expect(screen.getByText(/证据理由/)).toBeInTheDocument();
  });
  it("上下文按原文展示且不执行HTML", () => {
    render(
      <History
        messages={[
          { role: "user", content: '<script>原文</script>\n逗号,引号"' },
        ]}
      />,
    );
    expect(screen.getByText(/<script>原文/)).toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
  });
  it("校验错误展示字段与原操作未知", () => {
    render(
      <ErrorBox
        error={
          new ApiError(
            {
              code: "COMMIT_UNKNOWN",
              message: "未知",
              commit_state: "unknown",
              field_errors: [{ row: 2, field: "案例编号", reason: "重复" }],
            },
            503,
          )
        }
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("案例编号");
    expect(screen.getByRole("alert")).toHaveTextContent("核查原操作");
  });
  it("实际进度和次数展示", () => {
    render(
      <Progress
        task={
          {
            state: "running",
            phase: "evaluating",
            elapsed_ms: null,
            progress: { succeeded: 1, final_failed: 1, pending: 2, running: 1 },
            items: [{ attempt_count: 3 }],
          } as Task
        }
      />,
    );
    expect(screen.getByText(/最终失败 1/)).toBeInTheDocument();
    expect(screen.getByText(/attempt_count/)).toHaveTextContent("3");
  });
  it("未保存编辑不能审核，取消编辑可还原", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      async (input) =>
        new Response(
          JSON.stringify({
            data: String(input).includes("capabilities")
              ? {
                  can_approve: true,
                  can_edit: true,
                  can_export: true,
                  reason: "本人审核",
                }
              : {
                  id: "qa",
                  task_id: "batch",
                  case_id: "case",
                  standard_question: "原问",
                  answer: "原答",
                  revision: 1,
                  review_state: "approved",
                  history: [],
                  knowledge_gap: { snippet: "原句", reason: "依据" },
                  trace: {},
                },
          }),
          { status: 200 },
        ),
    );
    render(<QAEditor id="qa" />);
    const q = await screen.findByLabelText("标准问");
    fireEvent.click(screen.getByRole("checkbox"));
    expect(screen.getByRole("button", { name: "确认审核通过" })).toBeEnabled();
    fireEvent.change(q, { target: { value: "改问" } });
    expect(screen.getByRole("button", { name: "确认审核通过" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "取消编辑" }));
    expect(q).toHaveValue("原问");
    expect(screen.getByRole("button", { name: "确认审核通过" })).toBeEnabled();
  });
});
