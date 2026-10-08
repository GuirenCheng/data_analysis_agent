import client from "./client";
import type { SessionCreate, SessionOut, SessionDetail, SessionListResponse } from "@/types";

export const sessionsApi = {
  list(page = 1, perPage = 20, status?: string): Promise<SessionListResponse> {
    const params: Record<string, any> = { page, per_page: perPage };
    if (status) params.status = status;
    return client.get("/sessions", { params }).then((r) => r.data);
  },

  create(data: SessionCreate): Promise<SessionOut> {
    return client.post("/sessions", data).then((r) => r.data);
  },

  get(id: string): Promise<SessionDetail> {
    return client.get(`/sessions/${id}`).then((r) => r.data);
  },

  delete(id: string): Promise<void> {
    return client.delete(`/sessions/${id}`);
  },
};
