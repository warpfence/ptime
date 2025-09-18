# 채팅 시스템 컴포넌트 템플릿

## 1. WebSocket Hook

### hooks/useSocket.ts
```typescript
import { useEffect, useRef, useState, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

interface UseSocketProps {
  sessionId?: string
  participantId?: string
  nickname?: string
  role?: 'participant' | 'presenter'
}

interface SocketEvents {
  onMessage?: (message: any) => void
  onParticipantUpdate?: (count: number) => void
  onError?: (error: string) => void
}

export function useSocket({ sessionId, participantId, nickname, role = 'participant' }: UseSocketProps) {
  const socketRef = useRef<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [participantCount, setParticipantCount] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (socketRef.current?.connected) return

    const socketUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:8000'

    socketRef.current = io(socketUrl, {
      transports: ['websocket', 'polling'],
      timeout: 10000,
      reconnection: true,
      reconnectionAttempts: maxReconnectAttempts,
      reconnectionDelay: 1000,
    })

    const socket = socketRef.current

    // 연결 이벤트
    socket.on('connect', () => {
      setIsConnected(true)
      setError(null)
      reconnectAttempts.current = 0

      // 세션 참여
      if (sessionId && nickname) {
        socket.emit('join_session', {
          session_id: sessionId,
          participant_id: participantId,
          nickname: nickname,
          role: role
        })
      }
    })

    socket.on('disconnect', (reason) => {
      setIsConnected(false)
      if (reason === 'io server disconnect') {
        // 서버가 연결을 끊었을 때는 수동으로 재연결
        socket.connect()
      }
    })

    socket.on('connect_error', (error) => {
      setIsConnected(false)
      reconnectAttempts.current++

      if (reconnectAttempts.current >= maxReconnectAttempts) {
        setError('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.')
      }
    })

    // 참여자 수 업데이트
    socket.on('participant_count_update', (data) => {
      setParticipantCount(data.count)
    })

    // 세션 참여 완료
    socket.on('joined_session', (data) => {
      setParticipantCount(data.participant_count)
    })

    // 에러 처리
    socket.on('error', (data) => {
      setError(data.message)
    })

  }, [sessionId, participantId, nickname, role])

  useEffect(() => {
    connect()

    return () => {
      socketRef.current?.disconnect()
    }
  }, [connect])

  const sendMessage = useCallback((message: string, messageType: 'text' | 'emoji' = 'text') => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('send_message', {
        message,
        message_type: messageType
      })
    }
  }, [isConnected])

  const getChatHistory = useCallback(() => {
    if (socketRef.current && isConnected && sessionId) {
      socketRef.current.emit('get_chat_history', { session_id: sessionId })
    }
  }, [isConnected, sessionId])

  return {
    socket: socketRef.current,
    isConnected,
    participantCount,
    error,
    sendMessage,
    getChatHistory,
    reconnect: connect
  }
}
```

## 2. 채팅 메시지 컴포넌트

### components/chat/ChatMessage.tsx
```typescript
import { cn, formatTime } from '@/lib/utils'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

interface ChatMessageProps {
  id: string
  participantNickname?: string
  message: string
  messageType: 'text' | 'emoji' | 'system'
  createdAt: string
  isOwn?: boolean
  className?: string
}

export function ChatMessage({
  participantNickname,
  message,
  messageType,
  createdAt,
  isOwn = false,
  className
}: ChatMessageProps) {
  if (messageType === 'system') {
    return (
      <div className={cn("text-center text-sm text-gray-500 my-3 px-4", className)}>
        <div className="bg-gray-100 rounded-full py-1 px-3 inline-block">
          {message}
        </div>
      </div>
    )
  }

  return (
    <div className={cn(
      "flex gap-3 px-4 py-2 hover:bg-gray-50",
      isOwn && "bg-blue-50",
      className
    )}>
      {!isOwn && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="text-xs">
            {participantNickname?.charAt(0)?.toUpperCase() || '?'}
          </AvatarFallback>
        </Avatar>
      )}

      <div className={cn("flex-1 min-w-0", isOwn && "ml-auto max-w-[80%]")}>
        {!isOwn && participantNickname && (
          <div className="text-xs font-medium text-gray-700 mb-1">
            {participantNickname}
          </div>
        )}

        <div className={cn(
          "rounded-lg px-3 py-2 break-words",
          messageType === 'emoji' ? "text-2xl" : "text-sm",
          isOwn
            ? "bg-blue-500 text-white ml-auto inline-block"
            : "bg-white border border-gray-200 inline-block"
        )}>
          {message}
        </div>

        <div className={cn(
          "text-xs text-gray-500 mt-1",
          isOwn ? "text-right" : "text-left"
        )}>
          {formatTime(createdAt)}
        </div>
      </div>

      {isOwn && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="text-xs bg-blue-500 text-white">
            {participantNickname?.charAt(0)?.toUpperCase() || 'Me'}
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}
```

