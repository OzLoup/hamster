from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn

from app.core.config import settings
from app.core.dependencies import get_db, require_business_web_user, require_web_user
from app.database.seed import seed_database_if_empty
from app.models.user import User
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


def render_page(
    request: Request, template_name: str, db: Session, current_user: User
) -> HTMLResponse:
    business_name = AppSettingsService(db, current_user.business_id).get_settings().name
    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "app_name": settings.app_name,
            "business_name": business_name,
            "current_user": current_user,
        },
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "pages/login.html", {"request": request, "app_name": settings.app_name}
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_placeholder_page(
    request: Request, current_user: User = Depends(require_web_user)
) -> HTMLResponse:
    return templates.TemplateResponse(
        "pages/admin_placeholder.html",
        {"request": request, "app_name": settings.app_name, "current_user": current_user},
    )


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "index.html", db, current_user)


@app.get("/products", response_class=HTMLResponse)
def products_page(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "pages/products.html", db, current_user)


@app.get("/categories", response_class=HTMLResponse)
def categories_page(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "pages/categories.html", db, current_user)


@app.get("/sales", response_class=HTMLResponse)
def sales_page(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "pages/sales.html", db, current_user)


@app.get("/suppliers", response_class=HTMLResponse)
def suppliers_page(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "pages/suppliers.html", db, current_user)


@app.get("/purchases", response_class=HTMLResponse)
def purchases_page(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "pages/purchases.html", db, current_user)


@app.get("/open-tabs", response_class=HTMLResponse)
def open_tabs_page(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "pages/open_tabs.html", db, current_user)


@app.get("/reports", response_class=HTMLResponse)
def reports_page(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "pages/reports.html", db, current_user)


@app.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_business_web_user)
) -> HTMLResponse:
    return render_page(request, "pages/settings.html", db, current_user)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
