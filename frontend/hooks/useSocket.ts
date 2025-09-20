"use client";

import { useEffect, useState, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

export interface SocketData {
  sessionId?: string;
  participantId?: string;
  nickname?: string;
}

export interface ConnectionStatus {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  retryCount: number;
}

export interface ParticipantData {
  id: string;
  nickname: string;
  joined_at: string;
  is_online: boolean;
}

export interface MessageData {
  id: string;
  participant_id: string;
  nickname: string;
  message: string;
  timestamp: string;
  type: string;
}

export interface ParticipantCountData {
  session_id: string;
  total_count: number;
  online_count: number;
  timestamp: string;
}

const SOCKET_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const MAX_RETRY_ATTEMPTS = 5;
const RETRY_DELAY = 1000; // 1초

export function useSocket() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    isConnected: false,
    isConnecting: false,
    error: null,
    retryCount: 0
  });

  const socketRef = useRef<Socket | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const socketDataRef = useRef<SocketData>({});

  // Socket 인스턴스 생성 및 연결
  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return socketRef.current;
    }

    setConnectionStatus(prev => ({
      ...prev,
      isConnecting: true,
      error: null
    }));

    const newSocket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      reconnection: false, // 수동 재연결 관리
    });

    // 연결 성공
    newSocket.on('connect', () => {
      console.log('Socket 연결 성공:', newSocket.id);
      setConnectionStatus({
        isConnected: true,
        isConnecting: false,
        error: null,
        retryCount: 0
      });
    });

    // 연결 실패
    newSocket.on('connect_error', (error) => {
      console.error('Socket 연결 실패:', error);
      setConnectionStatus(prev => ({
        isConnected: false,
        isConnecting: false,
        error: error.message,
        retryCount: prev.retryCount + 1
      }));

      // 자동 재연결 시도
      if (connectionStatus.retryCount < MAX_RETRY_ATTEMPTS) {
        retryConnection();
      }
    });

    // 연결 해제
    newSocket.on('disconnect', (reason) => {
      console.log('Socket 연결 해제:', reason);
      setConnectionStatus(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error: reason === 'io client disconnect' ? null : reason
      }));

      // 예상치 못한 연결 해제인 경우 재연결 시도
      if (reason !== 'io client disconnect' && connectionStatus.retryCount < MAX_RETRY_ATTEMPTS) {
        retryConnection();
      }
    });

    // 서버 연결 확인
    newSocket.on('connected', (data) => {
      console.log('서버 연결 확인:', data);
    });

    socketRef.current = newSocket;
    setSocket(newSocket);

    return newSocket;
  }, [connectionStatus.retryCount]);

  // 재연결 시도
  const retryConnection = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }

    const delay = RETRY_DELAY * Math.pow(2, connectionStatus.retryCount); // 지수 백오프

    retryTimeoutRef.current = setTimeout(() => {
      console.log(`재연결 시도 ${connectionStatus.retryCount + 1}/${MAX_RETRY_ATTEMPTS}`);
      connect();
    }, delay);
  }, [connectionStatus.retryCount, connect]);

  // 수동 재연결
  const reconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
    setConnectionStatus(prev => ({ ...prev, retryCount: 0 }));
    connect();
  }, [connect]);

  // 세션 참여
  const joinSession = useCallback((sessionId: string, participantId: string, nickname: string) => {
    if (!socketRef.current?.connected) {
      console.error('Socket이 연결되지 않았습니다.');
      return false;
    }

    socketDataRef.current = { sessionId, participantId, nickname };

    socketRef.current.emit('join_session', {
      session_id: sessionId,
      participant_id: participantId,
      nickname: nickname
    });

    return true;
  }, []);

  // 세션 나가기
  const leaveSession = useCallback(() => {
    if (!socketRef.current?.connected) {
      return false;
    }

    socketRef.current.emit('leave_session', {});
    socketDataRef.current = {};
    return true;
  }, []);

  // 메시지 전송
  const sendMessage = useCallback((message: string) => {
    if (!socketRef.current?.connected) {
      console.error('Socket이 연결되지 않았습니다.');
      return false;
    }

    if (!message.trim()) {
      return false;
    }

    socketRef.current.emit('send_message', { message: message.trim() });
    return true;
  }, []);

  // 하트비트 전송
  const sendHeartbeat = useCallback(() => {
    if (!socketRef.current?.connected) {
      return false;
    }

    socketRef.current.emit('heartbeat', {});
    return true;
  }, []);

  // 참여자 목록 요청
  const requestParticipantList = useCallback(() => {
    if (!socketRef.current?.connected) {
      return false;
    }

    socketRef.current.emit('get_participant_list', {});
    return true;
  }, []);

  // 이벤트 리스너 등록
  const addEventListener = useCallback((event: string, handler: (...args: any[]) => void) => {
    if (!socketRef.current) {
      return false;
    }

    socketRef.current.on(event, handler);
    return true;
  }, []);

  // 이벤트 리스너 제거
  const removeEventListener = useCallback((event: string, handler?: (...args: any[]) => void) => {
    if (!socketRef.current) {
      return false;
    }

    if (handler) {
      socketRef.current.off(event, handler);
    } else {
      socketRef.current.off(event);
    }
    return true;
  }, []);

  // 연결 해제
  const disconnect = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }

    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setSocket(null);
    }

    setConnectionStatus({
      isConnected: false,
      isConnecting: false,
      error: null,
      retryCount: 0
    });

    socketDataRef.current = {};
  }, []);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    socket,
    connectionStatus,
    socketData: socketDataRef.current,

    // 연결 관리
    connect,
    disconnect,
    reconnect,

    // 세션 관리
    joinSession,
    leaveSession,

    // 메시지 관리
    sendMessage,
    sendHeartbeat,
    requestParticipantList,

    // 이벤트 관리
    addEventListener,
    removeEventListener,
  };
}