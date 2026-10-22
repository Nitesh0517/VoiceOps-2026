"""Automated tests for RAG loader, hybrid retriever, and precedence."""
import pytest
from app.rag.document_loader import load_kb_documents, load_product_catalog
from app.rag.retriever import HybridRetriever
from app.rag.rag_engine import RAGEngine


@pytest.fixture(scope="module")
def rag():
    return RAGEngine()


def test_kb_document_loader():
    chunks = load_kb_documents()
    assert len(chunks) >= 21
    # Check key section IDs are present
    chunk_ids = {c.chunk_id for c in chunks}
    assert "KB-00.1" in chunk_ids
    assert "RET-2" in chunk_ids
    assert "REF-2" in chunk_ids
    assert "DWM-2" in chunk_ids
    assert "WAR-2" in chunk_ids


def test_product_catalog_loader():
    prods = load_product_catalog()
    assert len(prods) == 70
    sku_ids = {p.chunk_id for p in prods}
    assert "products.csv:ELE-0012" in sku_ids
    assert "products.csv:ELE-0001" in sku_ids


def test_rag_precedence_wallet_refund(rag):
    # PQ0003: "How fast are refunds to the ZentroMart Wallet?"
    # Policy REF-2 says instant (2 hrs), FAQ-1 says 5-7 days. REF-2 must win over FAQ-1.
    ctx = rag.get_context("How fast are refunds to the ZentroMart Wallet?")
    assert ctx["answerable"] is True
    top_chunk_id = ctx["source_chunks"][0]
    assert top_chunk_id in ("REF-2", "KB-00.1")
    assert "FAQ-1" not in ctx["source_chunks"][:1]


def test_rag_product_sku_retrieval(rag):
    # PQ0002: "SKU ELE-0012 pe ZentroMart Assured hai kya? Claim kaise karein?"
    ctx = rag.get_context("SKU ELE-0012 pe ZentroMart Assured hai kya? Claim kaise karein?")
    assert ctx["answerable"] is True
    assert "products.csv:ELE-0012" in ctx["source_chunks"]
    assert any("WAR" in sid for sid in ctx["source_chunks"])


def test_rag_unsupported_questions(rag):
    # PQ0004: "Can I schedule a delivery at midnight?"
    ctx1 = rag.get_context("Can I schedule a delivery at midnight?")
    assert ctx1["answerable"] is False

    # PQ0009: "Is there a student discount?"
    ctx2 = rag.get_context("Is there a student discount?")
    assert ctx2["answerable"] is False
