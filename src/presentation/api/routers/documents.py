from fastapi import APIRouter, HTTPException, status

from src.domain.models import (
    BatchIngestRequest,
    BatchIngestResponse,
    IngestRequest,
    IngestResponse,
)
from src.presentation.api.dependencies import (
    BatchIngestUseCaseDep,
    IngestUseCaseDep,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
)
async def ingest_document(
    request: IngestRequest,
    use_case: IngestUseCaseDep,
) -> IngestResponse:
    """Ingest a single document text for chunking and vector indexing."""
    try:
        return await use_case.aexecute(request)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {err}",
        ) from err


@router.post(
    "/ingest/by-language",
    response_model=BatchIngestResponse,
    status_code=status.HTTP_200_OK,
)
async def ingest_documents_by_language(
    request: BatchIngestRequest,
    use_case: BatchIngestUseCaseDep,
) -> BatchIngestResponse:
    """
    Batch ingest all markdown files in the specified language folder.
    """
    try:
        return await use_case.execute(request)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch ingestion failed: {err}",
        ) from err
