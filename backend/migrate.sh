#!/bin/bash

# 데이터베이스 마이그레이션 관리 스크립트

# conda 환경 활성화
source /opt/homebrew/anaconda3/etc/profile.d/conda.sh
conda activate engagenow

# 백엔드 디렉토리로 이동
cd "$(dirname "$0")"

# 명령어 실행
case "$1" in
    "upgrade"|"up")
        echo "🔄 데이터베이스 마이그레이션을 최신 버전으로 업그레이드 중..."
        alembic upgrade head
        ;;
    "downgrade"|"down")
        REVISION=${2:-"-1"}
        echo "🔙 데이터베이스를 $REVISION 버전으로 다운그레이드 중..."
        alembic downgrade "$REVISION"
        ;;
    "current"|"status")
        echo "📍 현재 마이그레이션 상태:"
        alembic current
        ;;
    "history"|"log")
        echo "📜 마이그레이션 히스토리:"
        alembic history
        ;;
    "revision"|"new")
        if [ -z "$2" ]; then
            echo "❌ 마이그레이션 설명을 입력해주세요."
            echo "사용법: $0 revision '마이그레이션 설명'"
            exit 1
        fi
        echo "📝 새 마이그레이션 파일 생성 중: $2"
        alembic revision --autogenerate -m "$2"
        ;;
    "reset")
        echo "🔄 데이터베이스 리셋 중..."
        echo "주의: 모든 데이터가 삭제됩니다!"
        read -p "계속하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            alembic downgrade base
            echo "🔄 최신 마이그레이션으로 재적용 중..."
            alembic upgrade head
            echo "✅ 데이터베이스 리셋 완료"
        else
            echo "❌ 작업이 취소되었습니다."
        fi
        ;;
    "test")
        echo "🧪 데이터베이스 연결 테스트 중..."
        python -c "
from app.database import engine
try:
    with engine.connect() as conn:
        print('✅ 데이터베이스 연결 성공')
except Exception as e:
    print(f'❌ 데이터베이스 연결 실패: {e}')
"
        ;;
    *)
        echo "📋 사용 가능한 명령어:"
        echo "  $0 upgrade|up              - 최신 마이그레이션 적용"
        echo "  $0 downgrade|down [rev]    - 이전 마이그레이션으로 롤백"
        echo "  $0 current|status          - 현재 마이그레이션 상태 확인"
        echo "  $0 history|log             - 마이그레이션 히스토리 확인"
        echo "  $0 revision|new <desc>     - 새 마이그레이션 파일 생성"
        echo "  $0 reset                   - 데이터베이스 완전 리셋"
        echo "  $0 test                    - 데이터베이스 연결 테스트"
        echo ""
        echo "예시:"
        echo "  $0 upgrade                 # 최신 버전으로 업그레이드"
        echo "  $0 revision 'Add user table'  # 새 마이그레이션 생성"
        echo "  $0 test                    # 연결 테스트"
        ;;
esac