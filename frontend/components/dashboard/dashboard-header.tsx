'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Menu, Bell, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { UserProfile } from '@/components/auth';
import { CreateSessionDialog } from './create-session-dialog';

export function DashboardHeader() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          {/* 왼쪽: 로고 및 모바일 메뉴 */}
          <div className="flex items-center gap-4">
            {/* 모바일 메뉴 토글 */}
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              <Menu className="h-5 w-5" />
            </Button>

            {/* 로고 */}
            <Link href="/dashboard" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">EN</span>
              </div>
              <span className="font-bold text-xl">EngageNow</span>
            </Link>
          </div>

          {/* 오른쪽: 액션 버튼들 */}
          <div className="flex items-center gap-3">
            {/* 세션 생성 버튼 */}
            <Button
              onClick={() => setIsCreateDialogOpen(true)}
              className="hidden sm:flex"
            >
              <Plus className="h-4 w-4 mr-2" />
              새 세션
            </Button>

            {/* 모바일용 세션 생성 버튼 */}
            <Button
              size="icon"
              onClick={() => setIsCreateDialogOpen(true)}
              className="sm:hidden"
            >
              <Plus className="h-4 w-4" />
            </Button>

            {/* 알림 버튼 */}
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              {/* 알림 배지 (예시) */}
              <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full text-xs"></span>
            </Button>

            {/* 사용자 프로필 */}
            <UserProfile />
          </div>
        </div>

        {/* 모바일 메뉴 */}
        {isMobileMenuOpen && (
          <div className="lg:hidden border-t bg-background/95 backdrop-blur">
            <nav className="container mx-auto px-4 py-4">
              <div className="space-y-2">
                <Link
                  href="/dashboard"
                  className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  대시보드
                </Link>
                <Link
                  href="/dashboard/sessions"
                  className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  내 세션
                </Link>
                <Link
                  href="/dashboard/analytics"
                  className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  분석
                </Link>
                <Link
                  href="/dashboard/settings"
                  className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  설정
                </Link>
              </div>
            </nav>
          </div>
        )}
      </header>

      {/* 세션 생성 다이얼로그 */}
      <CreateSessionDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
      />
    </>
  );
}