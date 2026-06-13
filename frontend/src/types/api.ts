// ── Auth & User ──

export interface PasswordLoginRequest {
  login: string;
  password: string;
}

export interface TokenModel {
  access_token: string;
  refresh_token: string;
}

export interface UserProfileViewModel {
  id: string;
  first_name: string | null;
  last_name: string | null;
  username: string | null;
  language_code: string | null;
  photo_url: string | null;
}

export interface PasswordAuthResponse {
  tokens: TokenModel;
  user: UserProfileViewModel;
}

export interface UserSummaryViewModel {
  id: string;
  first_name: string | null;
  last_name: string | null;
  username: string | null;
}

// ── Pagination ──

export interface PaginationParams {
  page: number;
  size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface CursorPaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
}

// ── Bots ──

export type BotStatus = "active" | "disabled" | "maintenance";

export interface BotCreateRequest {
  token: string;
}

export interface BotUpdateRequest {
  token?: string | null;
  status?: BotStatus | null;
}

export interface BotViewModel {
  id: string;
  name: string;
  status: BotStatus;
  created_at: string;
}

// ── Chats & Messages ──

export type SenderType = "user" | "bot" | "admin" | "system";
export type MessageType = "text" | "media" | "image" | "video" | "audio" | "document" | "system";
export type ChatStatus = "open" | "closed" | "blocked";

export interface ChatListItemViewModel {
  chat_id: string;
  telegram_id: number;
  first_name: string | null;
  username: string | null;
  last_message: string | null;
  updated_at: string;
}

export interface MessageListItemViewModel {
  id: string;
  sender: SenderType;
  content: string | null;
  created_at: string;
}

export interface SendMessageRequest {
  text: string;
}

export interface SendMessageResponse {
  telegram_message_id: number;
  status: string;
}

// ── Broadcasts ──

export type BroadcastStatus = "draft" | "scheduled" | "processing" | "sent" | "failed" | "cancelled";

export interface BroadcastFilters {
  last_active_days?: number | null;
}

export interface BroadcastCreateRequest {
  bot_id: string;
  text: string;
  filters?: BroadcastFilters | null;
  schedule_at?: string | null;
}

export interface BroadcastResponse {
  id: string;
  status: BroadcastStatus;
}

export interface BroadcastStatsResponse {
  total: number;
  sent: number;
  failed: number;
}

// ── Analytics ──

export interface BotAnalyticsSummary {
  users: number;
  chats: number;
  messages: number;
  dau: number;
}

// ── System ──

export interface HealthCheckResponse {
  status: "ok";
}

export interface SuccessResponse {
  success: boolean;
}

// ── API Error ──

export interface ApiErrorDetail {
  loc?: (string | number)[];
  msg: string;
  type: string;
}

export interface ApiError {
  detail: string | ApiErrorDetail[];
}
