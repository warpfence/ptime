'use client';

import { useState } from 'react';
import { MoreVertical, Users, Eye, QrCode, Play, Pause, Trash2, Edit } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Session } from '@/types/session';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface SessionListProps {
  sessions: Session[];
  loading?: boolean;
  onViewSession?: (session: Session) => void;
  onEditSession?: (session: Session) => void;
  onToggleSession?: (session: Session) => void;
  onDeleteSession?: (session: Session) => void;
  onShowQRCode?: (session: Session) => void;
}

export function SessionList({
  sessions,
  loading = false,
  onViewSession,
  onEditSession,
  onToggleSession,
  onDeleteSession,
  onShowQRCode,
}: SessionListProps) {
  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-3">
              <div className="h-4 bg-muted rounded w-3/4"></div>
              <div className="h-3 bg-muted rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="h-3 bg-muted rounded"></div>
                <div className="h-3 bg-muted rounded w-2/3"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-24 h-24 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
          <Users className="w-12 h-12 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-2">아직 세션이 없습니다</h3>
        <p className="text-muted-foreground mb-6">
          첫 번째 세션을 생성하여 청중과 소통을 시작해보세요.
        </p>
        <Button>새 세션 만들기</Button>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {sessions.map((session) => (
        <SessionCard
          key={session.id}
          session={session}
          onView={onViewSession}
          onEdit={onEditSession}
          onToggle={onToggleSession}
          onDelete={onDeleteSession}
          onShowQRCode={onShowQRCode}
        />
      ))}
    </div>
  );
}

interface SessionCardProps {
  session: Session;
  onView?: (session: Session) => void;
  onEdit?: (session: Session) => void;
  onToggle?: (session: Session) => void;
  onDelete?: (session: Session) => void;
  onShowQRCode?: (session: Session) => void;
}

function SessionCard({
  session,
  onView,
  onEdit,
  onToggle,
  onDelete,
  onShowQRCode,
}: SessionCardProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleAction = (action: () => void) => {
    action();
    setIsMenuOpen(false);
  };

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold truncate">
              {session.title}
            </CardTitle>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={session.is_active ? 'default' : 'secondary'}>
                {session.is_active ? '활성' : '비활성'}
              </Badge>
              <span className="text-sm text-muted-foreground">
                코드: {session.session_code}
              </span>
            </div>
          </div>

          <DropdownMenu open={isMenuOpen} onOpenChange={setIsMenuOpen}>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleAction(() => onView?.(session))}>
                <Eye className="mr-2 h-4 w-4" />
                세션 보기
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleAction(() => onShowQRCode?.(session))}>
                <QrCode className="mr-2 h-4 w-4" />
                QR 코드
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => handleAction(() => onToggle?.(session))}>
                {session.is_active ? (
                  <>
                    <Pause className="mr-2 h-4 w-4" />
                    세션 중지
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    세션 시작
                  </>
                )}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleAction(() => onEdit?.(session))}>
                <Edit className="mr-2 h-4 w-4" />
                편집
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => handleAction(() => onDelete?.(session))}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                삭제
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent>
        {session.description && (
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
            {session.description}
          </p>
        )}

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">참여자</span>
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{session.current_participants}</span>
              {session.max_participants && (
                <span className="text-muted-foreground">/ {session.max_participants}</span>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">생성일</span>
            <span className="text-muted-foreground">
              {formatDistanceToNow(new Date(session.created_at), {
                addSuffix: true,
                locale: ko,
              })}
            </span>
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => onView?.(session)}
          >
            <Eye className="h-4 w-4 mr-1" />
            보기
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onShowQRCode?.(session)}
          >
            <QrCode className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}