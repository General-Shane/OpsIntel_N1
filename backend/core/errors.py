from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

class OPSINTELBaseException(Exception):
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(OPSINTELBaseException)
    async def opsintel_exception_handler(request: Request, exc: OPSINTELBaseException):
        logger.error(
            "opsintel_exception",
            error_code=exc.error_code,
            message=exc.message,
            path=request.url.path
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "message": exc.message}}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}}
        )