## 3. 채팅 입력 컴포넌트

### components/chat/ChatInput.tsx
```typescript
'use client'
import { useState, KeyboardEvent, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, Smile } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

interface ChatInputProps {
  onSendMessage: (message: string, type?: 'text' | 'emoji') => void
  disabled?: boolean
  placeholder?: string
  maxLength?: number
}

export function ChatInput({
  onSendMessage,
  disabled = false,
  placeholder = "메시지를 입력하세요...",
  maxLength = 500
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSend = () => {
    const trimmedMessage = message.trim()
    if (trimmedMessage && !disabled) {
      const messageType = /^[\p{Emoji}]+$/u.test(trimmedMessage) ? 'emoji' : 'text'
      onSendMessage(trimmedMessage, messageType)
      setMessage('')
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleEmojiClick = (emoji: string) => {
    onSendMessage(emoji, 'emoji')
    setShowEmojiPicker(false)
    inputRef.current?.focus()
  }

  const commonEmojis = [
    '👍', '👏', '😀', '😊', '😮', '😢', '❤️', '🔥',
    '💯', '❓', '👋', '🎉', '✨', '💪', '🤔', '😴'
  ]

  return (
    <div className="border-t bg-white p-4">
      {/* 빠른 이모지 버튼 */}
      <div className="flex flex-wrap gap-1 mb-3">
        {commonEmojis.slice(0, 8).map((emoji) => (
          <Button
            key={emoji}
            variant="outline"
            size="sm"
            onClick={() => handleEmojiClick(emoji)}
            disabled={disabled}
            className="text-lg p-1 h-8 w-8 hover:scale-110 transition-transform"
          >
            {emoji}
          </Button>
        ))}
      </div>

      {/* 메시지 입력 영역 */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Input
            ref={inputRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={maxLength}
            className="pr-10 mobile-optimized"
          />
          <div className="absolute right-2 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">
            {message.length}/{maxLength}
          </div>
        </div>

        <Popover open={showEmojiPicker} onOpenChange={setShowEmojiPicker}>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={disabled}
              className="px-3"
            >
              <Smile className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-64 p-2">
            <div className="grid grid-cols-6 gap-2">
              {commonEmojis.map((emoji) => (
                <Button
                  key={emoji}
                  variant="ghost"
                  onClick={() => handleEmojiClick(emoji)}
                  className="text-lg p-2 h-10 w-10 hover:scale-110 transition-transform"
                >
                  {emoji}
                </Button>
              ))}
            </div>
          </PopoverContent>
        </Popover>

        <Button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          size="sm"
          className="px-4"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
```

## 4. 채팅 컨테이너 컴포넌트

