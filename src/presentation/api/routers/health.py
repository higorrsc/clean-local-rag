from fastapi import APIRouter

from src.domain.models import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check service health and readiness."""
    return HealthResponse(status="ok", version="0.1.0")
