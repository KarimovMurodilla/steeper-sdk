export type WSAction = "authenticate" | "subscribe" | "unsubscribe" | "typing" | "ping";

export type EventType =
  | "chat.message.created"
  | "chat.message.updated"
  | "chat.message.deleted"
  | "chat.created"
  | "chat.typing"
  | "system.error";

export interface WSUplinkMessage {
  action: WSAction;
  token?: string;
  chat_id?: string;
  bot_id?: string;
}

export interface WSDownlinkEnvelope {
  version: number;
  event: EventType;
  bot_id: string;
  chat_id: string;
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
