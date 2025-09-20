"use client";

import { useSocketEvents } from '@/hooks/useSocketEvents';
import { Users, Eye, UserCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ParticipantCounterProps {
  showDetails?: boolean;
  className?: string;
}

export function ParticipantCounter({ showDetails = false, className }: ParticipantCounterProps) {
  const { participantCount } = useSocketEvents();

  if (!showDetails) {
    return (
      <Badge variant="outline" className={cn("flex items-center gap-1", className)}>
        <Users className="w-3 h-3" />
        <span className="text-xs">{participantCount.online}명 참여</span>
      </Badge>
    );
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* 전체 참여자 수 */}
      <Badge variant="secondary" className="flex items-center gap-1">
        <Users className="w-3 h-3" />
        <span className="text-xs">전체 {participantCount.total}명</span>
      </Badge>

      {/* 온라인 참여자 수 */}
      <Badge variant="default" className="flex items-center gap-1">
        <Eye className="w-3 h-3" />
        <span className="text-xs">온라인 {participantCount.online}명</span>
      </Badge>

      {/* 온라인 비율 표시 */}
      {participantCount.total > 0 && (
        <div className="flex items-center gap-1">
          <UserCheck className="w-3 h-3 text-green-600" />
          <span className="text-xs text-muted-foreground">
            {Math.round((participantCount.online / participantCount.total) * 100)}%
          </span>
        </div>
      )}
    </div>
  );
}