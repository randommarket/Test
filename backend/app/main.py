from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.routes import router
from app.api.ui import router as ui_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.request_id import RequestIdMiddleware

setup_logging()
app = FastAPI(title=settings.app_name)
app.add_middleware(RequestIdMiddleware)
app.include_router(router)
app.include_router(ui_router)

app.mount("/static", StaticFiles(directory="app/templates"), name="static")
app.state.templates = Jinja2Templates(directory="app/templates")

FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health():
    return {"status": "ok"}
