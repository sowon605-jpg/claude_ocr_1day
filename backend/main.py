import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# 업로드 디렉토리 자동 생성
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)

# expenses.json 초기화
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)
expenses_file = data_dir / "expenses.json"
if not expenses_file.exists():
    expenses_file.write_text("[]", encoding="utf-8")

app = FastAPI(title="영수증 지출 관리 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "영수증 지출 관리 API 서버가 실행 중입니다."}
