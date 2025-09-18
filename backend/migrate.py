#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 관리 스크립트

Usage:
    python migrate.py upgrade    # 최신 마이그레이션 적용
    python migrate.py downgrade  # 이전 마이그레이션으로 롤백
    python migrate.py current    # 현재 마이그레이션 상태 확인
    python migrate.py history    # 마이그레이션 히스토리 확인
    python migrate.py revision "description"  # 새 마이그레이션 파일 생성
"""

import sys
import subprocess
import os

def run_alembic_command(command, description=None):
    """Alembic 명령어 실행"""
    try:
        if command == "revision" and description:
            cmd = ["alembic", "revision", "--autogenerate", "-m", description]
        else:
            cmd = ["alembic", command]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    # 백엔드 디렉토리로 이동
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if command == "upgrade":
        print("🔄 데이터베이스 마이그레이션을 최신 버전으로 업그레이드 중...")
        if run_alembic_command("upgrade", "head"):
            print("✅ 마이그레이션 업그레이드 완료")
        else:
            print("❌ 마이그레이션 업그레이드 실패")
            sys.exit(1)

    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        print(f"🔙 데이터베이스를 {revision} 버전으로 다운그레이드 중...")
        if run_alembic_command("downgrade", revision):
            print("✅ 마이그레이션 다운그레이드 완료")
        else:
            print("❌ 마이그레이션 다운그레이드 실패")
            sys.exit(1)

    elif command == "current":
        print("📍 현재 마이그레이션 상태:")
        run_alembic_command("current")

    elif command == "history":
        print("📜 마이그레이션 히스토리:")
        run_alembic_command("history")

    elif command == "revision":
        if len(sys.argv) < 3:
            print("❌ 마이그레이션 설명을 입력해주세요.")
            print("사용법: python migrate.py revision '마이그레이션 설명'")
            sys.exit(1)

        description = sys.argv[2]
        print(f"📝 새 마이그레이션 파일 생성 중: {description}")
        if run_alembic_command("revision", description):
            print("✅ 마이그레이션 파일 생성 완료")
        else:
            print("❌ 마이그레이션 파일 생성 실패")
            sys.exit(1)

    elif command == "reset":
        print("🔄 데이터베이스 리셋 중...")
        print("주의: 모든 데이터가 삭제됩니다!")
        confirm = input("계속하시겠습니까? (y/N): ")
        if confirm.lower() == 'y':
            if run_alembic_command("downgrade", "base"):
                print("🔄 최신 마이그레이션으로 재적용 중...")
                if run_alembic_command("upgrade", "head"):
                    print("✅ 데이터베이스 리셋 완료")
                else:
                    print("❌ 마이그레이션 재적용 실패")
            else:
                print("❌ 데이터베이스 리셋 실패")
        else:
            print("❌ 작업이 취소되었습니다.")

    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()