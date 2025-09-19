'use client';

import { useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/auth-store';

interface AuthGuardProps {
  children: ReactNode;
  redirectTo?: string;
  fallback?: ReactNode;
}

export function AuthGuard({
  children,
  redirectTo = '/auth/login',
  fallback
}: AuthGuardProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    // 컴포넌트 마운트 시 인증 상태 확인
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    // 인증되지 않은 경우 리다이렉트
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, isLoading, router, redirectTo]);

  // 로딩 중일 때 표시할 컴포넌트
  if (isLoading) {
    return (
      fallback || (
        <div className="flex items-center justify-center min-h-screen">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="text-sm text-muted-foreground">인증 확인 중...</p>
          </div>
        </div>
      )
    );
  }

  // 인증되지 않은 경우 빈 컴포넌트 반환 (리다이렉트 진행 중)
  if (!isAuthenticated) {
    return null;
  }

  // 인증된 경우 자식 컴포넌트 렌더링
  return <>{children}</>;
}