---
name: ml4t-rag-financial-research
description: "Retrieval-Augmented Generation for financial document analysis. Use when building LLM pipelines over earnings calls, filings, or research reports."
when_to_use: "Use when building research systems that ground LLM answers in source filings, earnings calls, or research reports"
dependencies: []
metadata:
  book_chapters: "22"
  library: ""
paths: ["**/*agent*.py", "**/*rl*.py", "**/*rag*.py", "**/*graph*.py", "**/*knowledge*.py", "**/*orchestrat*.py"]
---
# RAG for Financial Research

Naive RAG on financial documents produces hallucinated numbers and misattributed claims. Financial-specific chunking, metadata-aware retrieval, and source grounding turn RAG from a liability into a research tool.

## The Problem

Fixed-size 512-token chunks split a 10-K's risk factors across 3 chunks, mix revenue discussion with footnotes, and lose the section context that tells the LLM whether a number is audited revenue or a forward-looking estimate. The model cites "$4.2B revenue" from a risk-factor hypothetical, not the income statement.

## The Pattern

Chunk by document structure (sections, paragraphs), preserve metadata (section, filing date, entity), retrieve with metadata filters so the LLM knows exactly where each fact comes from.

### WRONG

```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=50)
chunks = splitter.split_text(filing_text)
# Chunk 47: "...risk of loss. Revenue for Q3 was $4.2B, representing..."
# No idea if this is Item 1A (Risk Factors) or Item 8 (Financial Statements)
```

### CORRECT

```python
import re
from dataclasses import dataclass

@dataclass
class FinancialChunk:
    text: str
    section: str       # "Item 7 - MD&A"
    filing_type: str   # "10-K", "10-Q"
    entity: str        # "AAPL"
    filing_date: str   # "2024-02-02"

SEC_SECTION_RE = re.compile(
    r"(Item\s+\d+[A-Za-z]?\s*[-—.]\s*.+?)(?=Item\s+\d+[A-Za-z]?\s*[-—.]|\Z)",
    re.DOTALL | re.IGNORECASE,
)

def chunk_sec_filing(text: str, meta: dict) -> list[FinancialChunk]:
    """Split by Item sections, then paragraphs within each."""
    chunks = []
    for match in SEC_SECTION_RE.finditer(text):
        section_text = match.group(1).strip()
        section_name = section_text.split("\n")[0].strip()
        for para in section_text.split("\n\n"):
            if len(para.strip()) > 50:
                chunks.append(FinancialChunk(
                    para.strip(), section_name,
                    meta["filing_type"], meta["ticker"], meta["date"],
                ))
    return chunks
```

## Metadata-Aware Retrieval

Filter by entity before semantic search to avoid cross-entity contamination. Over-retrieve from the vector index (e.g., 3x), then filter by `entity` and `filing_date` metadata before returning top-k results. This prevents "revenue grew 15%" from AAPL matching an MSFT query.

## Grounded Generation

Always require source attribution: include `[Entity Filing Date, Section]` tags in the context and instruct the LLM to cite each claim. Cross-check any numbers the LLM surfaces against structured data (XBRL, financial databases).

## Guardrails

- **Never fixed-size chunk structured documents** — 10-K sections and earnings call speaker turns have natural boundaries
- **Always filter by entity before ranking** — "revenue grew 15%" from AAPL matches MSFT queries semantically
- **Embed filing date in metadata** — "latest revenue" means nothing without knowing which quarter
- **Validate LLM numbers against structured data** — cross-check cited figures against XBRL

## Production Implementation

No ml4t library for RAG. Recommended stack:

- **Chunking**: Custom section-aware parser or `unstructured` library
- **Embeddings**: `sentence-transformers` with `BAAI/bge-base-en-v1.5` or domain-tuned
- **Vector store**: FAISS for local, Qdrant/Weaviate for production
- **Orchestration**: LangChain or LlamaIndex with metadata filtering

## Checklist

- [ ] Documents chunked by structure (section, paragraph) not fixed token count
- [ ] Every chunk carries metadata (entity, date, section, filing type)
- [ ] Retrieval filters by entity before semantic ranking
- [ ] Generation prompt requires source citations
- [ ] Numbers in LLM output validated against structured financial data
