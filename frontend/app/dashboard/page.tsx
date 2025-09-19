'use client';

import { useState, useEffect } from 'react';
import { Plus, Users, Activity, Calendar, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AuthGuard } from '@/components/auth';
import { DashboardLayout, SessionList, CreateSessionDialog } from '@/components/dashboard';
import { Session, SessionStats, CreateSessionRequest } from '@/types/session';
import { useAuthStore } from '@/lib/stores/auth-store';

// 임시 데이터 (나중에 API로 대체)
const mockSessions: Session[] = [
  {
    id: '1',
    title: '2024 Q3 성과 발표',
    description: '3분기 성과 발표 및 Q4 계획 공유',
    session_code: 'ABC123',
    is_active: true,
    max_participants: 50,
    current_participants: 23,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    creator_id: 'user1',
  },
  {
    id: '2',
    title: '팀 미팅',
    description: '주간 팀 미팅 및 프로젝트 진행 상황 공유',
    session_code: 'DEF456',
    is_active: false,
    current_participants: 0,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    creator_id: 'user1',
  },
];

const mockStats: SessionStats = {
  total_sessions: 12,
  active_sessions: 2,
  total_participants: 145,
  recent_activity: 23,
};

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [sessions, setSessions] = useState<Session[]>(mockSessions);
  const [stats, setStats] = useState<SessionStats>(mockStats);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleCreateSession = async (data: CreateSessionRequest) => {
    try {
      setIsLoading(true);

      // TODO: API 호출로 대체
      const newSession: Session = {
        id: Math.random().toString(36).substr(2, 9),
        title: data.title,
        description: data.description,
        session_code: Math.random().toString(36).substr(2, 6).toUpperCase(),
        is_active: false,
        max_participants: data.max_participants,
        current_participants: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        creator_id: user?.id || '',
      };

      setSessions(prev => [newSession, ...prev]);
      setStats(prev => ({ ...prev, total_sessions: prev.total_sessions + 1 }));

      console.log('새 세션 생성:', newSession);
    } catch (error) {
      console.error('세션 생성 실패:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewSession = (session: Session) => {
    console.log('세션 보기:', session);
    // TODO: 세션 상세 페이지로 이동
  };

  const handleEditSession = (session: Session) => {
    console.log('세션 편집:', session);
    // TODO: 세션 편집 다이얼로그 열기
  };

  const handleToggleSession = (session: Session) => {
    setSessions(prev =>
      prev.map(s =>
        s.id === session.id ? { ...s, is_active: !s.is_active } : s
      )
    );
    console.log('세션 상태 토글:', session);
  };

  const handleDeleteSession = (session: Session) => {
    if (confirm('정말로 이 세션을 삭제하시겠습니까?')) {
      setSessions(prev => prev.filter(s => s.id !== session.id));
      setStats(prev => ({ ...prev, total_sessions: prev.total_sessions - 1 }));
      console.log('세션 삭제:', session);
    }
  };

  const handleShowQRCode = (session: Session) => {
    console.log('QR 코드 표시:', session);
    // TODO: QR 코드 다이얼로그 열기
  };

  return (
    <AuthGuard>
      <DashboardLayout>
        <div className="space-y-6">
          {/* 헤더 영역 */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">대시보드</h1>
              <p className="text-muted-foreground">
                {user?.name}님, 환영합니다! 세션을 관리하고 참여자와 소통하세요.
              </p>
            </div>
            <Button onClick={() => setIsCreateDialogOpen(true)} className="shrink-0">
              <Plus className="mr-2 h-4 w-4" />
              새 세션
            </Button>
          </div>

          {/* 통계 카드 */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">전체 세션</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_sessions}</div>
                <p className="text-xs text-muted-foreground">
                  생성한 모든 세션
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">활성 세션</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.active_sessions}</div>
                <p className="text-xs text-muted-foreground">
                  현재 진행 중인 세션
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">총 참여자</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_participants}</div>
                <p className="text-xs text-muted-foreground">
                  누적 참여자 수
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">최근 활동</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.recent_activity}</div>
                <p className="text-xs text-muted-foreground">
                  이번 주 새 참여자
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 세션 목록 */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold">내 세션</h2>
                <p className="text-sm text-muted-foreground">
                  생성한 세션을 관리하고 참여자와 소통하세요.
                </p>
              </div>
            </div>

            <SessionList
              sessions={sessions}
              loading={isLoading}
              onViewSession={handleViewSession}
              onEditSession={handleEditSession}
              onToggleSession={handleToggleSession}
              onDeleteSession={handleDeleteSession}
              onShowQRCode={handleShowQRCode}
            />
          </div>
        </div>

        {/* 세션 생성 다이얼로그 */}
        <CreateSessionDialog
          open={isCreateDialogOpen}
          onOpenChange={setIsCreateDialogOpen}
          onCreateSession={handleCreateSession}
        />
      </DashboardLayout>
    </AuthGuard>
  );
}