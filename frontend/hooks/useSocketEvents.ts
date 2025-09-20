"use client";

import { useEffect, useState, useCallback } from 'react';
import { useSocket, MessageData, ParticipantData, ParticipantCountData } from './useSocket';

export interface SocketEvents {
  onMessage: (message: MessageData) => void;
  onParticipantJoined: (participant: { participant_id: string; nickname: string; joined_at: string }) => void;
  onParticipantLeft: (participant: { participant_id: string; nickname: string; left_at: string }) => void;
  onParticipantCountUpdated: (data: ParticipantCountData) => void;
  onParticipantList: (data: { participants: ParticipantData[]; total_count: number; online_count: number }) => void;
  onSessionJoined: (data: { message: string; session_id: string; participant_id: string }) => void;
  onHeartbeatAck: (data: { timestamp: string }) => void;
  onError: (error: { message: string }) => void;
}

export function useSocketEvents(events?: Partial<SocketEvents>) {
  const { socket, addEventListener, removeEventListener } = useSocket();

  const [messages, setMessages] = useState<MessageData[]>([]);
  const [participants, setParticipants] = useState<ParticipantData[]>([]);
  const [participantCount, setParticipantCount] = useState({ total: 0, online: 0 });
  const [lastHeartbeat, setLastHeartbeat] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  // 메시지 수신 핸들러
  const handleNewMessage = useCallback((message: MessageData) => {
    setMessages(prev => [...prev, message]);
    events?.onMessage?.(message);
  }, [events]);

  // 참여자 참가 핸들러
  const handleParticipantJoined = useCallback((data: { participant_id: string; nickname: string; joined_at: string }) => {
    events?.onParticipantJoined?.(data);
  }, [events]);

  // 참여자 나감 핸들러
  const handleParticipantLeft = useCallback((data: { participant_id: string; nickname: string; left_at: string }) => {
    events?.onParticipantLeft?.(data);
  }, [events]);

  // 참여자 수 업데이트 핸들러
  const handleParticipantCountUpdated = useCallback((data: ParticipantCountData) => {
    setParticipantCount({ total: data.total_count, online: data.online_count });
    events?.onParticipantCountUpdated?.(data);
  }, [events]);

  // 참여자 목록 수신 핸들러
  const handleParticipantList = useCallback((data: { participants: ParticipantData[]; total_count: number; online_count: number }) => {
    setParticipants(data.participants);
    setParticipantCount({ total: data.total_count, online: data.online_count });
    events?.onParticipantList?.(data);
  }, [events]);

  // 세션 참여 성공 핸들러
  const handleSessionJoined = useCallback((data: { message: string; session_id: string; participant_id: string }) => {
    events?.onSessionJoined?.(data);
  }, [events]);

  // 하트비트 응답 핸들러
  const handleHeartbeatAck = useCallback((data: { timestamp: string }) => {
    setLastHeartbeat(data.timestamp);
    events?.onHeartbeatAck?.(data);
  }, [events]);

  // 에러 핸들러
  const handleError = useCallback((error: { message: string }) => {
    setErrors(prev => [...prev, error.message]);
    events?.onError?.(error);
  }, [events]);

  // Socket 이벤트 리스너 등록
  useEffect(() => {
    if (!socket) return;

    // 이벤트 리스너 등록
    addEventListener('new_message', handleNewMessage);
    addEventListener('participant_joined', handleParticipantJoined);
    addEventListener('participant_left', handleParticipantLeft);
    addEventListener('participant_count_updated', handleParticipantCountUpdated);
    addEventListener('participant_list', handleParticipantList);
    addEventListener('session_joined', handleSessionJoined);
    addEventListener('heartbeat_ack', handleHeartbeatAck);
    addEventListener('error', handleError);

    // 컴포넌트 언마운트 시 이벤트 리스너 정리
    return () => {
      removeEventListener('new_message', handleNewMessage);
      removeEventListener('participant_joined', handleParticipantJoined);
      removeEventListener('participant_left', handleParticipantLeft);
      removeEventListener('participant_count_updated', handleParticipantCountUpdated);
      removeEventListener('participant_list', handleParticipantList);
      removeEventListener('session_joined', handleSessionJoined);
      removeEventListener('heartbeat_ack', handleHeartbeatAck);
      removeEventListener('error', handleError);
    };
  }, [
    socket,
    addEventListener,
    removeEventListener,
    handleNewMessage,
    handleParticipantJoined,
    handleParticipantLeft,
    handleParticipantCountUpdated,
    handleParticipantList,
    handleSessionJoined,
    handleHeartbeatAck,
    handleError
  ]);

  // 메시지 목록 초기화
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // 에러 목록 초기화
  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  // 특정 에러 제거
  const removeError = useCallback((index: number) => {
    setErrors(prev => prev.filter((_, i) => i !== index));
  }, []);

  return {
    // 상태 데이터
    messages,
    participants,
    participantCount,
    lastHeartbeat,
    errors,

    // 상태 관리 함수
    clearMessages,
    clearErrors,
    removeError,
  };
}