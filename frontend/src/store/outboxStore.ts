import { create } from "zustand";

export interface OutboxMessage {
  /** Client-generated id; the server message arrives with its own id. */
  clientId: string;
  chatId: string;
  text: string;
  createdAt: string;
  status: "sending" | "failed";
}

interface OutboxState {
  /** Keyed by chat id, oldest first. */
  messages: Record<string, OutboxMessage[]>;
  add: (message: OutboxMessage) => void;
  markFailed: (chatId: string, clientId: string) => void;
  markSending: (chatId: string, clientId: string) => void;
  remove: (chatId: string, clientId: string) => void;
}

/**
 * Messages the admin sent that the server has not confirmed yet. They live
 * outside react-query so a background refetch cannot wipe a failed send before
 * the user has had a chance to retry it.
 */
/** Stable empty result: a fresh [] each render would loop useSyncExternalStore. */
export const NO_OUTBOX: OutboxMessage[] = [];

export const useOutboxStore = create<OutboxState>((set) => ({
  messages: {},

  add: (message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [message.chatId]: [...(state.messages[message.chatId] ?? []), message],
      },
    })),

  markFailed: (chatId, clientId) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [chatId]: (state.messages[chatId] ?? []).map((m) =>
          m.clientId === clientId ? { ...m, status: "failed" } : m,
        ),
      },
    })),

  markSending: (chatId, clientId) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [chatId]: (state.messages[chatId] ?? []).map((m) =>
          m.clientId === clientId ? { ...m, status: "sending" } : m,
        ),
      },
    })),

  remove: (chatId, clientId) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [chatId]: (state.messages[chatId] ?? []).filter(
          (m) => m.clientId !== clientId,
        ),
      },
    })),
}));
