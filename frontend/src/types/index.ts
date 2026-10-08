// ── 认证 ──────────────────────────
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserInfo {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
}

// ── 会话 ──────────────────────────
export type SessionStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface SessionCreate {
  query: string;
  file_ids: string[];
  max_rounds: number;
}

export interface SessionOut {
  id: string;
  user_id: string;
  title?: string;
  query: string;
  status: SessionStatus;
  max_rounds: number;
  current_round: number;
  progress: number;
  error_message?: string;
  output_dir?: string;
  report_path?: string;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
}

export interface SessionDetail extends SessionOut {
  steps: AnalysisStep[];
  figures: FigureInfo[];
}

export interface SessionListResponse {
  items: SessionOut[];
  total: number;
  page: number;
  per_page: number;
}

// ── 分析 ──────────────────────────
export interface AnalysisStep {
  id: string;
  round_number: number;
  action: string;
  code?: string;
  execution_output?: string;
  execution_error?: string;
  execution_success?: boolean;
  figures_collected?: Record<string, any>[];
  created_at?: string;
}

export interface FigureInfo {
  figure_number?: number;
  filename: string;
  file_path: string;
  description: string;
  analysis: string;
}

export interface ReportOut {
  markdown: string;
  figures: FigureInfo[];
  report_file_path?: string;
}

export interface StreamEvent {
  status: SessionStatus;
  progress: number;
  current_round: number;
  message?: string;
}

// ── 文件 ──────────────────────────
export interface FileOut {
  id: string;
  original_name: string;
  file_size?: number;
  mime_type?: string;
  columns_detected?: string[];
  row_count?: number;
  created_at?: string;
}

export interface FilePreview {
  columns: string[];
  rows: any[][];
  total_rows: number;
}

// ── 配置 ──────────────────────────
export interface UserConfig {
  id: string;
  llm_provider: string;
  llm_model: string;
  llm_base_url?: string;
  temperature: number;
  max_tokens: number;
  default_max_rounds: number;
  default_output_dir: string;
}

export interface UserConfigUpdate {
  llm_provider?: string;
  llm_model?: string;
  llm_base_url?: string;
  llm_api_key?: string;
  temperature?: number;
  max_tokens?: number;
  default_max_rounds?: number;
  default_output_dir?: string;
}

// ── RAG ───────────────────────────
export interface RagResult {
  content_text: string;
  content_type: string;
  source_session_id: string;
  similarity: number;
}

export interface RagSearchResponse {
  results: RagResult[];
  query: string;
  total_found: number;
}

// ── 通用 ──────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface ErrorResponse {
  detail: string;
  code: string;
}
