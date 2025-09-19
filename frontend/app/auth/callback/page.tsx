'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/auth-store';
import AuthService from '@/lib/services/auth-service';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, setError, setLoading } = useAuthStore();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        setLoading(true);
        setError(null);

        // URL에서 토큰 파라미터 추출
        const accessToken = searchParams.get('access_token');
        const tokenType = searchParams.get('token_type');
        const expiresIn = searchParams.get('expires_in');

        // 에러 파라미터 확인
        const error = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');

        if (error) {
          throw new Error(errorDescription || '로그인에 실패했습니다');
        }

        if (!accessToken || !tokenType || !expiresIn) {
          throw new Error('인증 토큰이 올바르지 않습니다');
        }

        const tokens = {
          access_token: accessToken,
          token_type: tokenType,
          expires_in: parseInt(expiresIn, 10),
        };

        // 토큰으로 사용자 정보 조회
        const user = await AuthService.getCurrentUser();

        // 인증 상태 업데이트
        login(tokens, user);
        setStatus('success');

        // 대시보드로 리다이렉트
        setTimeout(() => {
          router.push('/dashboard');
        }, 1500);

      } catch (error) {
        console.error('OAuth 콜백 처리 오류:', error);
        const errorMessage = error instanceof Error ? error.message : '로그인에 실패했습니다';
        setError(errorMessage);
        setStatus('error');

        // 에러 발생시 로그인 페이지로 리다이렉트
        setTimeout(() => {
          router.push('/auth/login');
        }, 3000);
      } finally {
        setLoading(false);
      }
    };

    handleCallback();
  }, [searchParams, login, setError, setLoading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 px-4">
      <div className="w-full max-w-md text-center">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          {status === 'processing' && (
            <>
              <div className="mx-auto w-16 h-16 mb-4">
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary border-t-transparent"></div>
              </div>
              <h2 className="text-xl font-semibold mb-2">로그인 처리 중</h2>
              <p className="text-muted-foreground">
                Google 인증을 완료하고 있습니다...
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="mx-auto w-16 h-16 mb-4 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-green-600 dark:text-green-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2 text-green-600 dark:text-green-400">
                로그인 성공
              </h2>
              <p className="text-muted-foreground">
                대시보드로 이동합니다...
              </p>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="mx-auto w-16 h-16 mb-4 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-red-600 dark:text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2 text-red-600 dark:text-red-400">
                로그인 실패
              </h2>
              <p className="text-muted-foreground mb-4">
                로그인 페이지로 돌아갑니다...
              </p>
              <button
                onClick={() => router.push('/auth/login')}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                다시 시도
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}