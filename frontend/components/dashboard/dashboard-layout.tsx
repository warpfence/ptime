'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { DashboardNav } from './dashboard-nav';
import { DashboardHeader } from './dashboard-header';

interface DashboardLayoutProps {
  children: ReactNode;
  className?: string;
}

export function DashboardLayout({ children, className }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      {/* 헤더 */}
      <DashboardHeader />

      {/* 메인 컨테이너 */}
      <div className="flex">
        {/* 사이드 네비게이션 */}
        <DashboardNav />

        {/* 메인 콘텐츠 */}
        <main className={cn(
          "flex-1 p-6 lg:p-8",
          "ml-0 lg:ml-64", // 데스크톱에서 사이드바 공간 확보
          className
        )}>
          {children}
        </main>
      </div>
    </div>
  );
}