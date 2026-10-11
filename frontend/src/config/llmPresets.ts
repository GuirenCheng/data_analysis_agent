// LLM 提供商预设：帮助不了解 API 的用户一键选好 Base URL 与常用模型，
// 不再需要手动填写。每个提供商都支持「自定义」入口，保留高级用户的手工能力。

export interface LlmPreset {
  key: string;
  label: string;
  baseUrl: string;
  models: string[];
}

export const LLM_PRESETS: LlmPreset[] = [
  {
    key: "deepseek",
    label: "DeepSeek（深度求索）",
    baseUrl: "https://api.deepseek.com",
    models: ["deepseek-v4-pro", "deepseek-r1-250528", "deepseek-chat", "deepseek-reasoner"],
  },
  {
    key: "openai",
    label: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo-preview", "o1", "o1-mini"],
  },
  {
    key: "siliconflow",
    label: "硅基流动 SiliconFlow",
    baseUrl: "https://api.siliconflow.cn/v1",
    models: [
      "deepseek-ai/DeepSeek-V3",
      "deepseek-ai/DeepSeek-R1",
      "Qwen/Qwen2.5-72B-Instruct",
      "Qwen/Qwen2.5-7B-Instruct",
    ],
  },
  {
    key: "zhipu",
    label: "智谱 AI（GLM）",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
    models: ["glm-4-plus", "glm-4-air", "glm-4-flash"],
  },
  {
    key: "custom",
    label: "自定义（手动填写）",
    baseUrl: "",
    models: [],
  },
];

export function getPreset(key: string): LlmPreset | undefined {
  return LLM_PRESETS.find((p) => p.key === key);
}

/** 把后端存的旧 provider 值（如 openai_compatible）归一化到预设 key，未知值归入「自定义」。 */
export function normalizeProviderKey(key: string): string {
  return getPreset(key) ? key : "custom";
}
