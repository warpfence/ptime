'use client';

import { useState } from 'react';
import { LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/lib/stores/auth-store';

interface LogoutButtonProps {
  className?: string;
  variant?: 'default' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  showText?: boolean;
}

export function LogoutButton({
  className,
  variant = 'ghost',
  size = 'default',
  showText = true
}: LogoutButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      setIsLoading(true);

      // 백엔드 로그아웃 API 호출 (선택적)
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/logout`, {
          method: 'POST',
          credentials: 'include',
        });

        if (!response.ok) {
          console.warn('백엔드 로그아웃 실패, 로컬 로그아웃 진행');
        }
      } catch (error) {
        console.warn('백엔드 로그아웃 요청 실패, 로컬 로그아웃 진행:', error);
      }

      // 로컬 상태 정리
      logout();

      // 홈페이지로 리다이렉트
      window.location.href = '/';
    } catch (error) {
      console.error('로그아웃 오류:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      onClick={handleLogout}
      disabled={isLoading}
      variant={variant}
      size={size}
      className={className}
    >
      {isLoading ? (
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        <>
          <LogOut className={showText ? 'mr-2 h-4 w-4' : 'h-4 w-4'} />
          {showText && '로그아웃'}
        </>
      )}
    </Button>
  );
}