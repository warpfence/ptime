# Frontend 컴포넌트 템플릿

## 1. 인증 관련 컴포넌트

### 인증 상태 관리 스토어
#### lib/stores/auth.ts
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '../api'

interface User {
  id: string
  email: string
  name: string
  provider: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string, user: User) => void
  logout: () => void
  refreshToken: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: (token, user) => {
        apiClient.setToken(token)
        set({ token, user, isAuthenticated: true })
      },

      logout: () => {
        apiClient.setToken('')
        set({ token: null, user: null, isAuthenticated: false })
      },

      refreshToken: async () => {
        try {
          set({ isLoading: true })
          const response = await apiClient.refreshToken()
          get().login(response.access_token, response.user)
        } catch (error) {
          get().logout()
        } finally {
          set({ isLoading: false })
        }
      }
    }),
    { name: 'auth-storage' }
  )
)
```

### 로그인 버튼 컴포넌트
#### components/auth/LoginButton.tsx
```typescript
'use client'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api'

export function LoginButton() {
  const handleGoogleLogin = () => {
    apiClient.googleLogin()
  }

  return (
    <Button onClick={handleGoogleLogin} className="w-full" size="lg">
      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
        <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      Google로 로그인
    </Button>
  )
}
```

### 인증 가드 컴포넌트
#### components/auth/AuthGuard.tsx
```typescript
'use client'
import { useAuthStore } from '@/lib/stores/auth'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

