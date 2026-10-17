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

// 通用下载：用隐藏 <a> 触发，可携带 filename
function triggerDownload(url: string, filename: string): void {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// 构建 PPT 文件的访问 URL（下载 / 预览均走此端点，服务端按需生成并缓存）
export function pptUrl(sessionId: string): string {
  const token = localStorage.getItem("access_token") || "";
  return `/api/v1/analyses/${sessionId}/ppt?token=${encodeURIComponent(token)}`;
}

// 触发浏览器下载 .pptx
export function downloadPpt(sessionId: string, filename = "最终分析报告.pptx"): void {
  triggerDownload(pptUrl(sessionId), filename);
}

// 构建 Word 文件的访问 URL（服务端按需生成并缓存）
export function docxUrl(sessionId: string): string {
  const token = localStorage.getItem("access_token") || "";
  return `/api/v1/analyses/${sessionId}/docx?token=${encodeURIComponent(token)}`;
}

// 触发浏览器下载 .docx
export function downloadDocx(sessionId: string, filename = "最终分析报告.docx"): void {
  triggerDownload(docxUrl(sessionId), filename);
}
