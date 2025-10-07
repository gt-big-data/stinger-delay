import { ApiResponse } from '@/types/api';
import { API_BASE_URL } from '../constants/apiEndpoints';

/**
 * Generic API client wrapper for fetch requests.
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      ...options,
    });

    const data = await response.json();

    return {
      data,
      status: response.status,
      error: !response.ok ? data.message || 'Request failed' : undefined,
    };
  } catch (err) {
    console.error('API error:', err);
    return {
      data: null as unknown as T,
      status: 500,
      error: (err as Error).message,
    };
  }
}
