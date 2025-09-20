"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { QRCodeDisplay } from "./qr-code-display";
import { Session } from "@/types/session";

interface QRCodeDialogProps {
  session: Session | null;
  isOpen: boolean;
  onClose: () => void;
}

export function QRCodeDialog({ session, isOpen, onClose }: QRCodeDialogProps) {
  if (!session) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>세션 QR 코드</DialogTitle>
        </DialogHeader>

        <div className="flex justify-center">
          <QRCodeDisplay
            sessionCode={session.session_code}
            qrCodeUrl={session.qr_code_url}
            title={session.title}
            isActive={session.is_active}
            participantCount={session.participant_count}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}