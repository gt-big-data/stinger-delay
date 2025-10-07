/**
 * Shared API request/response typing. Useful for feature APIs and error handling.
 */
export interface ApiRequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
}

export interface PaginatedResponse<T> {
  results: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ApiError {
  message: string;
  status?: number;
}
