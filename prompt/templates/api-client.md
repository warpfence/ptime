# API 클라이언트 표준화

## 1. 타입 안전한 API 클라이언트

### lib/api/client.ts

```typescript
import type {
  ApiResponse,
  PaginatedResponse,
  Session,
  SessionCreate,
  Participant
} from '@/types/api'

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  setAuthToken(token: string) {
    this.token = token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {})
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || `HTTP Error: ${response.status}`)
      }

      return { data, error: null, status: response.status }
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : 'Unknown error',
        status: 0
      }
    }
  }

  // Auth methods
  async googleLogin() {
    window.location.href = `${this.baseUrl}/auth/login/google`
  }

  async refreshToken() {
    const result = await this.request<{ access_token: string; user: any }>('/auth/refresh', {
      method: 'POST'
    })

    if (result.error) {
      throw new Error(result.error)
    }

    return result.data!
  }

  // Session methods
  async createSession(data: SessionCreate) {
    return this.request<Session>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  async getSessions() {
    return this.request<Session[]>('/api/sessions')
  }

  async getSession(sessionId: string) {
    return this.request<Session>(`/api/sessions/${sessionId}`)
  }

  async joinSession(sessionCode: string, nickname: string) {
    return this.request<{ participant: Participant; session: Session }>(`/api/join/${sessionCode}`, {
      method: 'POST',
      body: JSON.stringify({ nickname })
    })
  }
}

export const apiClient = new ApiClient()
```