import type { BotLogViewModel } from "./api";

export type WSAction = "authenticate" | "subscribe" | "unsubscribe" | "typing" | "ping";

export type EventType =
  | "chat.message.created"
  | "chat.message.updated"
  | "chat.message.deleted"
  | "chat.created"
  | "chat.typing"
  | "bot.log.created"
  | "system.error";

/**
 * Opt-in event streams. Log traffic is orders of magnitude denser than chat
 * traffic, so the backend only sends it to sockets that asked for this topic.
 */
export type WSTopic = "logs";

export interface WSUplinkMessage {
  action: WSAction;
  token?: string;
  chat_id?: string;
  bot_id?: string;
  topic?: WSTopic;
}

export interface WSDownlinkEnvelope {
  version: number;
  event: EventType;
  bot_id: string;
  /** Null for events that are not tied to a chat (e.g. bot logs). */
  chat_id: string | null;
  timestamp: number;
  data: Record<string, unknown>;
}

export interface WSErrorPayload {
  code: number;
  message: string;
}

export interface WSChatMessageCreatedData {
  message_id: string;
  tg_message_id: number;
  text: string;
  sender_type: "user" | "bot" | "admin" | "system";
}

export interface WSChatCreatedData {
  chat_id: string;
  telegram_user: Record<string, unknown>;
  status: "open" | "closed" | "blocked";
}

export interface WSBotLogCreatedData {
  records: BotLogViewModel[];
}
