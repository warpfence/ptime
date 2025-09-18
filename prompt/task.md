# EngageNow 구현 작업 명세서 (Task.md)

> **참고**: 코드 구현 템플릿은 별도 파일에서 확인하세요.
> - Backend 설정: @backend-setup.md
> - 데이터베이스 모델: @database-models.md
> - 인증 시스템: @auth-system.md
> - 세션 관리: @session-management.md
> - WebSocket 채팅: @websocket-chat.md
> - Frontend 설정: @frontend-setup.md
> - Frontend 컴포넌트: @frontend-components.md
> - 채팅 컴포넌트: @chat-components.md
> - 테스팅 및 배포: @testing-deployment.md

## 1. Phase 1: 기본 인프라 및 인증 시스템 (2주)

### 1.1 프로젝트 초기 설정

#### Task 1.1.1: 개발 환경 설정
**우선순위**: P0 (Critical) | **소요시간**: 1일 | **담당자**: Backend Developer

**작업 내용**:
- [x] Docker Compose 설정 파일 작성 (참고: @backend-setup.md)
- [x] 프로젝트 폴더 구조 생성
- [x] PostgreSQL 15+ 접속정보 설정 (NAS 설정)
- [x] Redis 7+ 접속정보 설정 (NAS 설정)
- [x] 개발용 환경 변수 설정

**완료 기준**:
- Docker Compose로 PostgreSQL, Redis 정상 구동
- 개발 환경에서 데이터베이스 연결 확인

**테스트 계획**:
- PostgreSQL 접속 테스트:
    - url : honi001.synology.me
    - port : 9000
    - POSTGRES_DB=engagenow
    - POSTGRES_USER=hooni1939
    - POSTGRES_PASSWORD=qweruiopyt1!
- Redis 접속 테스트:
    - url : honi001.synology.me
    - port : 9000

---

#### Task 1.1.2: Backend FastAPI 프로젝트 설정
**우선순위**: P0 (Critical) | **소요시간**: 1일 | **담당자**: Backend Developer

**작업 내용**:
- [x] FastAPI 프로젝트 초기화 (참고: @backend-setup.md)
- [x] 필수 라이브러리 설치 및 requirements.txt 작성
- [x] 기본 프로젝트 구조 생성
- [x] FastAPI main.py 앱 진입점 생성
- [x] 설정 관리 시스템 구축

**API 스펙**:
- 기본 헬스체크 엔드포인트: `GET /health`
- API 문서: `GET /docs` (FastAPI 자동 생성)

**완료 기준**:
- FastAPI 서버 정상 구동 (포트: 8000)
- `/health` 엔드포인트 응답 확인
- `/docs` Swagger UI 접근 가능

**테스트 계획**:
- 단위 테스트: `pytest tests/test_main.py`
- API 테스트: `curl http://localhost:8000/health`

---

#### Task 1.1.3: Frontend Next.js 프로젝트 설정
**우선순위**: P0 (Critical) | **소요시간**: 1일 | **담당자**: Frontend Developer

**작업 내용**:
- [x] Next.js 14 프로젝트 초기화 (참고: @frontend-setup.md)
- [x] 필수 라이브러리 설치
- [x] Shadcn/ui 컴포넌트 라이브러리 설정
- [x] 프로젝트 구조 생성
- [x] Tailwind CSS 설정

**완료 기준**:
- Next.js 개발 서버 정상 구동 (포트: 3000)
- Tailwind CSS 스타일링 적용 확인
- Shadcn/ui 기본 컴포넌트 동작 확인

**테스트 계획**:
- 개발 서버 실행: `npm run dev`
- 빌드 테스트: `npm run build`

---

### 1.2 데이터베이스 스키마 설계

#### Task 1.2.1: SQLAlchemy 모델 생성
**우선순위**: P0 (Critical) | **소요시간**: 2일 | **담당자**: Backend Developer

**작업 내용**:
- [x] 기본 모델 클래스 생성 (참고: @database-models.md)
- [x] 사용자 모델 생성
- [x] 세션 모델 생성
- [x] 참여자 모델 생성
- [x] 모듈 모델 생성
- [x] 채팅 메시지 모델 생성
- [x] Q&A 모델 생성
- [x] 투표 모델 생성

