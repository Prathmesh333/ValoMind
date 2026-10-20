import json
import secrets
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from valomind.config import Settings

ROOT = Path(__file__).resolve().parents[3]
bearer = HTTPBearer(auto_error=False)


class Health(BaseModel):
    status: str


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    app = FastAPI(title="ValoMind foundation", version="0.1.0")

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    def problem(request: Request, status: int, detail: str, code: str):
        return JSONResponse(
            status_code=status,
            media_type="application/problem+json",
            content={
                "type": "about:blank",
                "title": detail,
                "detail": detail,
                "status": status,
                "code": code,
                "instance": request.url.path,
                "request_id": request.state.request_id,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        codes = {401: "UNAUTHORIZED", 404: "NOT_FOUND", 503: "NOT_READY"}
        return problem(
            request, exc.status_code, str(exc.detail), codes.get(exc.status_code, "ERROR")
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return problem(request, 422, "Invalid request", "INVALID_REQUEST")

    @app.get("/api/v1/health/live", response_model=Health)
    def live():
        return {"status": "ok"}

    @app.get("/api/v1/health/ready", response_model=Health)
    def ready():
        engine = create_engine(config.database_url, connect_args={"connect_timeout": 2})
        try:
            with engine.connect() as connection:
                # Check migration state as well as database connectivity.
                revision = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar()
                if revision != "0001":
                    raise HTTPException(503, "Database migration required")
        except SQLAlchemyError:
            raise HTTPException(503, "Database unavailable or migration required") from None
        finally:
            engine.dispose()
        return {"status": "ready"}

    def demo_access(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        token = config.demo_access_token.get_secret_value()
        if not config.demo_synthetic or not token:
            raise HTTPException(404, "Not found")
        if credentials is None or not secrets.compare_digest(credentials.credentials, token):
            raise HTTPException(401, "Authentication required")

    @app.get("/api/v1/demo/match", dependencies=[Depends(demo_access)])
    def demo_match(request: Request):
        data = json.loads((ROOT / "ValoMind_Codex_Docs/fixtures/demo_match.json").read_text())
        return {
            "data": data,
            "meta": {
                "is_synthetic": True,
                "schema_version": "1.0",
                "request_id": request.state.request_id,
                "warning": "Invented fixture; no footage processed and no model trained.",
            },
        }

    return app


app = create_app()
