'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/lib/stores/auth-store';

interface LoginButtonProps {
  className?: string;
  variant?: 'default' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

export function LoginButton({
  className,
  variant = 'default',
  size = 'default'
}: LoginButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { setLoading, setError } = useAuthStore();

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      setLoading(true);
      setError(null);

      // 백엔드에서 Google OAuth URL 가져오기
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login/google`);

      if (!response.ok) {
        throw new Error(`서버 오류: ${response.status}`);
      }

      const data = await response.json();

      if (data.authorization_url) {
        // Google OAuth URL로 리다이렉션
        window.location.href = data.authorization_url;
      } else {
        throw new Error('OAuth URL을 받아올 수 없습니다');
      }
    } catch (error) {
      console.error('로그인 오류:', error);
      setError(error instanceof Error ? error.message : '로그인에 실패했습니다');
      setIsLoading(false);
      setLoading(false);
    }
  };

  return (
    <Button
      onClick={handleGoogleLogin}
      disabled={isLoading}
      variant={variant}
      size={size}
      className={className}
    >
      {isLoading ? (
        <>
          <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          로그인 중...
        </>
      ) : (
        <>
          <svg
            className="mr-2 h-4 w-4"
            aria-hidden="true"
            focusable="false"
            data-prefix="fab"
            data-icon="google"
            role="img"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 488 512"
          >
            <path
              fill="currentColor"
              d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h240z"
            />
          </svg>
          Google로 로그인
        </>
      )}
    </Button>
  );
}