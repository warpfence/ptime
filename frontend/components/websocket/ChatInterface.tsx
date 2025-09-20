"use client";

import { useState, useRef, useEffect } from 'react';
import { useSocket } from '@/hooks/useSocket';
import { useSocketEvents, MessageData } from '@/hooks/useSocketEvents';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ConnectionStatus } from './ConnectionStatus';
import { ParticipantCounter } from './ParticipantCounter';
import { Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface ChatInterfaceProps {
  sessionId: string;
  participantId: string;
  nickname: string;
  className?: string;
  autoConnect?: boolean;
}

export function ChatInterface({
  sessionId,
  participantId,
  nickname,
  className,
  autoConnect = true
}: ChatInterfaceProps) {
  const [messageInput, setMessageInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isJoined, setIsJoined] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { connectionStatus, connect, joinSession, sendMessage, disconnect } = useSocket();
  const { messages, clearMessages } = useSocketEvents({
    onMessage: (message) => {
      console.log('새 메시지:', message);
    },
    onSessionJoined: (data) => {
      console.log('세션 참여 성공:', data);
      setIsJoined(true);
    },
    onError: (error) => {
      console.error('Socket 에러:', error);
    }
  });

  // 자동 연결 및 세션 참여
  useEffect(() => {
    if (autoConnect && !connectionStatus.isConnected && !connectionStatus.isConnecting) {
      connect();
    }
  }, [autoConnect, connectionStatus, connect]);

  useEffect(() => {
    if (connectionStatus.isConnected && !isJoined && sessionId && participantId && nickname) {
      const success = joinSession(sessionId, participantId, nickname);
      if (success) {
        console.log('세션 참여 요청 전송');
      }
    }
  }, [connectionStatus.isConnected, isJoined, sessionId, participantId, nickname, joinSession]);

  // 메시지 목록 하단으로 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 메시지 전송 핸들러
  const handleSendMessage = async () => {
    if (!messageInput.trim() || isSending || !connectionStatus.isConnected) {
      return;
    }

    setIsSending(true);
    const success = sendMessage(messageInput.trim());

    if (success) {
      setMessageInput('');
      inputRef.current?.focus();
    }

    setIsSending(false);
  };

  // Enter 키로 메시지 전송
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 시간 포맷팅
  const formatMessageTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return formatDistanceToNow(date, { addSuffix: true, locale: ko });
    } catch {
      return '방금 전';
    }
  };

  // 메시지 컴포넌트
  const MessageItem = ({ message }: { message: MessageData }) => {
    const isMyMessage = message.participant_id === participantId;

    return (
      <div className={cn(
        "flex gap-2 mb-4",
        isMyMessage ? "justify-end" : "justify-start"
      )}>
        {!isMyMessage && (
          <Avatar className="w-8 h-8">
            <AvatarFallback className="text-xs">
              {message.nickname.charAt(0)}
            </AvatarFallback>
          </Avatar>
        )}

        <div className={cn(
          "max-w-[70%]",
          isMyMessage ? "text-right" : "text-left"
        )}>
          {!isMyMessage && (
            <div className="text-xs text-muted-foreground mb-1">
              {message.nickname}
            </div>
          )}

          <div className={cn(
            "inline-block px-3 py-2 rounded-lg text-sm",
            isMyMessage
              ? "bg-primary text-primary-foreground"
              : "bg-muted"
          )}>
            {message.message}
          </div>

          <div className="text-xs text-muted-foreground mt-1">
            {formatMessageTime(message.timestamp)}
          </div>
        </div>

        {isMyMessage && (
          <Avatar className="w-8 h-8">
            <AvatarFallback className="text-xs">
              {nickname.charAt(0)}
            </AvatarFallback>
          </Avatar>
        )}
      </div>
    );
  };

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">실시간 채팅</h3>
          <ParticipantCounter showDetails />
        </div>
        <ConnectionStatus />
      </div>

      {/* 메시지 목록 */}
      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            아직 메시지가 없습니다.<br />
            첫 번째 메시지를 보내보세요!
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageItem key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      {/* 메시지 입력 */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              connectionStatus.isConnected
                ? "메시지를 입력하세요..."
                : "연결을 기다리는 중..."
            }
            disabled={!connectionStatus.isConnected || isSending}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!connectionStatus.isConnected || !messageInput.trim() || isSending}
            size="sm"
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>

        {!connectionStatus.isConnected && (
          <div className="text-xs text-muted-foreground mt-2">
            실시간 채팅을 사용하려면 인터넷 연결이 필요합니다.
          </div>
        )}
      </div>
    </div>
  );
}