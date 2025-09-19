'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  BarChart3,
  Settings,
  HelpCircle,
  Calendar
} from 'lucide-react';

const navigation = [
  {
    name: '대시보드',
    href: '/dashboard',
    icon: LayoutDashboard,
    current: false,
  },
  {
    name: '내 세션',
    href: '/dashboard/sessions',
    icon: Users,
    current: false,
  },
  {
    name: '실시간 채팅',
    href: '/dashboard/chat',
    icon: MessageSquare,
    current: false,
  },
  {
    name: '분석',
    href: '/dashboard/analytics',
    icon: BarChart3,
    current: false,
  },
  {
    name: '일정',
    href: '/dashboard/calendar',
    icon: Calendar,
    current: false,
  },
];

const secondaryNavigation = [
  {
    name: '설정',
    href: '/dashboard/settings',
    icon: Settings,
  },
  {
    name: '도움말',
    href: '/dashboard/help',
    icon: HelpCircle,
  },
];

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 lg:pt-16 lg:bg-background lg:border-r">
      <div className="flex flex-col flex-grow overflow-y-auto">
        {/* 주요 네비게이션 */}
        <div className="flex-1 px-4 py-6 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                )}
              >
                <item.icon
                  className={cn(
                    "mr-3 h-5 w-5 flex-shrink-0",
                    isActive ? "text-primary-foreground" : "text-muted-foreground"
                  )}
                />
                {item.name}
              </Link>
            );
          })}
        </div>

        {/* 보조 네비게이션 */}
        <div className="px-4 py-6 border-t border-border">
          <div className="space-y-1">
            {secondaryNavigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent"
                  )}
                >
                  <item.icon
                    className={cn(
                      "mr-3 h-5 w-5 flex-shrink-0",
                      isActive ? "text-primary-foreground" : "text-muted-foreground"
                    )}
                  />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>

        {/* 하단 정보 */}
        <div className="px-4 py-4 bg-muted/20">
          <div className="text-xs text-muted-foreground text-center">
            <p>EngageNow v1.0</p>
            <p className="mt-1">© 2024 All rights reserved</p>
          </div>
        </div>
      </div>
    </nav>
  );
}