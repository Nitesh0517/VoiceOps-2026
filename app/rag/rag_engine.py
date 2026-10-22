"""RAG Engine coordinating retrieval, context formatting, and citation tracking."""
from typing import List, Dict, Any, Optional
from app.rag.retriever import HybridRetriever
from app.rag.document_loader import KnowledgeChunk


class RAGResponse:
    def __init__(self, answer: str, source_chunks: List[str], answerable: bool,
                 confidence: float, raw_chunks: List[KnowledgeChunk]):
        self.answer = answer
        self.source_chunks = source_chunks
        self.answerable = answerable
        self.confidence = confidence
        self.raw_chunks = raw_chunks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "source_chunks": self.source_chunks,
            "answerable": self.answerable,
            "confidence": round(self.confidence, 4)
        }


class RAGEngine:
    def __init__(self, retriever: Optional[HybridRetriever] = None):
        self.retriever = retriever or HybridRetriever()

    def get_context(self, query: str, top_k: int = 4) -> Dict[str, Any]:
        """Retrieve top relevant chunks and construct formatted context."""
        chunks, scores, answerable = self.retriever.retrieve(query, top_k=top_k)
        
        if not answerable or not chunks:
            return {
                "answerable": False,
                "confidence": 0.0,
                "context_text": "",
                "source_chunks": [],
                "chunks": []
            }
            
        context_parts = []
        source_chunks = []
        for chunk in chunks:
            source_chunks.append(chunk.chunk_id)
            context_parts.append(
                f"--- [SOURCE: {chunk.chunk_id}] ({chunk.title}) [Status: {chunk.status}] ---\n"
                f"{chunk.content}\n"
            )
            
        return {
            "answerable": True,
            "confidence": scores[0] if scores else 0.0,
            "context_text": "\n".join(context_parts),
            "source_chunks": source_chunks,
            "chunks": chunks
        }