### components/chat/ChatContainer.tsx
```typescript
'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { useSocket } from '@/hooks/useSocket'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { ConnectionStatus } from '@/components/session/ConnectionStatus'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { RefreshCw, AlertCircle } from 'lucide-react'

interface Message {
  id: string
  participant_nickname?: string
  message: string
  message_type: 'text' | 'emoji' | 'system'
  created_at: string
}

interface ChatContainerProps {
  sessionId: string
  participantId?: string
  participantNickname: string
  role?: 'participant' | 'presenter'
  className?: string
}

export function ChatContainer({
  sessionId,
  participantId,
  participantNickname,
  role = 'participant',
  className
}: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [userScrolled, setUserScrolled] = useState(false)

  const {
    socket,
    isConnected,
    participantCount,
    error,
    sendMessage,
    getChatHistory,
    reconnect
  } = useSocket({
    sessionId,
    participantId,
    nickname: participantNickname,
    role
  })

  // 자동 스크롤 함수
  const scrollToBottom = useCallback((force = false) => {
    if (force || !userScrolled) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [userScrolled])

  // 스크롤 이벤트 핸들러
  const handleScroll = useCallback((e: Event) => {
    const target = e.target as HTMLElement
    const isNearBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 100
    setUserScrolled(!isNearBottom)
  }, [])

  useEffect(() => {
    if (!socket) return

    // 새 메시지 수신
    const handleNewMessage = (data: Message) => {
      setMessages(prev => [...prev, data])
    }

    // 채팅 히스토리 수신
    const handleChatHistory = (data: { messages: Message[] }) => {
      setMessages(data.messages)
      setIsLoadingHistory(false)
      setTimeout(() => scrollToBottom(true), 100)
    }

    socket.on('new_message', handleNewMessage)
    socket.on('chat_history', handleChatHistory)

    // 연결 시 채팅 히스토리 요청
    if (isConnected && isLoadingHistory) {
      getChatHistory()
    }

    return () => {
      socket.off('new_message', handleNewMessage)
      socket.off('chat_history', handleChatHistory)
    }
  }, [socket, isConnected, isLoadingHistory, getChatHistory, scrollToBottom])

  // 새 메시지가 추가될 때 스크롤
  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // 스크롤 이벤트 리스너 등록
  useEffect(() => {
    const scrollElement = scrollAreaRef.current
    if (scrollElement) {
      scrollElement.addEventListener('scroll', handleScroll)
      return () => scrollElement.removeEventListener('scroll', handleScroll)
    }
  }, [handleScroll])

  const handleSendMessage = useCallback((message: string, messageType: 'text' | 'emoji' = 'text') => {
    sendMessage(message, messageType)
  }, [sendMessage])

  if (error && !isConnected) {
    return (
      <div className={`flex flex-col h-full ${className}`}>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">연결 오류</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={reconnect} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              다시 연결
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex flex-col h-full bg-gray-50 ${className}`}>
      {/* 헤더 */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">실시간 채팅</h2>
          <ConnectionStatus isConnected={isConnected} participantCount={participantCount} />
        </div>
      </div>

      {/* 메시지 목록 */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 custom-scrollbar">
        {isLoadingHistory ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <div className="py-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <p>아직 메시지가 없습니다.</p>
                <p className="text-sm">첫 번째 메시지를 보내보세요!</p>
              </div>
            ) : (
              messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  id={msg.id}
                  participantNickname={msg.participant_nickname}
                  message={msg.message}
                  messageType={msg.message_type}
                  createdAt={msg.created_at}
                  isOwn={msg.participant_nickname === participantNickname}
                />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      {/* 새 메시지 알림 */}
      {userScrolled && (
        <div className="px-4 py-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setUserScrolled(false)
              scrollToBottom(true)
            }}
            className="w-full"
          >
            새 메시지 보기
          </Button>
        </div>
      )}

      {/* 입력 영역 */}
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={!isConnected}
        placeholder={
          isConnected
            ? "메시지를 입력하세요..."
            : "연결을 기다리는 중..."
        }
      />
    </div>
  )
}
```

## 5. 채팅 관리자 뷰 (발표자용)

### components/chat/ChatModeratorView.tsx
```typescript
'use client'
import { useState } from 'react'
import { ChatContainer } from './ChatContainer'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Trash2, Archive, Download } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface ChatModeratorViewProps {
  sessionId: string
  presenterName: string
  onExportChat?: () => void
  onClearChat?: () => void
}

export function ChatModeratorView({
  sessionId,
  presenterName,
  onExportChat,
  onClearChat
}: ChatModeratorViewProps) {
  const [isModeratorMode, setIsModeratorMode] = useState(false)

  return (
    <div className="flex flex-col h-full">
      {/* 관리자 컨트롤 패널 */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <span>채팅 관리</span>
            <Badge variant="outline">발표자</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={isModeratorMode ? "default" : "outline"}
              size="sm"
              onClick={() => setIsModeratorMode(!isModeratorMode)}
            >
              {isModeratorMode ? "일반 모드" : "관리자 모드"}
            </Button>

            {onExportChat && (
              <Button variant="outline" size="sm" onClick={onExportChat}>
                <Download className="h-4 w-4 mr-2" />
                대화 내역 다운로드
              </Button>
            )}

            <Button variant="outline" size="sm">
              <Archive className="h-4 w-4 mr-2" />
              히스토리 보기
            </Button>

            {onClearChat && isModeratorMode && (
              <Button variant="destructive" size="sm" onClick={onClearChat}>
                <Trash2 className="h-4 w-4 mr-2" />
                채팅 지우기
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 채팅 컨테이너 */}
      <div className="flex-1">
        <ChatContainer
          sessionId={sessionId}
          participantNickname={presenterName}
          role="presenter"
        />
      </div>
    </div>
  )
}
```