"use client";

import { useSocket } from '@/hooks/useSocket';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Wifi, WifiOff, RotateCcw, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConnectionStatusProps {
  showReconnectButton?: boolean;
  className?: string;
}

export function ConnectionStatus({ showReconnectButton = true, className }: ConnectionStatusProps) {
  const { connectionStatus, reconnect } = useSocket();

  const getStatusColor = () => {
    if (connectionStatus.isConnecting) return 'bg-yellow-500';
    if (connectionStatus.isConnected) return 'bg-green-500';
    return 'bg-red-500';
  };

  const getStatusText = () => {
    if (connectionStatus.isConnecting) return '연결 중...';
    if (connectionStatus.isConnected) return '연결됨';
    return '연결 끊김';
  };

  const getStatusIcon = () => {
    if (connectionStatus.isConnecting) {
      return <Loader2 className="w-3 h-3 animate-spin" />;
    }
    if (connectionStatus.isConnected) {
      return <Wifi className="w-3 h-3" />;
    }
    return <WifiOff className="w-3 h-3" />;
  };

  const getStatusVariant = (): "default" | "secondary" | "destructive" | "outline" => {
    if (connectionStatus.isConnecting) return 'secondary';
    if (connectionStatus.isConnected) return 'default';
    return 'destructive';
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Badge variant={getStatusVariant()} className="flex items-center gap-1">
        {getStatusIcon()}
        <span className="text-xs">{getStatusText()}</span>
      </Badge>

      {/* 연결 상태 표시등 */}
      <div className="flex items-center gap-1">
        <div
          className={cn(
            "w-2 h-2 rounded-full transition-colors duration-300",
            getStatusColor()
          )}
        />
        <span className="text-xs text-muted-foreground">
          {connectionStatus.isConnected ? '실시간' : '오프라인'}
        </span>
      </div>

      {/* 에러 표시 */}
      {connectionStatus.error && (
        <div className="flex items-center gap-1 text-destructive">
          <AlertCircle className="w-3 h-3" />
          <span className="text-xs">{connectionStatus.error}</span>
        </div>
      )}

      {/* 재시도 횟수 표시 */}
      {connectionStatus.retryCount > 0 && !connectionStatus.isConnected && (
        <span className="text-xs text-muted-foreground">
          재시도 {connectionStatus.retryCount}회
        </span>
      )}

      {/* 재연결 버튼 */}
      {showReconnectButton && !connectionStatus.isConnected && !connectionStatus.isConnecting && (
        <Button
          size="sm"
          variant="outline"
          onClick={reconnect}
          className="h-6 px-2 text-xs"
        >
          <RotateCcw className="w-3 h-3 mr-1" />
          재연결
        </Button>
      )}
    </div>
  );
}