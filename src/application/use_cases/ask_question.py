from src.domain.interfaces import (
    AsyncEmbeddingGateway,
    AsyncLLMGateway,
    AsyncVectorRepository,
    EmbeddingGateway,
    LLMGateway,
    VectorRepository,
)
from src.domain.models import QueryRequest, QueryResponse, SourceChunk

NO_CONTEXT_ANSWER = (
    "Não foram encontradas informações relevantes no contexto disponível "
    "para responder à pergunta."
)
SYSTEM_PROMPT = (
    "Você é um assistente RAG local preciso e prestativo. "
    "Responda à pergunta do usuário baseando-se estritamente no contexto "
    "fornecido. Se a resposta não estiver presente no contexto, informe "
    "honestamente que não possui a informação."
)


class AskQuestionUseCase:
    """
    Orchestrates semantic retrieval, prompt assembly, and answer generation with LLM.
    Supports both synchronous and asynchronous execution.
    """

    def __init__(
        self,
        embedding_gateway: EmbeddingGateway | AsyncEmbeddingGateway,
        vector_repository: VectorRepository | AsyncVectorRepository,
        llm_gateway: LLMGateway | AsyncLLMGateway,
    ) -> None:
        self.embedding_gateway = embedding_gateway
        self.vector_repository = vector_repository
        self.llm_gateway = llm_gateway

    def execute(self, request: QueryRequest) -> QueryResponse:
        question = (request.question or "").strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        top_k = request.top_k or 4

        # Generate query embedding
        query_embedding = self.embedding_gateway.generate_embedding(question)

        # Retrieve relevant chunks from vector repository
        retrieved = self.vector_repository.search_similar(query_embedding, top_k=top_k)

        if not retrieved:
            return QueryResponse(
                answer=NO_CONTEXT_ANSWER,
                sources=[],
            )

        # Build augmented prompt
        context_blocks: list[str] = []
        source_chunks: list[SourceChunk] = []

        for chunk, score in retrieved:
            source_label = chunk.source or "Documento"
            context_blocks.append(f"[{source_label}]: {chunk.content}")
            source_chunks.append(
                SourceChunk(
                    content=chunk.content,
                    source=chunk.source,
                    score=float(score),
                )
            )

        context_text = "\n\n".join(context_blocks)
        user_prompt = f"Contexto:\n{context_text}\n\nPergunta: {question}\n\nResposta:"

        answer = self.llm_gateway.generate_response(
            prompt=user_prompt, system_prompt=SYSTEM_PROMPT
        )

        return QueryResponse(answer=answer, sources=source_chunks)

    async def aexecute(self, request: QueryRequest) -> QueryResponse:
        question = (request.question or "").strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        top_k = request.top_k or 4

        # Generate query embedding asynchronously
        if hasattr(self.embedding_gateway, "agenerate_embedding"):
            query_embedding = await self.embedding_gateway.agenerate_embedding(question)
        else:
            query_embedding = self.embedding_gateway.generate_embedding(question)

        # Retrieve relevant chunks asynchronously
        if hasattr(self.vector_repository, "asearch_similar"):
            retrieved = await self.vector_repository.asearch_similar(
                query_embedding, top_k=top_k
            )
        else:
            retrieved = self.vector_repository.search_similar(
                query_embedding, top_k=top_k
            )

        if not retrieved:
            return QueryResponse(
                answer=NO_CONTEXT_ANSWER,
                sources=[],
            )

        context_blocks: list[str] = []
        source_chunks: list[SourceChunk] = []

        for chunk, score in retrieved:
            source_label = chunk.source or "Documento"
            context_blocks.append(f"[{source_label}]: {chunk.content}")
            source_chunks.append(
                SourceChunk(
                    content=chunk.content,
                    source=chunk.source,
                    score=float(score),
                )
            )

        context_text = "\n\n".join(context_blocks)
        user_prompt = f"Contexto:\n{context_text}\n\nPergunta: {question}\n\nResposta:"

        if hasattr(self.llm_gateway, "agenerate_response"):
            answer = await self.llm_gateway.agenerate_response(
                prompt=user_prompt, system_prompt=SYSTEM_PROMPT
            )
        else:
            answer = self.llm_gateway.generate_response(
                prompt=user_prompt, system_prompt=SYSTEM_PROMPT
            )

        return QueryResponse(answer=answer, sources=source_chunks)
