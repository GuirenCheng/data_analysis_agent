import client from "./client";
import type { AnalysisStep, ReportOut, StreamEvent } from "@/types";

export const analysesApi = {
  getSteps(sessionId: string): Promise<AnalysisStep[]> {
    return client.get(`/analyses/${sessionId}/steps`).then((r) => r.data);
  },

  getReport(sessionId: string): Promise<ReportOut> {
    return client.get(`/analyses/${sessionId}/report`).then((r) => r.data);
  },

  cancel(sessionId: string): Promise<void> {
    return client.post(`/analyses/${sessionId}/cancel`);
  },

  // SSE 进度流 — 返回 EventSource 以便组件管理生命周期
  streamProgress(sessionId: string, token: string): EventSource {
    const base = "/api/v1";
    const url = `${base}/analyses/${sessionId}/stream?token=${encodeURIComponent(token)}`;
    return new EventSource(url);
  },
};

// 构建图表图片的访问 URL（<img>/<el-image> 无法设置 Authorization 头，用 ?token= 兜底）
export function figureUrl(sessionId: string, filename: string): string {
  const token = localStorage.getItem("access_token") || "";
  return `/api/v1/analyses/${sessionId}/figures/${encodeURIComponent(filename)}?token=${encodeURIComponent(token)}`;
}
