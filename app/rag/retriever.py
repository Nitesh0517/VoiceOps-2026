"""Hybrid Knowledge Base Retriever with Document Precedence and Entity Grounding."""
import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from app.rag.document_loader import KnowledgeChunk, load_kb_documents, load_product_catalog


# Document precedence weights based on KB-00.1
PRECEDENCE_WEIGHTS = {
    "policy": 1.40,
    "agent_guide": 1.18,
    "help": 1.05,
    "faq": 0.88,       # Traps: Policy overrides FAQ
    "marketing": 0.70,
    "meta": 1.00
}

UNSUPPORTED_PATTERNS = [
    r"\bmidnight\b",
    r"\bstudent discount\b",
    r"\bpet\b",
    r"\bflight\b",
    r"\blottery\b",
    r"\bcrypto\b",
    r"\bgift card\b",
    r"\binstall.*ac\b",
    r"\bexchange rate\b"
]


class HybridRetriever:
    def __init__(self, kb_chunks: List[KnowledgeChunk] | None = None,
                 product_chunks: List[KnowledgeChunk] | None = None):
        self.kb_chunks = kb_chunks if kb_chunks is not None else load_kb_documents()
        self.product_chunks = product_chunks if product_chunks is not None else load_product_catalog()
        
        # Product lookup maps
        self.products_by_sku: Dict[str, KnowledgeChunk] = {}
        for p in self.product_chunks:
            # chunk_id is "products.csv:<sku>"
            sku = p.chunk_id.split(":", 1)[-1].strip().upper()
            self.products_by_sku[sku] = p

        self.chunk_by_id: Dict[str, KnowledgeChunk] = {c.chunk_id: c for c in self.kb_chunks}
        for p in self.product_chunks:
            self.chunk_by_id[p.chunk_id] = p
        
        # Build vectorizers over KB documents
        corpus = [f"{c.title}\n{c.content}" for c in self.kb_chunks]
        
        # Word TF-IDF
        self.word_vec = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 3),
            token_pattern=r"(?u)\b[\w-]+\b",
            max_features=5000
        )
        self.word_matrix = self.word_vec.fit_transform(corpus)
        
        # Char TF-IDF for Hindi / Hinglish phonetics
        self.char_vec = TfidfVectorizer(
            lowercase=True,
            analyzer="char_wb",
            ngram_range=(3, 5),
            max_features=7000
        )
        self.char_matrix = self.char_vec.fit_transform(corpus)
        
        # Dense SVD
        n_components = min(35, len(corpus) - 1)
        if n_components > 2:
            self.svd = TruncatedSVD(n_components=n_components, random_state=42)
            self.dense_matrix = self.svd.fit_transform(self.word_matrix)
            norms = np.linalg.norm(self.dense_matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.dense_matrix = self.dense_matrix / norms
        else:
            self.svd = None
            self.dense_matrix = None

    def _extract_sku(self, query: str) -> List[str]:
        return re.findall(r"\b([A-Z]{3}-\d{4})\b", query.upper())

    def _match_product(self, query: str) -> Optional[KnowledgeChunk]:
        """Find matching product by SKU or distinct title words."""
        skus = self._extract_sku(query)
        if skus and skus[0] in self.products_by_sku:
            return self.products_by_sku[skus[0]]
            
        q_lower = query.lower()
        for p in self.product_chunks:
            title = p.title.split(":", 1)[-1].strip().lower()
            if title and title in q_lower:
                return p
        # Check distinctive product phrases
        for p in self.product_chunks:
            title = p.title.split(":", 1)[-1].strip().lower()
            words = [w for w in title.split() if len(w) > 4]
            if len(words) >= 2 and all(w in q_lower for w in words[:2]):
                return p
        return None

    def _is_unsupported(self, query: str) -> bool:
        q_lower = query.lower()
        for pat in UNSUPPORTED_PATTERNS:
            if re.search(pat, q_lower):
                return True
        return False

    def retrieve(self, query: str, top_k: int = 5) -> Tuple[List[KnowledgeChunk], List[float], bool]:
        """
        Retrieve relevant knowledge chunks with score ranking and precedence filtering.
        Returns (chunks, scores, is_answerable).
        """
        if self._is_unsupported(query):
            return [], [], False
            
        matching_product = self._match_product(query)
        
        q_word = self.word_vec.transform([query])
        q_char = self.char_vec.transform([query])
        
        word_sims = (self.word_matrix @ q_word.T).toarray().ravel()
        char_sims = (self.char_matrix @ q_char.T).toarray().ravel()
        
        if self.svd is not None and self.dense_matrix is not None:
            q_dense = self.svd.transform(q_word)
            q_norm = np.linalg.norm(q_dense)
            if q_norm > 0:
                q_dense = q_dense / q_norm
                dense_sims = (self.dense_matrix @ q_dense.T).ravel()
            else:
                dense_sims = np.zeros_like(word_sims)
        else:
            dense_sims = np.zeros_like(word_sims)
            
        combined_scores = 0.50 * word_sims + 0.35 * char_sims + 0.15 * np.maximum(0, dense_sims)
        
        q_lower = query.lower()
        final_scores = np.zeros_like(combined_scores)
        
        for idx, chunk in enumerate(self.kb_chunks):
            score = combined_scores[idx]
            
            # Precedence weighting
            prec_weight = PRECEDENCE_WEIGHTS.get(chunk.doc_type, 1.0)
            if chunk.status == "superseded":
                prec_weight *= 0.30  # Superseded policies strictly penalized
            score *= prec_weight
            
            # Explicit section boost
            if chunk.chunk_id.lower() in q_lower:
                score += 0.80
                
            # Domain-specific keyword grounding boosts
            if ("refund" in q_lower or "wallet" in q_lower or "paise" in q_lower) and chunk.chunk_id == "REF-2":
                score += 0.35
            if ("assured" in q_lower or "warranty" in q_lower) and chunk.chunk_id == "WAR-2":
                score += 0.40
            if ("return" in q_lower or "wapas" in q_lower) and chunk.chunk_id == "RET-2":
                score += 0.25
                
            final_scores[idx] = score
            
        ranked_indices = np.argsort(final_scores)[::-1]
        
        results: List[KnowledgeChunk] = []
        result_scores: List[float] = []
        
        # If product was specifically matched, place it in top results
        if matching_product is not None:
            results.append(matching_product)
            result_scores.append(1.0)
            
        for i in ranked_indices:
            if len(results) >= top_k:
                break
            results.append(self.kb_chunks[i])
            result_scores.append(float(final_scores[i]))
            
        max_score = max(result_scores) if result_scores else 0.0
        is_answerable = max_score >= 0.12
        
        return results, result_scores, is_answerable
