from pathlib import Path
from typing import Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .api.routes import router
from .database import init_db
from .errors import register_error_handlers


def create_app(
    db_path: Optional[Union[str, Path]] = None,
    frontend_dist: Optional[Union[str, Path]] = None,
) -> FastAPI:
    db_path = Path(db_path or config.DATABASE_PATH)
    dist = Path(frontend_dist or config.FRONTEND_DIST)

    init_db(db_path)

    app = FastAPI(
        title="Transaction Ledger API",
        version="1.0.0",
        description="Accounts, credits and debits with an immutable transaction history.",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.db_path = db_path

    register_error_handlers(app)
    app.include_router(router)

    if (dist / "index.html").is_file():
        _mount_frontend(app, dist)

    return app


def _mount_frontend(app: FastAPI, dist: Path) -> None:
    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index = dist / "index.html"
    root = dist.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (dist / path).resolve()
        if path and candidate.is_file() and root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)
