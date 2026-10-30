from fastapi import APIRouter, HTTPException, status

from src.domain.models import QueryRequest, QueryResponse
from src.presentation.api.dependencies import AskQuestionUseCaseDep

router = APIRouter(prefix="/query", tags=["Query"])


@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
)
async def query_knowledge_base(
    request: QueryRequest,
    use_case: AskQuestionUseCaseDep,
) -> QueryResponse:
    """Perform semantic retrieval and generate context-grounded LLM answer."""
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
            detail=f"Query failed: {err}",
        ) from err
