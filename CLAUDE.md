# 개발 준수사항

-   파일 생성시 파일 인코딩은 UTF-8을 기준으로 작성한다.
-   @task.md 파일을 기준으로 개발을 진행할 때, task가 진행 완료될 때마다 체크박스에 체크하여 개발 진행사항을 기록한다.
-   python 연결은 conda 가상환경을 사용해야 하고, `python` 명령어로 python을 실행할 수 있다.
    -   conda 경로: `/opt/homebrew/anaconda3/`
    -   conda 초기화: `source /opt/homebrew/anaconda3/bin/activate`
    -   가상환경 활성화: `conda activate engagenow`
    -   전체 명령어 예시: `source /opt/homebrew/anaconda3/bin/activate && conda activate engagenow`
-   templates 폴더에 있는 템플릿 파일을 참조해서 task 개발을 진행하는데, 진행 과정에서 템플릿 파일이 업데이트된다면 파일을 업데이트해야 한다.
-   FrontEnd 화면을 개발할 때, emoji는 사용하지 말고, 꼭 아이콘을 사용해야하는 경우 Lucide icon을 사용해줘

# MCP 사용

-   개발 중, Next.js, React, Python 등 공식 문서를 확인할 땐 context-7-mcp를 사용해서 정확한 문서를 보고 개발 진행해줘.
-   개발 중, shadcn 관련 레퍼런스가 필요할 경우, shadcn-ui-mcp를 사용하여 개발 진행해줘.

# EngageNow Frontend 개발 방안

## 1. Frontend 프로젝트 구조 / 개발 표준 및 컨벤션

@project-structure-setup.md

## 2. 테마 관리 시스템

@theme-system.md

## 3. 상태 관리 표준화

@state-management.md

## 4. API 클라이언트 표준화

@api-client.md

## 5. 컴포넌트 개발 가이드라인

@component-development.md

# EngageNow Backend 개발 방안

## python 가상환경 접속 방법

-   conda activate engagenow

## 1. Backend 프로젝트 구조 / 개발 표준 및 컨벤션

@backend-project-structure.md

## 2. FastAPI 설정 및 미들웨어

@fastapi-setup.md

## 3. 데이터베이스 모델 및 스키마

@database-models-schemas.md

## 4. 인증 시스템

@backend-auth-system.md

## 5. API 엔드포인트

@api-endpoints.md

## 6. WebSocket 및 실시간 통신

@websocket-realtime.md

---

이 개발 방안을 따르면 Claude Code 세션이 바뀌어도 일관된 개발이 가능하며, Frontend와 Backend 모두에서 확장 가능하고 유지보수가 용이한 시스템을 구축할 수 있습니다.
