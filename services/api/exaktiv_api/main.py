from typing import Annotated

from exaktiv_core.health import HealthReport, build_report
from exaktiv_core.settings import Settings, get_settings
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Exaktiv API")  # Internal only. Public API keys arrive in EXK11.


@app.get("/health", response_model=HealthReport)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> JSONResponse:
    report = await build_report(settings)
    return JSONResponse(report.model_dump(), status_code=200 if report.all_ok else 503)
