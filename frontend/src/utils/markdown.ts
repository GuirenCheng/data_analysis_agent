import { marked } from "marked";
import { figureUrl } from "@/api/analyses";

/**
 * 渲染 Markdown，并把报告里以相对路径引用的图片（`![](./文件名.png)`）
 * 重写为后端图片端点，否则图片会按前端 origin（localhost:3000）解析而 404。
 */
export function renderMarkdown(markdown: string, sessionId: string): string {
  const html = marked.parse(markdown) as string;

  return html.replace(/src="\.\/([^"]+)"/g, (_match, name: string) => {
    // marked 会把文件名做 URL 编码（如 `%E6%B5%8B`），先解码还原原始文件名，
    // 再交给 figureUrl 统一 encodeURIComponent，避免二次编码。
    let decoded = name;
    try {
      decoded = decodeURIComponent(name);
    } catch {
      /* 保持原样 */
    }
    decoded = decoded
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"');
    return `src="${figureUrl(sessionId, decoded)}"`;
  });
}
