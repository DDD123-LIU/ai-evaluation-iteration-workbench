import { afterEach, it, expect, vi } from "vitest";
import { ApiError, allItems, clearPending, pending, write } from "./api";
afterEach(() => {
  clearPending();
  vi.restoreAllMocks();
});
it("成功写入保存一个操作编号，结束后清理", async () => {
  const mock = vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValue(new Response(JSON.stringify({ data: { id: "saved" } })));
  expect(await write("/qa/q", { question: "原问" })).toEqual({ id: "saved" });
  const options = mock.mock.calls[0][1];
  expect(JSON.parse(String(options?.body)).operation_id).toMatch(
    /^[a-f\d-]{36}$/,
  );
  expect(pending()).toBeNull();
});
it("未知响应保留原请求，拒绝第二个新动作", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({
        code: "COMMIT_UNKNOWN",
        message: "未知",
        commit_state: "unknown",
      }),
      { status: 503 },
    ),
  );
  await expect(
    write("/exports", { selected_qa_ids: ["q"] }),
  ).rejects.toBeInstanceOf(ApiError);
  const original = pending();
  expect(original?.body?.selected_qa_ids).toEqual(["q"]);
  await expect(write("/exports", {})).rejects.toThrow("尚未确认");
  expect(pending()?.operation_id).toBe(original?.operation_id);
});
it("已知未提交的字段错误可以修正", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ code: "QA_INCOMPLETE", message: "缺答案" }), {
      status: 422,
    }),
  );
  await expect(write("/qa/q", {})).rejects.toBeInstanceOf(ApiError);
  expect(pending()).toBeNull();
});
it("网络失败保留原编号，原请求重发不产生新编号", async () => {
  const mock = vi
    .spyOn(globalThis, "fetch")
    .mockRejectedValueOnce(new TypeError("网络故障"));
  await expect(write("/qa/q", { answer: "原答" }, "PATCH")).rejects.toThrow(
    "网络故障",
  );
  const original = pending()!;
  mock.mockResolvedValueOnce(
    new Response(JSON.stringify({ data: { id: "q" } })),
  );
  await write(original.path, original.body!, original.method, true);
  expect(JSON.parse(String(mock.mock.calls[1][1]?.body)).operation_id).toBe(
    original.operation_id,
  );
  expect(pending()).toBeNull();
});
it("分页读完全部历史记录", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          items: Array.from({ length: 100 }, (_, id) => ({ id })),
        }),
      ),
    )
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ items: [{ id: 100 }] })),
    );
  expect(await allItems("/materials?kind=rules")).toHaveLength(101);
});
