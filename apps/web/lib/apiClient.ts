import { createApiClient } from "@codemindai/api-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

export const apiClient = createApiClient(API_URL);
export { API_URL };
