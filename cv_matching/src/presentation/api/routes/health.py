from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str = "cv-matching"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness probe.

    Separate from /health so a liveness check never restarts the pod for a reason
    that only means "not ready yet". Nothing is verified beyond the process being
    up: the CV parser and the LLM are both external calls made per request, and
    probing them here would take the pod out of rotation for someone else's outage.
    """
    return HealthResponse(status="ready")


@router.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})
