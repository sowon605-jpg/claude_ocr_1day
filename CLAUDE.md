# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

영수증 지출 관리 앱 — OCR(Upstage Vision LLM + LangChain)로 영수증 데이터를 자동 추출하고 지출을 관리하는 1일 스프린트 프로젝트. 데이터베이스 없이 JSON 파일 기반 저장소 사용.

## 기술 스택

| 레이어 | 기술 |
|-------|-----------|
| 프론트엔드 | React 18 + Vite 5 + TailwindCSS 3 |
| 백엔드 | Python FastAPI |
| OCR/AI | LangChain 1.2.15 + `ChatUpstage`(langchain-upstage 0.7.7)를 통한 Upstage Document AI |
| 이미지 처리 | Pillow, pdf2image |
| 저장소 | `backend/data/expenses.json` (추가 기반 JSON 배열) |
| 배포 | Vercel (서버리스) |

## 실행 명령어

### 프론트엔드 (`frontend/`)
```bash
npm install
npm run dev       # Vite 개발 서버
npm run build     # 프로덕션 빌드
npm run preview   # 프로덕션 빌드 미리보기
```

### 백엔드 (`backend/`)
```bash
pip install -r requirements.txt
uvicorn main:app --reload   # FastAPI 개발 서버 (포트 8000)
```

## 아키텍처

```
React SPA  →  FastAPI (POST /api/upload, GET /api/expenses 등)
                  ↓
           LangChain Chain:
           1. PIL/pdf2image → Base64 인코딩
           2. ChatUpstage Vision LLM 호출
           3. JSON 출력 파싱
           4. expenses.json에 추가 저장
```

**Vercel 서버리스 주의사항**: 요청 간 파일시스템이 초기화됨. MVP에서는 클라이언트 localStorage 사용; 장기적으로 Supabase 또는 Vercel KV로 마이그레이션 예정.

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|---------|
| POST | `/api/upload` | 영수증 업로드 → OCR → 저장 |
| GET | `/api/expenses` | 지출 목록 조회 (날짜 필터 지원) |
| PUT | `/api/expenses/{id}` | 지출 항목 수정 |
| DELETE | `/api/expenses/{id}` | 지출 항목 삭제 |
| GET | `/api/summary` | 합계 및 카테고리별 통계 |

## 데이터 스키마

```json
{
  "id": "uuid-v4",
  "created_at": "ISO8601",
  "store_name": "string",
  "receipt_date": "YYYY-MM-DD",
  "receipt_time": "HH:MM",
  "category": "string",
  "items": [{"name": "", "quantity": 0, "unit_price": 0, "total_price": 0}],
  "subtotal": 0,
  "discount": 0,
  "tax": 0,
  "total_amount": 0,
  "payment_method": "string",
  "raw_image_path": "uploads/..."
}
```

## 환경 변수

```
UPSTAGE_API_KEY=...   # Upstage Vision LLM 필수 키 (로컬: .env 파일, 프로덕션: Vercel 환경 변수)
```

## 주요 제약사항

- OCR 성공률 목표: 80% 이상, 응답 시간 목표: 10초 이하
- v1에서는 한국어·영어 영수증만 지원
- v1에서는 사용자 인증 없음 (URL 기반 접근만 허용)
- 파일 업로드는 OCR 처리 전 서버 측에서 유효성 검사
- 테스트용 영수증 이미지 11장이 `images/`에 있음 (이마트, 스타벅스, CU, 롯데 등)

## 프론트엔드 구조 (계획)

- `/` — `SummaryCard` + `ExpenseList`로 구성된 대시보드
- `/upload` — `DropZone` 업로드 + `ParsePreview` 수정 가능 폼
- `/expense/:id` — 상세 보기 및 편집

UI는 Pretendard + Noto Sans KR 폰트, 기본 색상 indigo-600, TailwindCSS 4px 간격 체계 사용.

## 배포

```json
// vercel.json
{
  "builds": [
    { "src": "frontend/package.json", "use": "@vercel/static-build" },
    { "src": "backend/main.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "backend/main.py" },
    { "src": "/(.*)", "dest": "frontend/dist/$1" }
  ]
}
```