**완료 기준**:
- 모든 모델 클래스 생성 완료
- SQLAlchemy 관계 설정 정상 동작
- Alembic 마이그레이션 파일 생성 성공

**테스트 계획**:
- 모델 생성 테스트: `pytest tests/test_models.py`
- 마이그레이션 테스트: `alembic revision --autogenerate`

---

#### Task 1.2.2: 데이터베이스 마이그레이션 설정
**우선순위**: P0 (Critical) | **소요시간**: 1일 | **담당자**: Backend Developer

**작업 내용**:
- [x] Alembic 초기 설정
- [x] alembic.ini 설정 파일 수정
- [x] 초기 마이그레이션 파일 생성
- [x] 마이그레이션 실행 및 검증

**완료 기준**:
- 데이터베이스에 모든 테이블 생성 확인
- 마이그레이션 업/다운그레이드 정상 동작

**테스트 계획**:
- 마이그레이션 실행: `alembic upgrade head`
- 롤백 테스트: `alembic downgrade -1`

---

### 1.3 인증 시스템 구현

#### Task 1.3.1: JWT 토큰 시스템 구현
**우선순위**: P0 (Critical) | **소요시간**: 2일 | **담당자**: Backend Developer

**작업 내용**:
- [x] JWT 설정 및 유틸리티 함수 생성 (참고: @auth-system.md)
- [x] 인증 미들웨어 구현
- [x] 토큰 생성/검증 로직 구현
- [x] 보안 설정 강화

**API 스펙**:
- 토큰 검증: `Authorization: Bearer <token>`
- 토큰 갱신: `POST /auth/refresh`

**완료 기준**:
- JWT 토큰 생성/검증 정상 동작
- 인증이 필요한 엔드포인트 보호 확인

**테스트 계획**:
- 토큰 생성 테스트: `pytest tests/test_auth.py::test_create_token`
- 토큰 검증 테스트: `pytest tests/test_auth.py::test_verify_token`

---

#### Task 1.3.2: Google OAuth 인증 구현
**우선순위**: P0 (Critical) | **소요시간**: 2일 | **담당자**: Backend Developer

**작업 내용**:
- [x] Google OAuth 설정 (참고: @auth-system.md)
- [x] OAuth 인증 라우터 구현
- [x] 사용자 정보 저장 로직 구현
- [x] 토큰 생성 및 반환 처리

**API 스펙**:
- Google 로그인 시작: `GET /auth/login/google`
- Google 콜백: `GET /auth/callback/google`

**완료 기준**:
- Google OAuth 로그인 플로우 정상 동작
- 사용자 정보 데이터베이스 저장 확인
- JWT 토큰 반환 확인

**테스트 계획**:
- OAuth 플로우 E2E 테스트
- 사용자 생성 테스트: `pytest tests/test_oauth.py`

---

#### Task 1.3.3: Frontend 인증 상태 관리
**우선순위**: P0 (Critical) | **소요시간**: 2일 | **담당자**: Frontend Developer

**작업 내용**:
- [ ] Zustand 인증 스토어 생성 (참고: @frontend-components.md)
- [ ] 인증 관련 컴포넌트 생성
- [ ] 인증 가드 컴포넌트 생성
- [ ] API 클라이언트 설정

**UI 컴포넌트 명세**:
- 로그인 페이지: `/auth/login`
- 로그아웃 버튼: 헤더 우측 상단
- 인증 가드: 보호된 페이지 래퍼

**완료 기준**:
- Google OAuth 로그인 정상 동작
- 인증 상태 브라우저 저장소 유지
- 보호된 라우트 접근 제어 확인

**테스트 계획**:
- 컴포넌트 단위 테스트: `npm run test`
- E2E 로그인 테스트: Playwright 사용

---

### 1.4 기본 대시보드 구현

#### Task 1.4.1: 발표자 대시보드 UI 구현
**우선순위**: P1 (High) | **소요시간**: 2일 | **담당자**: Frontend Developer

**작업 내용**:
- [ ] 대시보드 레이아웃 컴포넌트 생성 (참고: @frontend-components.md)
- [ ] 네비게이션 컴포넌트 구현
- [ ] 세션 목록 컴포넌트 생성
- [ ] 세션 생성 다이얼로그 구현

