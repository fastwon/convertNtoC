"""FastAPI app. Runs in-process on 127.0.0.1 (never exposed externally).

P0 scope: a health endpoint plus serving the built React SPA. Feature routers
(projects, episodes, llm, ...) get mounted here in later phases under ``/api``.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api.settings import router as settings_router
from .paths import static_dir


def create_app() -> FastAPI:
    app = FastAPI(title="convertN2C", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": "convertN2C"}

    app.include_router(settings_router)

    # Static SPA mount must be added LAST so /api/* routes take precedence.
    sdir = static_dir()
    if (sdir / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(sdir), html=True), name="spa")
    else:

        @app.get("/")
        def frontend_missing() -> HTMLResponse:
            return HTMLResponse(
                "<h1>프론트엔드 빌드를 찾을 수 없습니다</h1>"
                "<p>먼저 <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code> "
                "를 실행한 뒤 다시 시작하세요.</p>"
            )

    return app


app = create_app()
