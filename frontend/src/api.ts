import { useCallback, useEffect, useState } from "react";

export interface Failure {
  code: string;
  message: string;
  commit_state?: string;
  field_errors?: Record<string, unknown>[];
}
export class ApiError extends Error {
  constructor(
    public failure: Failure,
    public status: number,
  ) {
    super(failure.message);
  }
}
export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch("/api/v1" + path, options);
  const packet = await response.json();
  if (!response.ok) throw new ApiError(packet as Failure, response.status);
  return packet as T;
}
export async function data<T>(path: string): Promise<T> {
  return (await request<{ data: T }>(path)).data;
}
export async function allItems<T>(path: string): Promise<T[]> {
  const rows: T[] = [];
  for (let offset = 0; ; offset += 100) {
    const next = await request<{ items: T[] }>(
      path + (path.includes("?") ? "&" : "?") + `limit=100&offset=${offset}`,
    );
    rows.push(...next.items);
    if (next.items.length < 100) return rows;
  }
}
const pendingKey = "workbench-pending-operation";
let sending = false;
export const operationIsSending = () => sending;
function setSending(value: boolean) {
  sending = value;
  window.dispatchEvent(new Event("pending-operation"));
}
export interface Pending {
  path: string;
  method: string;
  operation_id: string;
  body: Record<string, unknown> | null;
  upload?: { kind: string; filename: string; sha256: string };
}
export function pending(): Pending | null {
  try {
    return JSON.parse(sessionStorage.getItem(pendingKey) || "null");
  } catch {
    return null;
  }
}
export function clearPending() {
  sessionStorage.removeItem(pendingKey);
  window.dispatchEvent(new Event("pending-operation"));
}
function remember(value: Pending) {
  sessionStorage.setItem(pendingKey, JSON.stringify(value));
  window.dispatchEvent(new Event("pending-operation"));
}
export async function write<T>(
  path: string,
  body: Record<string, unknown>,
  method = "POST",
  original = false,
): Promise<T> {
  if (sending || (pending() && !original))
    throw new Error("有保存结果尚未确认。请先查询原操作。");
  setSending(true);
  const packet = {
    ...body,
    operation_id: body.operation_id || crypto.randomUUID(),
  };
  remember({
    path,
    method,
    operation_id: String(packet.operation_id),
    body: packet,
  });
  try {
    const result = await request<{ data: T }>(path, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(packet),
    });
    clearPending();
    return result.data;
  } catch (error) {
    if (error instanceof ApiError && error.failure.commit_state !== "unknown")
      clearPending();
    throw error;
  } finally {
    setSending(false);
  }
}
export async function upload<T>(kind: string, file: File): Promise<T> {
  if (pending() || sending) throw new Error("请先核查尚未确认的操作结果");
  setSending(true);
  const operation_id = crypto.randomUUID();
  try {
    remember({
      path: "/uploads",
      method: "POST",
      operation_id,
      body: null,
      upload: { kind, filename: file.name, sha256: await fileDigest(file) },
    });
    const form = new FormData();
    form.append("kind", kind);
    form.append("operation_id", operation_id);
    form.append("file", file);
    const result = await request<{ data: T }>("/uploads", {
      method: "POST",
      body: form,
    });
    clearPending();
    return result.data;
  } catch (error) {
    if (error instanceof ApiError && error.failure.commit_state !== "unknown")
      clearPending();
    throw error;
  } finally {
    setSending(false);
  }
}
export async function fileDigest(file: File) {
  const bytes = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(bytes), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
export function useLoad<T>(
  loader: () => Promise<T>,
  key: string,
  poll = false,
) {
  const [value, setValue] = useState<T | null>(null),
    [error, setError] = useState<Error | null>(null),
    [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision((x) => x + 1), []);
  useEffect(() => {
    let active = true,
      inFlight = false;
    setValue(null);
    setLoading(true);
    const run = async () => {
      if (inFlight) return;
      inFlight = true;
      try {
        const result = await loader();
        if (active) {
          setValue(result);
          setError(null);
        }
      } catch (e) {
        if (active) setError(e instanceof Error ? e : new Error(String(e)));
      } finally {
        inFlight = false;
        if (active) setLoading(false);
      }
    };
    void run();
    const timer = poll
      ? window.setInterval(() => {
          if (document.visibilityState === "visible") void run();
        }, 2000)
      : undefined;
    return () => {
      active = false;
      clearInterval(timer);
    };
    // 每个资源显式key管理加载，防止闭包函数每次渲染重发。
  }, [key, revision, poll]);
  return { value, error, loading, reload };
}