**완료 기준**:
- 대시보드 접근 및 네비게이션 정상 동작
- 세션 목록 조회 및 표시 확인
- 반응형 디자인 적용 확인

**테스트 계획**:
- 컴포넌트 렌더링 테스트
- 반응형 디자인 테스트

---

## 2. Phase 2: 세션 생성 및 QR 코드 시스템 (2주)

### 2.1 세션 관리 API 개발

#### Task 2.1.1: 세션 CRUD API 구현
**우선순위**: P0 (Critical) | **소요시간**: 3일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] 세션 스키마 정의 (참고: @session-management.md)
- [ ] 세션 서비스 로직 구현
- [ ] 세션 API 라우터 구현
- [ ] 세션 코드 생성 시스템 구축

**API 스펙**:
- 세션 생성: `POST /api/sessions`
- 내 세션 목록: `GET /api/sessions`
- 세션 조회: `GET /api/sessions/{session_id}`
- 세션 수정: `PUT /api/sessions/{session_id}`
- 세션 삭제: `DELETE /api/sessions/{session_id}`

**완료 기준**:
- 모든 세션 CRUD 동작 확인
- 세션 코드 고유성 보장
- 권한 검증 정상 동작

**테스트 계획**:
- API 단위 테스트: `pytest tests/test_sessions.py`
- 권한 테스트: 다른 사용자 세션 접근 차단 확인

---

#### Task 2.1.2: QR 코드 생성 시스템 구현
**우선순위**: P0 (Critical) | **소요시간**: 2일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] QR 코드 생성 서비스 구현 (참고: @session-management.md)
- [ ] 세션 생성시 QR 코드 자동 생성
- [ ] 단축 URL 생성 기능
- [ ] Base64 인코딩 처리

**완료 기준**:
- QR 코드 이미지 정상 생성
- 세션 생성시 QR 코드 자동 생성
- QR 코드 스캔으로 참여 URL 접근 확인

**테스트 계획**:
- QR 코드 생성 테스트: `pytest tests/test_qr_code.py`
- QR 코드 스캔 테스트: 모바일 기기에서 확인

---

### 2.2 참여자 시스템 구현

#### Task 2.2.1: 참여자 모델 및 API 구현
**우선순위**: P0 (Critical) | **소요시간**: 2일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] 참여자 모델 생성 (참고: @websocket-chat.md)
- [ ] 참여자 스키마 정의
- [ ] 참여자 서비스 로직 구현
- [ ] 참여자 API 라우터 구현

**API 스펙**:
- 세션 참여: `POST /api/join/{session_code}`
- 참여자 목록: `GET /api/sessions/{session_id}/participants`

**완료 기준**:
- 세션 코드로 참여 가능
- 닉네임 중복 방지 동작
- 참여자 목록 조회 가능

**테스트 계획**:
- 참여자 가입 테스트: `pytest tests/test_participants.py`
- 닉네임 중복 테스트

---

#### Task 2.2.2: 참여자 입장 페이지 구현
**우선순위**: P0 (Critical) | **소요시간**: 2일 | **담당자**: Frontend Developer

**작업 내용**:
- [ ] 세션 참여 페이지 구현 (참고: @frontend-components.md)
- [ ] 닉네임 입력 폼 구현
- [ ] 모바일 최적화 스타일링
- [ ] 에러 처리 및 검증

**완료 기준**:
- QR 코드 스캔으로 참여 페이지 접근
- 닉네임 입력 및 유효성 검증
- 모바일 반응형 디자인 적용

**테스트 계획**:
- 다양한 기기에서 QR 코드 스캔 테스트
- 닉네임 유효성 검증 테스트

---

### 2.3 세션 모니터링 시스템

#### Task 2.3.1: 실시간 참여자 수 모니터링
**우선순위**: P1 (High) | **소요시간**: 2일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] Redis를 활용한 실시간 참여자 관리 (참고: @websocket-chat.md)
- [ ] 참여자 활동 추적 시스템
- [ ] 비활성 참여자 자동 제거
- [ ] 실시간 카운팅 시스템

