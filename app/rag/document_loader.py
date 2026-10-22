"""Knowledge Base Document Loader and Parser for ZentroMart."""
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.config import settings


class KnowledgeChunk(BaseModel):
    chunk_id: str                   # e.g. "RET-2" or "products.csv:ELE-0012"
    doc_id: str
    doc_type: str                   # policy, agent_guide, help, faq, marketing, product, meta
    status: str                     # current, superseded
    effective_from: Optional[str] = None
    title: str
    content: str
    source_file: str


def parse_frontmatter(text: str) -> Dict[str, str]:
    """Parse YAML-like frontmatter enclosed in ---."""
    meta = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            for line in fm_text.splitlines():
                line = line.strip()
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip("'\"")
    return meta


def load_kb_documents(kb_dir: Path | None = None) -> List[KnowledgeChunk]:
    """Load all 21 markdown files from kb/ directory and chunk by section ID."""
    target_dir = kb_dir or settings.KB_DIR
    chunks: List[KnowledgeChunk] = []
    
    md_files = sorted(target_dir.glob("*.md"))
    for file_path in md_files:
        text = file_path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        doc_id = meta.get("doc_id", file_path.stem)
        doc_type = meta.get("doc_type", "policy")
        status = meta.get("status", "current")
        effective_from = meta.get("effective_from")
        doc_title = meta.get("title", file_path.stem)
        
        # Split by section headers: ## [SECTION-ID] Title
        pattern = r"(##\s*\[([^\]]+)\]\s*([^\n]+))"
        matches = list(re.finditer(pattern, text))
        
        if not matches:
            # Fallback if no section headers
            chunks.append(KnowledgeChunk(
                chunk_id=doc_id,
                doc_id=doc_id,
                doc_type=doc_type,
                status=status,
                effective_from=effective_from,
                title=doc_title,
                content=text.strip(),
                source_file=file_path.name
            ))
            continue
            
        for i, match in enumerate(matches):
            section_header_full = match.group(1)
            section_id = match.group(2).strip()
            section_title = match.group(3).strip()
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_body = text[start_pos:end_pos].strip()
            
            chunks.append(KnowledgeChunk(
                chunk_id=section_id,
                doc_id=doc_id,
                doc_type=doc_type,
                status=status,
                effective_from=effective_from,
                title=f"{doc_title} - {section_title}",
                content=section_body,
                source_file=file_path.name
            ))
            
    return chunks


def load_product_catalog(csv_path: Path | None = None) -> List[KnowledgeChunk]:
    """Load products.csv as searchable knowledge chunks with chunk_id 'products.csv:<sku>'."""
    target_path = csv_path or (settings.DATA_CSV_DIR / "products.csv")
    chunks: List[KnowledgeChunk] = []
    
    if not target_path.exists():
        return chunks
        
    with open(target_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row["sku"].strip()
            title = row["title"].strip()
            brand = row.get("brand", "")
            cat = row.get("return_category", "")
            price = row.get("price_inr", "")
            fulfilled = row.get("fulfilled_by", "")
            assured = row.get("assured", "")
            warranty = row.get("warranty_months", "0")
            desc = row.get("description", "")
            
            content = (
                f"Product SKU: {sku}\n"
                f"Title: {title}\n"
                f"Brand: {brand}\n"
                f"Category: {cat}\n"
                f"Price: ₹{price}\n"
                f"Fulfilled by: {fulfilled}\n"
                f"ZentroMart Assured: {assured}\n"
                f"Warranty: {warranty} months\n"
                f"Description: {desc}"
            )
            
            chunks.append(KnowledgeChunk(
                chunk_id=f"products.csv:{sku}",
                doc_id="products.csv",
                doc_type="product",
                status="current",
                title=f"{sku}: {title}",
                content=content,
                source_file="products.csv"
            ))
            
    return chunks
