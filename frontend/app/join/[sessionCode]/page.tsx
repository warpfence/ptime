"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Users, ArrowLeft, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { participantService, SessionInfo } from "@/lib/services/participant-service";

interface JoinFormData {
  nickname: string;
}

export default function JoinSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionCode = params.sessionCode as string;

  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [formData, setFormData] = useState<JoinFormData>({ nickname: "" });
  const [isLoading, setIsLoading] = useState(true);
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nicknameError, setNicknameError] = useState<string | null>(null);

  // 세션 정보 로드
  useEffect(() => {
    loadSessionInfo();
  }, [sessionCode]);

  const loadSessionInfo = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const sessionInfo = await participantService.getSessionByCode(sessionCode);
      setSessionInfo(sessionInfo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "세션 정보를 불러올 수 없습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const validateNickname = (nickname: string): string | null => {
    return participantService.validateNickname(nickname);
  };

  const checkNicknameAvailability = async (nickname: string): Promise<boolean> => {
    try {
      if (!sessionInfo?.id) return false;

      const result = await participantService.checkNicknameAvailability(
        sessionInfo.id,
        nickname.trim()
      );
      return result.is_available;
    } catch (err) {
      return false;
    }
  };

  const handleNicknameChange = (value: string) => {
    setFormData({ ...formData, nickname: value });
    setNicknameError(null);
  };

  const handleJoinSession = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationError = validateNickname(formData.nickname);
    if (validationError) {
      setNicknameError(validationError);
      return;
    }

    setIsJoining(true);
    setError(null);

    try {
      // 닉네임 중복 검사
      const isAvailable = await checkNicknameAvailability(formData.nickname.trim());
      if (!isAvailable) {
        setNicknameError("이미 사용 중인 닉네임입니다. 다른 닉네임을 선택해주세요.");
        return;
      }

      // 세션 참여 API 호출
      const joinResult = await participantService.joinSession(sessionCode, {
        nickname: formData.nickname.trim()
      });

      console.log("세션 참여 성공:", joinResult);

      // 참여 성공 시 세션 대기실이나 채팅 페이지로 이동
      router.push(`/session/${joinResult.session_info.id}?participantId=${joinResult.participant.id}&nickname=${encodeURIComponent(formData.nickname.trim())}`);

    } catch (err) {
      setError(err instanceof Error ? err.message : "세션 참여 중 오류가 발생했습니다.");
    } finally {
      setIsJoining(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">세션 정보를 불러오는 중...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error && !sessionInfo) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardContent className="py-8">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                세션을 찾을 수 없습니다
              </h2>
              <p className="text-gray-600 mb-6">{error}</p>
              <Button onClick={() => router.push("/")} variant="outline">
                <ArrowLeft className="w-4 h-4 mr-2" />
                홈으로 돌아가기
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!sessionInfo?.is_active) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardContent className="py-8">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                세션이 비활성화되어 있습니다
              </h2>
              <p className="text-gray-600 mb-6">
                현재 이 세션은 참여할 수 없습니다. 발표자에게 문의하세요.
              </p>
              <Button onClick={() => router.push("/")} variant="outline">
                <ArrowLeft className="w-4 h-4 mr-2" />
                홈으로 돌아가기
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Users className="w-8 h-8 text-blue-600" />
          </div>
          <CardTitle className="text-xl font-bold text-gray-900">
            {sessionInfo.title}
          </CardTitle>
          {sessionInfo.description && (
            <p className="text-gray-600 text-sm mt-2">
              {sessionInfo.description}
            </p>
          )}
          <div className="flex items-center justify-center gap-2 mt-4">
            <Badge variant="default">
              활성 세션
            </Badge>
            <Badge variant="outline">
              <Users className="w-3 h-3 mr-1" />
              {sessionInfo.participant_count}명 참여
            </Badge>
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleJoinSession} className="space-y-4">
            <div>
              <Label htmlFor="nickname" className="text-sm font-medium text-gray-700">
                닉네임
              </Label>
              <Input
                id="nickname"
                type="text"
                placeholder="참여할 닉네임을 입력하세요"
                value={formData.nickname}
                onChange={(e) => handleNicknameChange(e.target.value)}
                className={`mt-1 ${nicknameError ? 'border-red-500 focus:border-red-500' : ''}`}
                disabled={isJoining}
                maxLength={20}
                autoComplete="off"
                autoFocus
              />
              {nicknameError && (
                <p className="text-red-500 text-xs mt-1">{nicknameError}</p>
              )}
              <p className="text-gray-500 text-xs mt-1">
                1-20자, 특수문자 사용 불가
              </p>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={isJoining || !formData.nickname.trim()}
            >
              {isJoining ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  참여 중...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  세션 참여하기
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              세션 코드: <span className="font-mono font-medium">{sessionCode}</span>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}