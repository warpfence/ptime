export interface Session {
  id: string;
  title: string;
  description?: string;
  session_code: string;
  qr_code?: string;
  is_active: boolean;
  max_participants?: number;
  current_participants: number;
  created_at: string;
  updated_at: string;
  creator_id: string;
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