export interface Session {
  id: string;
  title: string;
  description?: string;
  session_code: string;
  qr_code_url?: string;
  is_active: boolean;
  participant_count: number;
  created_at: string;
  started_at?: string;
  ended_at?: string;
}

export interface CreateSessionRequest {
  title: string;
  description?: string;
  max_participants?: number;
}

export interface UpdateSessionRequest {
  title?: string;
  description?: string;
  max_participants?: number;
  is_active?: boolean;
}

export interface SessionStats {
  total_sessions: number;
  active_sessions: number;
  total_participants: number;
  recent_activity: number;
}