# 컴포넌트 개발 가이드라인

## 1. 컴포넌트 템플릿

### 기본 컴포넌트 구조

```typescript
// components/example/ExampleComponent.tsx
'use client'

import React from 'react'
import { cn } from '@/lib/utils/cn'
import type { ExampleProps } from '@/types/components'

interface ExampleComponentProps extends ExampleProps {
  className?: string
  children?: React.ReactNode
}

export function ExampleComponent({
  className,
  children,
  ...props
}: ExampleComponentProps) {
  return (
    <div className={cn("base-styles", className)} {...props}>
      {children}
    </div>
  )
}

// 기본 내보내기
ExampleComponent.displayName = 'ExampleComponent'
```

## 2. 에러 경계 및 로딩 상태

### components/common/ErrorBoundary.tsx

```typescript
'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle } from 'lucide-react'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      const { fallback: Fallback } = this.props

      if (Fallback) {
        return (
          <Fallback
            error={this.state.error!}
            reset={() => this.setState({ hasError: false, error: null })}
          />
        )
      }

      return (
        <Card className="max-w-md mx-auto mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle size={20} />
              오류가 발생했습니다
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {this.state.error?.message || '알 수 없는 오류가 발생했습니다.'}
            </p>
            <Button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="w-full"
            >
              다시 시도
            </Button>
          </CardContent>
        </Card>
      )
    }

    return this.props.children
  }
}
```

## 3. 개발 워크플로우

### 개발 시작 체크리스트
1. **환경 변수 확인**: `.env.local` 파일 설정
2. **의존성 설치**: `npm install`
3. **타입 검사**: `npm run type-check`
4. **린팅 확인**: `npm run lint`
5. **개발 서버 실행**: `npm run dev`

### 컴포넌트 개발 순서
1. **타입 정의**: `types/` 폴더에 인터페이스 정의
2. **기본 구조**: shadcn/ui 컴포넌트 활용하여 기본 UI 구성
3. **상태 관리**: 필요시 Zustand 스토어 생성
4. **데이터 연동**: API 클라이언트를 통한 서버 통신
5. **테마 적용**: CSS 변수 및 테마 시스템 활용
6. **에러 처리**: ErrorBoundary 및 적절한 fallback UI
7. **테스트**: 단위 테스트 및 스토리북 스토리 작성

### 코드 품질 유지
- **ESLint**: 코드 스타일 일관성
- **Prettier**: 코드 포매팅
- **TypeScript**: 타입 안전성
- **Husky**: Git hooks를 통한 자동 검사

## 4. 성능 최적화 가이드라인

### 번들 크기 최적화
- **동적 임포트**: 라우트별 코드 분할
- **트리 쉐이킹**: 사용하지 않는 코드 제거
- **이미지 최적화**: Next.js Image 컴포넌트 활용

### 렌더링 최적화
- **React.memo**: 불필요한 리렌더링 방지
- **useMemo/useCallback**: 복잡한 계산 및 함수 메모이제이션
- **Suspense**: 로딩 상태 관리