'use client';

import { ReactNode } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles?: string[];
  fallback?: ReactNode;
}

export function RoleGuard({
  children,
  allowedRoles = [],
  fallback
}: RoleGuardProps) {
  const { user, isAuthenticated } = useAuthStore();

  // 인증되지 않은 경우
  if (!isAuthenticated || !user) {
    return fallback || <div>접근 권한이 없습니다.</div>;
  }

  // 특정 역할이 필요한 경우 확인
  if (allowedRoles.length > 0) {
    // user 객체에 role 필드가 추가되면 여기서 체크
    // const userRole = user.role;
    // const hasPermission = allowedRoles.includes(userRole);

    // 현재는 모든 인증된 사용자에게 권한 부여
    // if (!hasPermission) {
    //   return fallback || <div>이 기능에 대한 권한이 없습니다.</div>;
    // }
  }

  return <>{children}</>;
}