**완료 기준**:
- 실시간 참여자 수 정확한 추적
- 비활성 참여자 자동 제거
- 참여자 활동 상태 모니터링

**테스트 계획**:
- 참여자 추가/제거 테스트
- TTL 만료 테스트

---

## 3. Phase 3: 실시간 채팅 기능 (2주) - MVP 완성

### 3.1 WebSocket 서버 설정

#### Task 3.1.1: Socket.io 서버 구현
**우선순위**: P0 (Critical) | **소요시간**: 3일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] Socket.io 서버 설정 (참고: @websocket-chat.md)
- [ ] 클라이언트 연결 관리 시스템
- [ ] 세션별 룸 관리
- [ ] FastAPI와 Socket.io 통합

**완료 기준**:
- Socket.io 서버 정상 구동
- 클라이언트 연결/해제 처리
- 세션별 룸 관리 동작

**테스트 계획**:
- WebSocket 연결 테스트
- 다중 클라이언트 연결 테스트

---

#### Task 3.1.2: Frontend Socket.io 클라이언트 구현
**우선순위**: P0 (Critical) | **소요시간**: 2일 | **담당자**: Frontend Developer

**작업 내용**:
- [ ] Socket.io 클라이언트 훅 생성 (참고: @chat-components.md)
- [ ] 실시간 연결 상태 컴포넌트
- [ ] 연결 재시도 로직 구현
- [ ] 에러 처리 시스템

**완료 기준**:
- WebSocket 연결 상태 실시간 표시
- 참여자 수 실시간 업데이트
- 연결 재시도 로직 동작

**테스트 계획**:
- 네트워크 연결/해제 시나리오 테스트
- 다중 탭에서 동시 연결 테스트

---

### 3.2 실시간 채팅 시스템

#### Task 3.2.1: 채팅 메시지 API 구현
**우선순위**: P0 (Critical) | **소요시간**: 3일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] 채팅 메시지 모델 생성 (참고: @websocket-chat.md)
- [ ] 채팅 스키마 정의
- [ ] Socket.io 채팅 이벤트 핸들러 추가
- [ ] 메시지 저장 및 브로드캐스트 시스템

**완료 기준**:
- 실시간 메시지 송수신 동작
- 메시지 데이터베이스 저장 확인
- 채팅 히스토리 조회 가능

**테스트 계획**:
- 메시지 송수신 테스트
- 동시 다중 사용자 채팅 테스트

---

#### Task 3.2.2: 채팅 UI 컴포넌트 구현
**우선순위**: P0 (Critical) | **소요시간**: 3일 | **담당자**: Frontend Developer

**작업 내용**:
- [ ] 채팅 메시지 컴포넌트 (참고: @chat-components.md)
- [ ] 채팅 입력 컴포넌트
- [ ] 채팅 컨테이너 컴포넌트
- [ ] 이모지 시스템 구현

**완료 기준**:
- 실시간 채팅 메시지 송수신
- 이모지 반응 기능 동작
- 모바일 최적화 UI 적용

**테스트 계획**:
- 다양한 메시지 유형 테스트
- 모바일 기기에서 채팅 UX 테스트

---

### 3.3 MVP 통합 테스트

#### Task 3.3.1: E2E 테스트 구현
**우선순위**: P1 (High) | **소요시간**: 2일 | **담당자**: QA Engineer

**작업 내용**:
- [ ] Playwright E2E 테스트 설정 (참고: @testing-deployment.md)
- [ ] 전체 사용자 플로우 테스트 시나리오
- [ ] 성능 테스트 시나리오
- [ ] 다중 브라우저 호환성 테스트

**완료 기준**:
- 전체 사용자 플로우 E2E 테스트 통과
- 성능 테스트 기준 충족
- 다중 브라우저 호환성 확인

**테스트 계획**:
- Chrome, Safari, Firefox에서 실행
- 모바일 브라우저 호환성 테스트

---

## 4. 배포 및 품질 관리

### 4.1 Docker 배포 설정

#### Task 4.1.1: 프로덕션 Docker 설정
**우선순위**: P1 (High) | **소요시간**: 2일 | **담당자**: DevOps Engineer

