from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn

from app.core.config import settings
from app.core.dependencies import get_db
from app.database.seed import seed_database_if_empty
from app.routers.router import api_router
from app.services.app_settings_service import AppSettingsService

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema is owned by Alembic migrations (`alembic upgrade head`), not created here.
    seed_database_if_empty()
    yield


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.include_router(api_router, prefix="/api/v1")
    application.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    if settings.app_env == "development":
        @application.middleware("http")
        async def disable_static_cache(request: Request, call_next):
            response = await call_next(request)
            if request.url.path.startswith("/static/"):
                response.headers["Cache-Control"] = "no-store"
            return response

    return application


app = create_app()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def render_page(request: Request, template_name: str, db: Session) -> HTMLResponse:
    business_name = AppSettingsService(db).get_settings().business_name
    return templates.TemplateResponse(
        template_name,
        {"request": request, "app_name": settings.app_name, "business_name": business_name},
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render_page(request, "index.html", db)


@app.get("/products", response_class=HTMLResponse)
def products_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render_page(request, "pages/products.html", db)


@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render_page(request, "pages/categories.html", db)


@app.get("/sales", response_class=HTMLResponse)
def sales_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render_page(request, "pages/sales.html", db)


@app.get("/suppliers", response_class=HTMLResponse)
def suppliers_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render_page(request, "pages/suppliers.html", db)


@app.get("/purchases", response_class=HTMLResponse)
def purchases_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render_page(request, "pages/purchases.html", db)


@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render_page(request, "pages/reports.html", db)


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render_page(request, "pages/settings.html", db)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