interface AuthGuardProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function AuthGuard({ children, fallback }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">로그인이 필요합니다</h2>
          <p className="text-gray-600">서비스를 이용하려면 로그인해주세요.</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
```

## 2. 대시보드 컴포넌트

### 네비게이션 컴포넌트
#### components/dashboard/DashboardNav.tsx
```typescript
'use client'
import { useAuthStore } from '@/lib/stores/auth'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { LogOut, User } from 'lucide-react'

export function DashboardNav() {
  const { user, logout } = useAuthStore()

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-primary">EngageNow</h1>
          </div>

          <div className="flex items-center space-x-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center space-x-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>
                      {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden md:inline">{user?.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  프로필
                </DropdownMenuItem>
                <DropdownMenuItem onClick={logout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  로그아웃
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </nav>
  )
}
```

### 세션 목록 컴포넌트
#### components/dashboard/SessionList.tsx
```typescript
'use client'
import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { MoreVertical, Users, QrCode, Play, Square } from 'lucide-react'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { apiClient } from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface Session {
  id: string
  title: string
  description?: string
  session_code: string
  is_active: boolean
  participant_count: number
  created_at: string
}

interface SessionListProps {
  onCreateSession: () => void
  onViewSession: (sessionId: string) => void
}

export function SessionList({ onCreateSession, onViewSession }: SessionListProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const data = await apiClient.getSessions()
      setSessions(data)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleSessionStatus = async (sessionId: string, isActive: boolean) => {
    try {
      if (isActive) {
        await apiClient.deactivateSession(sessionId)
      } else {
        await apiClient.activateSession(sessionId)
      }
      await loadSessions()
    } catch (error) {
      console.error('Failed to toggle session status:', error)
    }
  }

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">내 세션</h1>
        <Button onClick={onCreateSession} size="lg">
          새 세션 만들기
        </Button>
      </div>

      {sessions.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <h3 className="text-lg font-semibold mb-2">아직 세션이 없습니다</h3>
            <p className="text-gray-600 mb-4">첫 번째 세션을 만들어보세요!</p>
            <Button onClick={onCreateSession}>세션 만들기</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sessions.map((session) => (
            <Card key={session.id} className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <span className="truncate">{session.title}</span>
                    <Badge variant={session.is_active ? "default" : "secondary"}>
                      {session.is_active ? '진행중' : '종료'}
                    </Badge>
                  </CardTitle>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onViewSession(session.id)}>
                        <QrCode className="mr-2 h-4 w-4" />
                        세션 관리
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => toggleSessionStatus(session.id, session.is_active)}
                      >
                        {session.is_active ? (
                          <>
                            <Square className="mr-2 h-4 w-4" />
                            세션 종료
                          </>
                        ) : (
                          <>
                            <Play className="mr-2 h-4 w-4" />
                            세션 시작
                          </>
                        )}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent onClick={() => onViewSession(session.id)}>
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {session.description || '설명이 없습니다.'}
                </p>

                <div className="flex items-center justify-between text-sm text-gray-500">
                  <div className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    <span>{session.participant_count}명 참여</span>
                  </div>
                  <span>{formatDate(session.created_at)}</span>
                </div>

                <div className="mt-3 p-2 bg-gray-50 rounded text-center">
                  <span className="text-xs text-gray-500">세션 코드</span>
                  <p className="font-mono font-bold text-lg">{session.session_code}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
```

### 세션 생성 다이얼로그
#### components/dashboard/CreateSessionDialog.tsx
```typescript
'use client'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { apiClient } from '@/lib/api'
import { validateSessionTitle } from '@/lib/utils'

interface CreateSessionDialogProps {
  trigger: React.ReactNode
  onSessionCreated: () => void
}

export function CreateSessionDialog({ trigger, onSessionCreated }: CreateSessionDialogProps) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: ''
  })
  const [errors, setErrors] = useState<{ [key: string]: string }>({})

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // 유효성 검사
    const titleError = validateSessionTitle(formData.title)
    if (titleError) {
      setErrors({ title: titleError })
      return
    }

    setLoading(true)
    setErrors({})

    try {
      await apiClient.createSession(formData)
      setFormData({ title: '', description: '' })
      setOpen(false)
      onSessionCreated()
    } catch (error) {
      setErrors({ general: error instanceof Error ? error.message : '세션 생성에 실패했습니다.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>새 세션 만들기</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">세션 제목 *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="세션 제목을 입력하세요"
              maxLength={100}
            />
            {errors.title && <p className="text-sm text-red-600">{errors.title}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">세션 설명</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="세션에 대한 간단한 설명 (선택사항)"
              rows={3}
              maxLength={500}
            />
          </div>

          {errors.general && (
            <p className="text-sm text-red-600">{errors.general}</p>
          )}

          <div className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={loading}
            >
              취소
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? '생성 중...' : '세션 생성'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

## 3. 세션 참여 컴포넌트

### 세션 참여 페이지
#### components/session/JoinSessionForm.tsx
```typescript
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import { validateNickname } from '@/lib/utils'

interface JoinSessionFormProps {
  sessionCode: string
}

export function JoinSessionForm({ sessionCode }: JoinSessionFormProps) {
  const [nickname, setNickname] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault()

    const validationError = validateNickname(nickname)
    if (validationError) {
      setError(validationError)
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await apiClient.joinSession(sessionCode, nickname.trim())

      // 세션 페이지로 이동
      router.push(`/session/${sessionCode}?participant=${response.participant.id}&nickname=${encodeURIComponent(nickname.trim())}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '참여에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">세션 참여</CardTitle>
          <p className="text-gray-600">닉네임을 입력해주세요</p>
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600">세션 코드</p>
            <p className="font-mono font-bold text-xl text-blue-600">{sessionCode}</p>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleJoin} className="space-y-4">
            <div>
              <Input
                type="text"
                placeholder="닉네임 (2-20글자)"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                maxLength={20}
                required
                className="text-center text-lg mobile-optimized"
                autoFocus
              />
            </div>

            {error && (
              <div className="text-red-600 text-sm text-center bg-red-50 p-2 rounded">
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={isLoading || nickname.trim().length < 2}
            >
              {isLoading ? '참여 중...' : '참여하기'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            <p>참여하면 실시간으로 세션에 연결됩니다</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
```

### 연결 상태 컴포넌트
#### components/session/ConnectionStatus.tsx
```typescript
import { Badge } from '@/components/ui/badge'
import { Users, Wifi, WifiOff } from 'lucide-react'

interface ConnectionStatusProps {
  isConnected: boolean
  participantCount: number
  className?: string
}

export function ConnectionStatus({ isConnected, participantCount, className }: ConnectionStatusProps) {
  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <Badge variant={isConnected ? "default" : "destructive"} className="flex items-center gap-1">
        {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
        {isConnected ? "연결됨" : "연결 끊어짐"}
      </Badge>

      <div className="flex items-center gap-1 text-sm">
        <Users className="h-4 w-4 text-gray-500" />
        <span className="font-medium">{participantCount}명</span>
        <span className="text-gray-500">참여중</span>
      </div>
    </div>
  )
}
```