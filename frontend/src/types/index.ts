export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt?: Date;
}

export interface ContentType {
  id: number;
  name: string;
  display_name: string;
  description?: string;
}

export interface Platform {
  id: number;
  name: string;
  display_name: string;
}

export interface GeneratedContent {
  id: string;
  content_type_id: number;
  platform_id: number;
  title?: string;
  body: string;
  slides?: Record<string, unknown>[];
  hashtags?: string[];
  cta?: string;
  hook?: string;
  rating?: number;
  feedback?: string;
  is_favorite: boolean;
  created_at: string;
}

export interface ScrapeJob {
  id: string;
  platform_id: number;
  job_type: string;
  status: "pending" | "running" | "completed" | "failed";
  search_terms?: string[];
  target_handles?: string[];
  max_results: number;
  results_count: number;
  error_message?: string;
  created_at: string;
}

export interface Report {
  id: string;
  report_type: string;
  title: string;
  summary?: string;
  full_content?: string;
  data?: Record<string, unknown>;
  created_at: string;
}
