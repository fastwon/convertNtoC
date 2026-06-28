# convertN2C

소설 → 만화 자동 변환 **데스크톱 앱** (Windows EXE).
프로젝트 단위로 화풍·캐릭터·줄거리를 기억해 회차별로 일관된 만화를 생성합니다.

- 기획/아키텍처: [docs/DESIGN.md](docs/DESIGN.md)
- 개발 로드맵(단계): [docs/ROADMAP.md](docs/ROADMAP.md)
- 작업 규약: [CLAUDE.md](CLAUDE.md)

스택: PyWebView + FastAPI(로컬, in-process) + React(Vite, SPA), PyInstaller 단일 exe.
LLM = Claude(Anthropic), 이미지 = 외부 API. 키는 사용자가 직접 입력(추후 단계).

> 현재 상태: **P0 스캐폴딩** — 창이 뜨고 React ↔ FastAPI(127.0.0.1) 연결 확인까지.

## 사전 요구사항

- Python 3.10+
- Node.js 18+ (LTS 권장)
- Windows: Edge **WebView2 런타임** (Win11 기본 포함)

## 개발 실행

```bash
# 1) 프론트엔드 빌드 (정적 SPA → frontend/dist)
cd frontend
npm install
npm run build
cd ..

# 2) 파이썬 환경 + 의존성
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash
# (PowerShell:  .venv\Scripts\Activate.ps1)
pip install -e ".[dev]"

# 3) 앱 실행 (창이 뜨고 "백엔드 연결됨 ✓" 표시)
python -m app.main
```

### HMR로 프론트 개발 (선택)

```bash
# 터미널 A: 백엔드를 고정 포트로
CONVERTN2C_PORT=8756 python -m app.main   # 또는 uvicorn으로 server:app
# 터미널 B: Vite 개발 서버(/api 는 8756으로 프록시)
cd frontend && npm run dev
```

## EXE 빌드

```bash
cd frontend && npm install && npm run build && cd ..
pip install -e ".[dev]"
pyinstaller packaging/convertN2C.spec
# 결과: dist/convertN2C.exe
```

## 구조

```
app/            # FastAPI 백엔드 (api/ llm/ services/ storage/)
frontend/       # React SPA (Vite)
packaging/      # PyInstaller spec
docs/           # DESIGN.md, ROADMAP.md
```
