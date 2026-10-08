import client from "./client";
import type { RagSearchResponse } from "@/types";

export const ragApi = {
  search(q: string, topK = 5, contentType?: string): Promise<RagSearchResponse> {
    const params: Record<string, any> = { q, top_k: topK };
    if (contentType) params.content_type = contentType;
    return client.get("/rag/search", { params }).then((r) => r.data);
  },
};
