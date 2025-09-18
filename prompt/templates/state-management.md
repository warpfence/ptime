# 상태 관리 표준화

## 1. Zustand 스토어 구조

### lib/stores/auth.ts

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '@/lib/api/client'
import type { User, AuthState } from '@/types/auth'

interface AuthStore extends AuthState {
  // Actions
  login: (token: string, user: User) => void
  logout: () => void
  refreshToken: () => Promise<void>
  updateUser: (user: Partial<User>) => void

  // Computed
  isAuthenticated: boolean
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      get isAuthenticated() {
        return !!get().token && !!get().user
      },

      login: (token, user) => {
        apiClient.setAuthToken(token)
        set({ token, user, error: null })
      },

      logout: () => {
        apiClient.setAuthToken('')
        set({ token: null, user: null, error: null })
      },

      refreshToken: async () => {
        try {
          set({ isLoading: true })
          const response = await apiClient.refreshToken()
          get().login(response.access_token, response.user)
        } catch (error) {
          get().logout()
          set({ error: error instanceof Error ? error.message : 'Unknown error' })
        } finally {
          set({ isLoading: false })
        }
      },

      updateUser: (userData) => {
        const currentUser = get().user
        if (currentUser) {
          set({ user: { ...currentUser, ...userData } })
        }
      }
    }),
    {
      name: 'engagenow-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user
      })
    }
  )
)
```