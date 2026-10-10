
from fastapi import Request
from fastapi.responses import JSONResponse


async def not_found_handler(
    request: Request,
    exc: Exception,
):
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
