
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Backend API for the ResumeZ AI platform",
    version=settings.app_version,
)


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
                "path": request.url.path,
            }
        },
    )


app.include_router(router)
