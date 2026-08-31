import { apiClient } from "./client";
import type {
  BotLogQueryParams,
  BotLogViewModel,
  CursorPaginatedResponse,
} from "@/types/api";

export const logsApi = {
  listLogs(botId: string, params: BotLogQueryParams = {}) {
    return apiClient.get<CursorPaginatedResponse<BotLogViewModel>>(
      `/v1/bots/${botId}/logs`,
      {
        params,
        // `level` is repeatable (?level=ERROR&level=CRITICAL); the default
        // serializer would send `level[]=` instead, which FastAPI rejects.
        paramsSerializer: { indexes: null },
      },
    );
  },
};
