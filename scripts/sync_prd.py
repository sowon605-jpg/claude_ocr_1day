#!/usr/bin/env python3
"""
PostToolUse 훅: Edit/Write 도구 실행 후 PRD 자동 갱신

지원 기능:
  1. backend/requirements.txt 변경 → PRD 내 모든 requirements 코드블록 동기화
  2. 추적 대상 파일 생성·수정 → CHANGES.log 기록
  3. 주요 파일 신규 생성(Write) → PRD Phase 완료 체크박스 자동 업데이트
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
PRD  = ROOT / "PRD_영수증_지출관리앱.md"

# ─── 추적 대상 경로 prefix (forward slash) ────────────────────────────────────
TRACKED_PREFIXES = (
    "backend/",
    "frontend/src/",
    "vercel.json",
    ".gitignore",
    ".env.example",
)

# ─── 신규 파일 생성 시 PRD 체크박스 매핑 ─────────────────────────────────────
# { 상대경로: [(찾을 텍스트, 바꿀 텍스트), ...] }
PHASE_CHECKBOXES = {
    "backend/routers/upload.py": [
        (
            "- [ ] `curl -X POST /api/upload -F",
            "- [x] `curl -X POST /api/upload -F",
        ),
    ],
    "backend/routers/expenses.py": [
        (
            "- [ ] `GET /api/expenses?from=",
            "- [x] `GET /api/expenses?from=",
        ),
        (
            "- [ ] 존재하지 않는 ID로 DELETE 시 404가 반환된다",
            "- [x] 존재하지 않는 ID로 DELETE 시 404가 반환된다",
        ),
    ],
    "backend/routers/summary.py": [],
    "backend/services/storage_service.py": [],
    "backend/services/ocr_service.py": [],
    "frontend/src/api/axios.js": [],
    "vercel.json": [
        (
            "| 8-1-1 | `vercel.json` 작성 | 프론트 빌드(`@vercel/static-build`) + 백엔드 서버리스(`@vercel/python` + Mangum) 라우팅 | ⬜ 수동 |",
            "| 8-1-1 | `vercel.json` 작성 | 프론트 빌드(`@vercel/static-build`) + 백엔드 서버리스(`@vercel/python` + Mangum) 라우팅 | ✅ 완료 |",
        ),
    ],
}


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        sys.exit(0)

    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    fp_str     = tool_input.get("file_path", "")

    if not fp_str or not PRD.exists():
        sys.exit(0)

    # 절대 경로 → 프로젝트 루트 기준 상대 경로 (forward slash)
    try:
        rel = Path(fp_str).relative_to(ROOT).as_posix()
    except ValueError:
        rel = Path(fp_str).as_posix()

    results = []

    # 1. requirements.txt 동기화
    if rel.endswith("requirements.txt") and rel.startswith("backend/"):
        if _sync_requirements():
            results.append("requirements.txt → PRD 코드블록 동기화 완료")

    # 2. 추적 파일 변경 로그 기록
    if _is_tracked(rel):
        _log_change(rel, tool_name)
        results.append(f"변경 로그 기록: {rel}")

    # 3. 신규 파일 생성 시 Phase 체크박스 업데이트
    if tool_name == "Write" and rel in PHASE_CHECKBOXES:
        marks = _mark_phase_checkboxes(rel)
        results.extend(marks)

    for r in results:
        print(f"[PRD 자동 동기화] {r}")


# ─── 1. requirements.txt 동기화 ──────────────────────────────────────────────

def _sync_requirements() -> bool:
    req = ROOT / "backend" / "requirements.txt"
    if not req.exists():
        return False

    content = req.read_text(encoding="utf-8").strip()
    prd = PRD.read_text(encoding="utf-8")

    # ```txt 로 시작하고 fastapi== 이 첫 줄인 블록을 모두 교체
    new_prd = re.sub(
        r"```txt\nfastapi==.*?```",
        f"```txt\n{content}\n```",
        prd,
        flags=re.DOTALL,
    )
    if new_prd != prd:
        PRD.write_text(new_prd, encoding="utf-8")
        return True
    return False


# ─── 2. 변경 로그 ─────────────────────────────────────────────────────────────

def _is_tracked(rel: str) -> bool:
    return any(rel.startswith(p) or rel == p for p in TRACKED_PREFIXES)


def _log_change(rel: str, tool: str):
    log_file = ROOT / "CHANGES.log"
    action = "생성" if tool == "Write" else "수정"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {action}: {rel}\n")


# ─── 3. Phase 완료 체크박스 ────────────────────────────────────────────────────

def _mark_phase_checkboxes(rel: str) -> list:
    replacements = PHASE_CHECKBOXES.get(rel, [])
    if not replacements:
        return []

    prd = PRD.read_text(encoding="utf-8")
    changed = []
    for old, new in replacements:
        if old in prd:
            prd = prd.replace(old, new)
            changed.append(f"Phase 체크박스 업데이트: ...{old[-40:]}")

    if changed:
        PRD.write_text(prd, encoding="utf-8")
    return changed


if __name__ == "__main__":
    main()
