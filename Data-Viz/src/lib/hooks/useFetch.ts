import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

export function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    apiClient<T>(url)
      .then((res) => {
        if (!isMounted) return;
        if (res.error) setError(res.error);
        else setData(res.data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));

    return () => {
      isMounted = false;
    };
  }, [url]);

  return { data, loading, error };
}
