"use client";

import { useState } from "react";
import { Copy, Download, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface QRCodeDisplayProps {
  sessionCode: string;
  qrCodeUrl?: string;
  title: string;
  isActive: boolean;
  participantCount: number;
  joinUrl?: string;
}

export function QRCodeDisplay({
  sessionCode,
  qrCodeUrl,
  title,
  isActive,
  participantCount,
  joinUrl
}: QRCodeDisplayProps) {
  const [copied, setCopied] = useState(false);

  const displayJoinUrl = joinUrl || `${window.location.origin}/join/${sessionCode}`;

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(displayJoinUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('클립보드 복사 실패:', err);
    }
  };

  const downloadQRCode = () => {
    if (!qrCodeUrl) return;

    const link = document.createElement('a');
    link.href = qrCodeUrl;
    link.download = `qr-code-${sessionCode}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center pb-4">
        <CardTitle className="text-lg">{title}</CardTitle>
        <div className="flex items-center justify-center gap-2">
          <Badge variant={isActive ? "default" : "secondary"}>
            {isActive ? "활성" : "비활성"}
          </Badge>
          <Badge variant="outline">
            참여자 {participantCount}명
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* QR 코드 이미지 */}
        <div className="flex justify-center">
          {qrCodeUrl ? (
            <div className="relative">
              <img
                src={qrCodeUrl}
                alt={`세션 ${sessionCode} QR 코드`}
                className="w-48 h-48 border border-gray-200 rounded-lg"
              />
              <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={downloadQRCode}
                  className="bg-white/90 hover:bg-white"
                >
                  <Download className="w-4 h-4 mr-2" />
                  다운로드
                </Button>
              </div>
            </div>
          ) : (
            <div className="w-48 h-48 border border-gray-200 rounded-lg flex items-center justify-center bg-gray-50">
              <span className="text-gray-500">QR 코드 생성 중...</span>
            </div>
          )}
        </div>

        {/* 세션 코드 */}
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-1">세션 코드</p>
          <p className="text-2xl font-mono font-bold tracking-wider">
            {sessionCode}
          </p>
        </div>

        {/* 참여 URL */}
        <div className="space-y-2">
          <p className="text-sm text-gray-600">참여 링크</p>
          <div className="flex gap-2">
            <input
              type="text"
              value={displayJoinUrl}
              readOnly
              className="flex-1 px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-md"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={copyToClipboard}
              className="min-w-[80px]"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-1" />
                  복사됨
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-1" />
                  복사
                </>
              )}
            </Button>
          </div>
        </div>

        {/* 사용 방법 안내 */}
        <div className="text-xs text-gray-500 space-y-1">
          <p>• 참여자가 QR 코드를 스캔하거나 링크를 클릭하여 참여할 수 있습니다</p>
          <p>• 세션이 활성화되어야 새로운 참여자가 입장할 수 있습니다</p>
        </div>
      </CardContent>
    </Card>
  );
}