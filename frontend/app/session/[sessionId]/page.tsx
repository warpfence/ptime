"use client";

import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Users, MessageCircle } from 'lucide-react';
import { ChatInterface } from '@/components/websocket/ChatInterface';
import { ConnectionStatus } from '@/components/websocket/ConnectionStatus';
import { ParticipantCounter } from '@/components/websocket/ParticipantCounter';

export default function SessionPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const sessionId = params.sessionId as string;
  const participantId = searchParams.get('participantId');
  const nickname = searchParams.get('nickname');

  const [sessionInfo, setSessionInfo] = useState({
    title: '실시간 세션',
    description: 'Socket.io 기반 실시간 채팅 테스트'
  });

  // 필수 파라미터 체크
  useEffect(() => {
    if (!participantId || !nickname) {
      router.push('/');
    }
  }, [participantId, nickname, router]);

  if (!participantId || !nickname) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="py-8 text-center">
            <p className="text-gray-600">잘못된 접근입니다.</p>
            <Button onClick={() => router.push('/')} className="mt-4">
              홈으로 돌아가기
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-6">
        {/* 헤더 */}
        <div className="mb-6">
          <div className="flex items-center gap-4 mb-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              나가기
            </Button>

            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">
                {sessionInfo.title}
              </h1>
              {sessionInfo.description && (
                <p className="text-gray-600 mt-1">{sessionInfo.description}</p>
              )}
            </div>

            <div className="flex items-center gap-4">
              <ConnectionStatus />
              <ParticipantCounter showDetails />
            </div>
          </div>

          {/* 참여자 정보 */}
          <div className="flex items-center gap-2">
            <Badge variant="outline">세션 ID: {sessionId}</Badge>
            <Badge variant="default">
              <Users className="w-3 h-3 mr-1" />
              {nickname}
            </Badge>
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 세션 정보 카드 */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  세션 정보
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium text-sm text-gray-700 mb-1">세션 코드</h4>
                  <p className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                    {sessionId}
                  </p>
                </div>

                <div>
                  <h4 className="font-medium text-sm text-gray-700 mb-1">참여자 정보</h4>
                  <div className="space-y-1">
                    <p className="text-sm">닉네임: {nickname}</p>
                    <p className="text-sm text-gray-500">ID: {participantId}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-sm text-gray-700 mb-2">연결 상태</h4>
                  <ConnectionStatus showReconnectButton={true} />
                </div>

                <div className="pt-4 border-t">
                  <ParticipantCounter showDetails />
                </div>
              </CardContent>
            </Card>

            {/* 기능 설명 카드 */}
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-sm">사용 가능한 기능</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-600 space-y-2">
                <div className="flex items-center gap-2">
                  <MessageCircle className="w-4 h-4" />
                  <span>실시간 채팅</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>참여자 수 실시간 업데이트</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                  <span>연결 상태 모니터링</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 채팅 인터페이스 */}
          <div className="lg:col-span-2">
            <Card className="h-[600px]">
              <ChatInterface
                sessionId={sessionId}
                participantId={participantId}
                nickname={nickname}
                autoConnect={true}
                className="h-full"
              />
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}