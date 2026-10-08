import client from "./client";
import type { UserConfig, UserConfigUpdate } from "@/types";

export const configsApi = {
  get(): Promise<UserConfig> {
    return client.get("/configs/me").then((r) => r.data);
  },

  update(data: UserConfigUpdate): Promise<UserConfig> {
    return client.put("/configs/me", data).then((r) => r.data);
  },
};
