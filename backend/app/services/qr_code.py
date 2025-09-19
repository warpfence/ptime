"""
QR 코드 생성 서비스
"""

import qrcode
import io
import base64
from typing import Optional
from ..config import settings


class QRCodeService:
    """QR 코드 생성 및 관리 서비스"""

    def __init__(self):
        # 설정에서 frontend URL을 가져오거나 기본값 사용
        self.base_url = getattr(settings, 'frontend_url', 'http://localhost:3000')

    def generate_qr_code(self, session_code: str) -> str:
        """
        세션 참여 URL QR 코드 생성

        Args:
            session_code: 세션 고유 코드

        Returns:
            Base64 인코딩된 QR 코드 이미지 데이터 URL
        """
        # 참여 URL 생성
        url = f"{self.base_url}/join/{session_code}"

        # QR 코드 생성 설정
        qr = qrcode.QRCode(
            version=1,  # QR 코드 사이즈 (1-40)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # 오류 보정 레벨
            box_size=10,  # 각 박스의 픽셀 크기
            border=4,  # 테두리 크기
        )

        # 데이터 추가 및 최적화
        qr.add_data(url)
        qr.make(fit=True)

        # 이미지 생성
        img = qr.make_image(fill_color="black", back_color="white")

        # Base64로 인코딩
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def generate_short_url(self, session_code: str) -> str:
        """
        세션 참여 단축 URL 생성

        Args:
            session_code: 세션 고유 코드

        Returns:
            세션 참여 URL
        """
        return f"{self.base_url}/join/{session_code}"

    def verify_qr_code_data(self, qr_data: str) -> Optional[str]:
        """
        QR 코드 데이터에서 세션 코드 추출

        Args:
            qr_data: QR 코드에서 읽은 데이터

        Returns:
            세션 코드 또는 None (유효하지 않은 경우)
        """
        try:
            # 기본 URL 패턴 확인
            if qr_data.startswith(f"{self.base_url}/join/"):
                session_code = qr_data.replace(f"{self.base_url}/join/", "")
                # 세션 코드 형식 검증 (6자리 대문자+숫자)
                if len(session_code) == 6 and session_code.isalnum() and session_code.isupper():
                    return session_code
            return None
        except Exception:
            return None