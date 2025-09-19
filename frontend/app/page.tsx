'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/stores/auth-store';
import { LoginButton, UserProfile } from '@/components/auth';
import { Button } from '@/components/ui/button';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const handleDashboardClick = () => {
    if (isAuthenticated) {
      router.push('/dashboard');
    } else {
      router.push('/auth/login');
    }
  };

  return (
    <main className="flex min-h-screen flex-col">
      {/* 헤더 */}
      <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">EngageNow</h1>
          <div className="flex items-center gap-4">
            {isAuthenticated && user ? (
              <UserProfile />
            ) : (
              <LoginButton variant="outline" />
            )}
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-4xl w-full text-center">
          <div className="mb-8">
            <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent leading-tight">
              EngageNow
            </h1>
            <p className="text-xl text-muted-foreground mb-4">
              실시간 청중 참여 플랫폼
            </p>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              QR 코드 하나로 간편하게 세션을 시작하고,
              실시간 채팅과 Q&A를 통해 청중과 소통하세요.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-2xl mx-auto">
            {/* 발표자 카드 */}
            <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg
                    className="w-6 h-6 text-primary-foreground"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">발표자</h3>
                <p className="text-muted-foreground text-sm">
                  세션을 생성하고 청중과 실시간으로 소통하세요
                </p>
              </div>
              <Button
                onClick={handleDashboardClick}
                className="w-full"
                size="lg"
              >
                {isAuthenticated ? '대시보드로 이동' : '로그인하고 시작하기'}
              </Button>
            </div>

            {/* 참여자 카드 */}
            <div className="bg-card text-card-foreground rounded-lg border p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <div className="w-12 h-12 bg-secondary rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg
                    className="w-6 h-6 text-secondary-foreground"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">참여자</h3>
                <p className="text-muted-foreground text-sm">
                  QR 코드를 스캔하거나 세션 코드로 참여하세요
                </p>
              </div>
              <Button
                asChild
                variant="outline"
                className="w-full"
                size="lg"
              >
                <Link href="/join">
                  세션 참여하기
                </Link>
              </Button>
            </div>
          </div>

          {/* 특징 섹션 */}
          <div className="mt-16 grid md:grid-cols-3 gap-8 text-left">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg
                  className="w-4 h-4 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <div>
                <h4 className="font-semibold mb-2">간편한 시작</h4>
                <p className="text-sm text-muted-foreground">
                  Google 로그인으로 즉시 세션 생성
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg
                  className="w-4 h-4 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <rect width="14" height="20" x="5" y="2" rx="2" ry="2" />
                  <path d="M12 18h.01" />
                </svg>
              </div>
              <div>
                <h4 className="font-semibold mb-2">모바일 최적화</h4>
                <p className="text-sm text-muted-foreground">
                  QR 코드 스캔으로 모바일에서 쉽게 참여
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg
                  className="w-4 h-4 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z" />
                </svg>
              </div>
              <div>
                <h4 className="font-semibold mb-2">실시간 소통</h4>
                <p className="text-sm text-muted-foreground">
                  채팅과 Q&A로 실시간 상호작용
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}