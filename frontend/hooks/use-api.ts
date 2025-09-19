import React, { useState, useCallback } from 'react';
import { ApiError } from '@/lib/api-client';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  execute: (...args: any[]) => Promise<T>;
  reset: () => void;
}

export function useApi<T>(
  apiFunction: (...args: any[]) => Promise<T>
): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: any[]): Promise<T> => {
      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const result = await apiFunction(...args);
        setState(prev => ({ ...prev, data: result, loading: false }));
        return result;
      } catch (error) {
        const errorMessage =
          error instanceof ApiError
            ? error.message
            : error instanceof Error
            ? error.message
            : '알 수 없는 오류가 발생했습니다';

        setState(prev => ({ ...prev, error: errorMessage, loading: false }));
        throw error;
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

// 즉시 실행되는 API 훅
export function useApiEffect<T>(
  apiFunction: () => Promise<T>,
  dependencies: React.DependencyList = []
): UseApiState<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const execute = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await apiFunction();
      setState({ data: result, loading: false, error: null });
    } catch (error) {
      const errorMessage =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
          ? error.message
          : '알 수 없는 오류가 발생했습니다';

      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
    }
  }, dependencies);

  // useEffect 대신 직접 실행
  React.useEffect(() => {
    execute();
  }, [execute]);

  return state;
}