**작업 내용**:
- [ ] 프로덕션 Dockerfile 작성 (참고: @testing-deployment.md)
- [ ] Docker Compose 프로덕션 설정
- [ ] 환경 변수 보안 설정
- [ ] 볼륨 지속성 설정

**완료 기준**:
- 프로덕션 환경에서 정상 배포
- 환경 변수 보안 설정 완료
- 데이터 볼륨 지속성 확인

**테스트 계획**:
- 스테이징 환경 배포 테스트
- 컨테이너 재시작 시나리오 테스트

---

### 4.2 모니터링 및 로깅

#### Task 4.2.1: 로깅 시스템 구축
**우선순위**: P2 (Medium) | **소요시간**: 1일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] 구조화된 로깅 설정 (참고: @testing-deployment.md)
- [ ] 에러 추적 시스템
- [ ] 성능 지표 로깅
- [ ] 로그 레벨 설정

**완료 기준**:
- 구조화된 JSON 로그 출력
- 에러 추적 가능한 로그 레벨 설정
- 성능 지표 로깅

---

### 4.3 보안 강화

#### Task 4.3.1: 보안 미들웨어 구현
**우선순위**: P1 (High) | **소요시간**: 1일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] CORS 및 보안 헤더 설정 (참고: @auth-system.md)
- [ ] Rate Limiting 구현
- [ ] 입력 데이터 검증 강화
- [ ] XSS, CSRF 보안 설정

**완료 기준**:
- XSS, CSRF 보안 헤더 설정
- API Rate Limiting 동작 확인
- 입력 데이터 검증 강화

---

## 5. 성공 지표 및 검증

### 5.1 성능 벤치마크

#### Task 5.1.1: 부하 테스트 구현
**우선순위**: P1 (High) | **소요시간**: 2일 | **담당자**: QA Engineer

**작업 내용**:
- [ ] Locust 부하 테스트 스크립트 (참고: @testing-deployment.md)
- [ ] WebSocket 동시 연결 테스트
- [ ] 성능 지표 수집 시스템
- [ ] 부하 시나리오 정의

**완료 기준**:
- 1,000명 동시 접속 처리 확인
- 응답 시간 < 200ms 유지
- 메모리 사용량 안정적 유지

---

### 5.2 사용성 테스트

#### Task 5.2.1: 사용자 경험 테스트
**우선순위**: P2 (Medium) | **소요시간**: 3일 | **담당자**: UX Designer

**작업 내용**:
- [ ] 실제 사용자 테스트 시나리오 작성
- [ ] 다양한 기기에서 접근성 테스트
- [ ] QR 코드 스캔 성공률 측정
- [ ] 모바일 브라우저 호환성 검증

**테스트 시나리오**:
1. 발표자가 10분 내에 세션을 생성하고 시작할 수 있는가?
2. 참여자가 QR 코드 스캔 후 30초 내에 채팅 참여 가능한가?
3. 50명이 동시에 채팅할 때 메시지 지연이 3초 이내인가?

**완료 기준**:
- 사용자 만족도 4.0/5.0 이상
- QR 코드 스캔 성공률 95% 이상
- 모바일 접근성 AA 등급 달성

---

## 6. 다음 Phase 준비

### 6.1 Phase 4 Q&A 시스템 사전 준비

#### Task 6.1.1: Q&A 데이터 모델 설계
**우선순위**: P3 (Low) | **소요시간**: 1일 | **담당자**: Backend Developer

**작업 내용**:
- [ ] Q&A 관련 데이터베이스 스키마 설계
- [ ] 질문 투표 시스템 아키텍처 문서화
- [ ] Q&A 모듈 인터페이스 정의

**완료 기준**:
- Phase 4 개발을 위한 기술 문서 완성
- 기존 채팅 시스템과의 연동 방안 설계

---

## 핵심 성공 요소

- **실시간 성능**: < 200ms 응답시간
- **확장성**: 1,000명 동시 접속
- **사용 편의성**: QR 스캔 접근
- **모바일 최적화**: 모든 기능 모바일 지원

MVP 완성 후 Phase 4-7을 통해 Q&A, 투표, 퀴즈, 분석 기능을 단계적으로 추가하여 완전한 실시간 청중 참여 플랫폼을 구축할 예정입니다.