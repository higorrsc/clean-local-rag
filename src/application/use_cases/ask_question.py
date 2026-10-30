from src.domain.interfaces import EmbeddingGateway, LLMGateway, VectorRepository
from src.domain.models import QueryRequest, QueryResponse, SourceChunk


class AskQuestionUseCase:
    """
    Orchestrates semantic retrieval, prompt assembly, and answer generation with LLM.
    """

    def __init__(
        self,
        embedding_gateway: EmbeddingGateway,
        vector_repository: VectorRepository,
        llm_gateway: LLMGateway,
    ) -> None:
        self.embedding_gateway = embedding_gateway
        self.vector_repository = vector_repository
        self.llm_gateway = llm_gateway

    def execute(self, request: QueryRequest) -> QueryResponse:
        question = (request.question or "").strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        top_k = request.top_k or 3

        # Generate query embedding
        query_embedding = self.embedding_gateway.generate_embedding(question)

        # Retrieve relevant chunks from vector repository
        retrieved = self.vector_repository.search_similar(query_embedding, top_k=top_k)

        if not retrieved:
            return QueryResponse(
                answer="Não foram encontradas informações relevantes no contexto disponível para responder à pergunta.",
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
        system_prompt = (
            "Você é um assistente RAG local preciso e prestativo. "
            "Responda à pergunta do usuário baseando-se estritamente no contexto fornecido. "
            "Se a resposta não estiver presente no contexto, informe honestamente que não possui a informação."
        )

        user_prompt = f"Contexto:\n{context_text}\n\nPergunta: {question}\n\nResposta:"

        answer = self.llm_gateway.generate_response(
            prompt=user_prompt, system_prompt=system_prompt
        )

        return QueryResponse(answer=answer, sources=source_chunks)
