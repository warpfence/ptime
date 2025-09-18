# 프로젝트 구조 표준화

## 1. Next.js App Router 기반 폴더 구조

```
frontend/
├── app/                     # Next.js App Router
│   ├── (auth)/             # Route Groups - 인증 관련
│   │   ├── login/
│   │   └── callback/
│   ├── (dashboard)/        # Route Groups - 대시보드
│   │   ├── dashboard/
│   │   └── session/
│   ├── (public)/           # Route Groups - 공개 페이지
│   │   ├── join/
│   │   └── about/
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                 # Shadcn/ui 기본 컴포넌트
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── layout/             # 레이아웃 컴포넌트
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── auth/               # 인증 관련 컴포넌트
│   │   ├── LoginForm.tsx
│   │   ├── AuthGuard.tsx
│   │   └── UserMenu.tsx
│   ├── session/            # 세션 관련 컴포넌트
│   │   ├── SessionCard.tsx
│   │   ├── QRCodeDisplay.tsx
│   │   └── ParticipantList.tsx
│   ├── chat/               # 채팅 관련 컴포넌트
│   │   ├── ChatContainer.tsx
│   │   ├── ChatMessage.tsx
│   │   └── ChatInput.tsx
│   └── common/             # 공통 컴포넌트
│       ├── LoadingSpinner.tsx
│       ├── ErrorBoundary.tsx
│       └── Toast.tsx
├── lib/
│   ├── stores/             # Zustand 상태 관리
│   │   ├── auth.ts
│   │   ├── session.ts
│   │   └── theme.ts
│   ├── hooks/              # 커스텀 훅
│   │   ├── useSocket.ts
│   │   ├── useAuth.ts
│   │   └── useTheme.ts
│   ├── api/                # API 클라이언트
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   └── session.ts
│   ├── utils/              # 유틸리티 함수
│   │   ├── cn.ts
│   │   ├── formatters.ts
│   │   └── validators.ts
│   └── constants/          # 상수 정의
│       ├── routes.ts
│       ├── api-endpoints.ts
│       └── themes.ts
├── styles/
│   ├── globals.css
│   ├── components.css
│   └── themes/
│       ├── light.css
│       ├── dark.css
│       └── brand.css
└── types/
    ├── auth.ts
    ├── session.ts
    └── api.ts
```

## 2. 개발 표준 및 컨벤션

### 컴포넌트 명명 규칙
- **컴포넌트 파일**: PascalCase (예: `SessionCard.tsx`)
- **훅 파일**: camelCase with 'use' prefix (예: `useSocket.ts`)
- **유틸리티 파일**: camelCase (예: `formatDate.ts`)
- **상수 파일**: kebab-case (예: `api-endpoints.ts`)

### Import 순서 규칙
```typescript
// 1. React 관련
import React from 'react'
import { useState, useEffect } from 'react'

// 2. 외부 라이브러리
import { io } from 'socket.io-client'
import { create } from 'zustand'

// 3. 내부 컴포넌트
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

// 4. 훅과 유틸리티
import { useAuth } from '@/lib/hooks/useAuth'
import { cn } from '@/lib/utils/cn'

// 5. 타입 정의
import type { Session } from '@/types/session'
```