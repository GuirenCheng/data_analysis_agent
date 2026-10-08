import client from "./client";
import type { FileOut, FilePreview } from "@/types";

export const filesApi = {
  upload(file: File): Promise<{ file: FileOut; message: string }> {
    const form = new FormData();
    form.append("file", file);
    return client.post("/files/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    }).then((r) => r.data);
  },

  preview(fileId: string, rows = 10): Promise<FilePreview> {
    return client.get(`/files/${fileId}/preview`, { params: { rows } }).then((r) => r.data);
  },

  delete(fileId: string): Promise<void> {
    return client.delete(`/files/${fileId}`);
  },
};
