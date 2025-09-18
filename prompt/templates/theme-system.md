# 테마 관리 시스템

## 1. CSS 변수 기반 테마 시스템

### globals.css - 기본 테마 변수

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* 기본 색상 시스템 */
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;

    /* 브랜드 색상 */
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 84% 4.9%;

    /* 상태 색상 */
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 84% 4.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;

    /* UI 요소 */
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;

    /* EngageNow 전용 색상 */
    --session-active: 142.1 76.2% 36.3%;
    --session-inactive: 210 40% 96%;
    --participant-online: 142.1 76.2% 36.3%;
    --chat-own: 221.2 83.2% 53.3%;
    --chat-other: 210 40% 96%;
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

    /* EngageNow Dark 전용 색상 */
    --session-active: 142.1 76.2% 36.3%;
    --session-inactive: 217.2 32.6% 17.5%;
    --participant-online: 142.1 76.2% 36.3%;
    --chat-own: 217.2 91.2% 59.8%;
    --chat-other: 217.2 32.6% 17.5%;
  }
}

/* 커스텀 유틸리티 클래스 */
@layer utilities {
  .session-active {
    @apply bg-session-active text-white;
  }

  .session-inactive {
    @apply bg-session-inactive text-muted-foreground;
  }

  .chat-message-own {
    @apply bg-chat-own text-white;
  }

  .chat-message-other {
    @apply bg-chat-other text-foreground;
  }
}
```

## 2. 테마 관리 스토어

### lib/stores/theme.ts

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type ThemeMode = 'light' | 'dark' | 'system'
type BrandTheme = 'default' | 'blue' | 'green' | 'purple'

interface ThemeState {
  mode: ThemeMode
  brand: BrandTheme
  setMode: (mode: ThemeMode) => void
  setBrand: (brand: BrandTheme) => void
  toggleMode: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      brand: 'default',

      setMode: (mode) => {
        set({ mode })
        applyTheme(mode, get().brand)
      },

      setBrand: (brand) => {
        set({ brand })
        applyTheme(get().mode, brand)
      },

      toggleMode: () => {
        const current = get().mode
        const next = current === 'light' ? 'dark' : 'light'
        get().setMode(next)
      }
    }),
    {
      name: 'engagenow-theme',
      onRehydrateStorage: () => (state) => {
        if (state) {
          applyTheme(state.mode, state.brand)
        }
      }
    }
  )
)

function applyTheme(mode: ThemeMode, brand: BrandTheme) {
  const root = document.documentElement

  // 다크모드 적용
  if (mode === 'dark') {
    root.classList.add('dark')
  } else if (mode === 'light') {
    root.classList.remove('dark')
  } else {
    // system 모드
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    root.classList.toggle('dark', isDark)
  }

  // 브랜드 테마 적용
  root.classList.remove('theme-default', 'theme-blue', 'theme-green', 'theme-purple')
  root.classList.add(`theme-${brand}`)
}
```

## 3. 테마 적용 훅

### lib/hooks/useTheme.ts

```typescript
import { useEffect } from 'react'
import { useThemeStore } from '@/lib/stores/theme'

export function useTheme() {
  const { mode, brand, setMode, setBrand, toggleMode } = useThemeStore()

  useEffect(() => {
    // 시스템 테마 변경 감지
    if (mode === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = () => {
        document.documentElement.classList.toggle('dark', mediaQuery.matches)
      }

      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [mode])

  return {
    mode,
    brand,
    setMode,
    setBrand,
    toggleMode,
    isDark: mode === 'dark' || (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  }
}
```