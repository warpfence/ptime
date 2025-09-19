'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LoginButton } from '@/components/auth';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    // 이미 인증된 사용자는 대시보드로 리다이렉트
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // 인증된 사용자인 경우 빈 화면 (리다이렉트 진행 중)
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 px-4">
      <div className="w-full max-w-md">
        <Card className="shadow-lg">
          <CardHeader className="text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-primary-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <CardTitle className="text-2xl font-bold">EngageNow</CardTitle>
            <CardDescription>
              실시간 청중 참여 플랫폼에 오신 것을 환영합니다
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center space-y-4">
              <p className="text-sm text-muted-foreground">
                Google 계정으로 간편하게 로그인하세요
              </p>
              <LoginButton className="w-full" size="lg" />
            </div>

            <div className="text-center">
              <p className="text-xs text-muted-foreground">
                로그인하면{' '}
                <a href="#" className="underline hover:text-primary">
                  이용약관
                </a>
                {' '}및{' '}
                <a href="#" className="underline hover:text-primary">
                  개인정보처리방침
                </a>
                에 동의하는 것으로 간주됩니다.
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground">
            세션에 참여하시나요?{' '}
            <a
              href="/join"
              className="text-primary hover:underline font-medium"
            >
              세션 참여하기
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}