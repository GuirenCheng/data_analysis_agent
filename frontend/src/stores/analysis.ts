import { defineStore } from "pinia";
import { ref } from "vue";
import { sessionsApi } from "@/api/sessions";
import { analysesApi } from "@/api/analyses";
import type { SessionOut, SessionDetail, StreamEvent } from "@/types";

export const useAnalysisStore = defineStore("analysis", () => {
  const sessions = ref<SessionOut[]>([]);
  const currentSession = ref<SessionDetail | null>(null);
  const total = ref(0);
  const loading = ref(false);

  // 当前正在监听进度的 session 和 eventSource
  const activeStreams = new Map<string, EventSource>();
  const streamProgress = ref<Record<string, StreamEvent>>({});

  async function fetchSessions(page = 1, perPage = 20, status?: string) {
    loading.value = true;
    try {
      const res = await sessionsApi.list(page, perPage, status);
      sessions.value = res.items;
      total.value = res.total;
    } finally {
      loading.value = false;
    }
  }

  async function createSession(query: string, fileIds: string[], maxRounds = 20) {
    const session = await sessionsApi.create({
      query,
      file_ids: fileIds,
      max_rounds: maxRounds,
    });
    sessions.value.unshift(session);
    return session;
  }

  async function fetchSessionDetail(id: string) {
    currentSession.value = await sessionsApi.get(id);
    return currentSession.value;
  }

  async function deleteSession(id: string) {
    await sessionsApi.delete(id);
    sessions.value = sessions.value.filter((s) => s.id !== id);
    stopStream(id);
  }

  function startStream(sessionId: string) {
    if (activeStreams.has(sessionId)) return;

    const token = localStorage.getItem("access_token") || "";
    const es = analysesApi.streamProgress(sessionId, token);

    es.onmessage = (event) => {
      try {
        const data: StreamEvent = JSON.parse(event.data);
        streamProgress.value[sessionId] = data;

        // 更新列表中的会话状态
        const idx = sessions.value.findIndex((s) => s.id === sessionId);
        if (idx >= 0) {
          sessions.value[idx].status = data.status;
          sessions.value[idx].progress = data.progress;
          sessions.value[idx].current_round = data.current_round;
        }
      } catch { /* ignore parse errors */ }
    };

    es.onerror = () => {
      es.close();
      activeStreams.delete(sessionId);
    };

    activeStreams.set(sessionId, es);
  }

  function stopStream(sessionId: string) {
    const es = activeStreams.get(sessionId);
    if (es) {
      es.close();
      activeStreams.delete(sessionId);
    }
  }

  function stopAllStreams() {
    activeStreams.forEach((es) => es.close());
    activeStreams.clear();
  }

  return {
    sessions,
    currentSession,
    total,
    loading,
    streamProgress,
    fetchSessions,
    createSession,
    fetchSessionDetail,
    deleteSession,
    startStream,
    stopStream,
    stopAllStreams,
  };
});
