# Frontend 설정 템플릿

## 1. Next.js 프로젝트 설정

### package.json
```json
{
  "name": "engagenow-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-button": "^2.0.3",
    "@radix-ui/react-card": "^1.0.4",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-input": "^1.0.4",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-scroll-area": "^1.0.5",
    "@radix-ui/react-separator": "^1.0.3",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "socket.io-client": "^4.7.4",
    "zustand": "^4.4.7",
    "qrcode": "^1.5.3",
    "@types/qrcode": "^1.5.5",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10",
    "postcss": "^8",
    "tailwindcss": "^3",
    "eslint": "^8",
    "eslint-config-next": "14.0.0",
    "@playwright/test": "^1.40.0",
    "jest": "^29.7.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^6.1.4"
  }
}
```

## 2. 프로젝트 구조

```
frontend/
├── app/                 # Next.js 13+ App Router
│   ├── layout.tsx       # 전역 레이아웃
│   ├── page.tsx         # 홈페이지
│   ├── globals.css      # 전역 스타일
│   ├── auth/            # 인증 관련 페이지
│   │   ├── login/
│   │   └── callback/
│   ├── dashboard/       # 발표자 대시보드
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── join/            # 세션 참여 페이지
│   │   └── [sessionCode]/
│   └── session/         # 세션 관련 페이지
│       └── [sessionCode]/
├── components/          # 재사용 가능한 컴포넌트
│   ├── ui/              # Shadcn UI 컴포넌트
│   ├── auth/            # 인증 관련 컴포넌트
│   ├── dashboard/       # 대시보드 컴포넌트
│   ├── session/         # 세션 관련 컴포넌트
│   └── chat/            # 채팅 관련 컴포넌트
├── lib/                 # 유틸리티 라이브러리
│   ├── utils.ts         # 공통 유틸리티
│   ├── stores/          # Zustand 스토어
│   └── api.ts           # API 클라이언트
├── hooks/               # 커스텀 React Hook
├── types/               # TypeScript 타입 정의
└── public/              # 정적 파일
```

## 3. Tailwind CSS 설정

### tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

## 4. 환경 설정

### next.config.js
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WEBSOCKET_URL: process.env.NEXT_PUBLIC_WEBSOCKET_URL,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
```

### .env.local (예시)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=http://localhost:8000
```

## 5. 글로벌 스타일

### app/globals.css
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 84% 4.9%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 84% 4.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 84% 4.9%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 94.1%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

/* 모바일 최적화 */
@media (max-width: 640px) {
  .mobile-optimized input {
    font-size: 16px; /* iOS 확대 방지 */
  }
}

/* 커스텀 스크롤바 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(155, 155, 155, 0.5);
  border-radius: 20px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(155, 155, 155, 0.7);
}
```

## 6. 공통 유틸리티

### lib/utils.ts
```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string) {
  const d = new Date(date)
  return d.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatTime(date: Date | string) {
  const d = new Date(date)
  return d.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function generateRandomId() {
  return Math.random().toString(36).substr(2, 9)
}

export function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
}

export function validateNickname(nickname: string): string | null {
  if (!nickname.trim()) {
    return '닉네임을 입력해주세요.'
  }
  if (nickname.trim().length < 2) {
    return '닉네임은 2글자 이상이어야 합니다.'
  }
  if (nickname.trim().length > 20) {
    return '닉네임은 20글자 이하여야 합니다.'
  }
  return null
}

export function validateSessionTitle(title: string): string | null {
  if (!title.trim()) {
    return '세션 제목을 입력해주세요.'
  }
  if (title.trim().length < 2) {
    return '제목은 2글자 이상이어야 합니다.'
  }
  if (title.trim().length > 100) {
    return '제목은 100글자 이하여야 합니다.'
  }
  return null
}
```

## 7. API 클라이언트

### lib/api.ts
```typescript
class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  setToken(token: string) {
    this.token = token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {})
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(url, {
      ...options,
      headers
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP Error: ${response.status}`)
    }

    return response.json()
  }

  // Auth methods
  async googleLogin() {
    window.location.href = `${this.baseUrl}/auth/login/google`
  }

  async refreshToken(): Promise<{ access_token: string; user: any }> {
    return this.request('/auth/refresh', { method: 'POST' })
  }

  // Session methods
  async createSession(data: { title: string; description?: string }) {
    return this.request('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async getSessions() {
    return this.request('/api/sessions')
  }

  async getSession(sessionId: string) {
    return this.request(`/api/sessions/${sessionId}`)
  }

  async updateSession(sessionId: string, data: any) {
    return this.request(`/api/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  async deleteSession(sessionId: string) {
    return this.request(`/api/sessions/${sessionId}`, { method: 'DELETE' })
  }

  async activateSession(sessionId: string) {
    return this.request(`/api/sessions/${sessionId}/activate`, { method: 'POST' })
  }

  async deactivateSession(sessionId: string) {
    return this.request(`/api/sessions/${sessionId}/deactivate`, { method: 'POST' })
  }

  // Participant methods
  async joinSession(sessionCode: string, nickname: string) {
    return this.request(`/api/join/${sessionCode}`, {
      method: 'POST',
      body: JSON.stringify({ nickname })
    })
  }
}

export const apiClient = new ApiClient()
```