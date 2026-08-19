import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cv_matching.src.infrastructure.config.settings import get_cv_matching_settings
from cv_matching.src.infrastructure.container import CvMatchingContainer
from cv_matching.src.presentation.api.routes import health, matching

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_cv_matching_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CV Matching API...")

    app.cv_container = CvMatchingContainer()
    app.cv_container.wire(
        modules=[
            "cv_matching.src.presentation.api.routes.matching",
        ]
    )

    try:
        yield
    finally:
        logger.info("Shutting down CV Matching API...")


app = FastAPI(
    title="CV Matching API",
    description="Evidence-backed CV extraction and CV/JD matching API",
    version=settings.app.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    # Set by the ingress in front of the service. FastAPI only uses it to build the
    # URLs in /docs - the app itself still serves the paths below unprefixed.
    root_path=settings.app.root_path,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Global exception handler caught: %s", exc)
    request_id = request.headers.get("X-Request-ID")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            **({"request_id": request_id} if request_id else {}),
        },
    )


app.include_router(
    health.router,
    prefix=settings.app.service_prefix,
    tags=["CV Matching - Health"],
)
app.include_router(
    matching.router,
    prefix=settings.app.service_prefix + settings.app.api_prefix,
    tags=["CV Matching"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
