# Architecture

## System Architecture

```mermaid
flowchart TD
    A[PDF File] --> B[PDF Reader\npymupdf + pdfplumber]
    B --> C{Scanned page?\n< 30 chars}
    C -- yes --> D[OCR Fallback\npytesseract]
    C -- no --> E[Text + Tables as Markdown]
    D --> E
    E --> F[Page Cache\n.cache/stem/pages.json]
    F --> G[Cleaner\nRemove headers/footers\nFix hyphenation\nDetect headings]
    G --> H[BM25 Indexer\nrank_bm25]
    H --> I[Per-Group Loop x10]
    I --> J[Retriever\nkeywords.yaml + BM25\nStructural boost + Neighbors\nChar budget]
    J --> K[Prompt Builder\nSystem prompt + Group instructions\nFew-shot examples + Pages]
    K --> L{LLM Client}
    L --> M[Gemini\ngoogle-genai]
    L --> N[Ollama\nplain requests]
    M --> O[Response Cache\nsha256 keyed JSON]
    N --> O
    O --> P[Rate Limiter\nToken bucket]
    P --> Q[Pydantic Parser]
    Q --> R{Parse OK?}
    R -- no --> S[Retry once\nwith error hint]
    S --> Q
    R -- yes --> T{> 50% null?}
    T -- yes --> U[Second-pass\nWider retrieval]
    U --> J
    T -- no --> V[Normalizer\nAmounts + Dates + Units]
    V --> W[Grounding Check\nrapidFuzz fuzzy match\nNumber verification]
    W --> X[Business Validator\nDates, SI tiers, Demographics]
    X --> Y[Confidence Scorer]
    Y --> Z[ExtractionResult\nPydantic model]
    Z --> AA[output/stem.json]
    Z --> AB[output/stem.qms.json]
    Z --> AC[output/stem.qms.csv]
    Z --> AD[output/stem.report.md]
```

## Module Dependency Graph

```mermaid
graph LR
    main --> pipeline
    pipeline --> pdf/reader
    pipeline --> pdf/cleaner
    pipeline --> retrieval/indexer
    pipeline --> extraction/runner
    pipeline --> postprocess/normalizer
    pipeline --> postprocess/grounding
    pipeline --> postprocess/validator
    pipeline --> postprocess/confidence
    pipeline --> export/json_writer
    pipeline --> export/qms_mapper
    extraction/runner --> retrieval/retriever
    extraction/runner --> llm/base
    extraction/runner --> prompts/groups
    extraction/runner --> schema/*
    llm/base --> llm/cache
    llm/base --> llm/rate_limiter
    config --> keywords.yaml
    config --> qms_mapping.yaml
    config --> .env
```

## Data Flow

1. **PDF → PageDoc list**: PyMuPDF extracts text; pdfplumber extracts tables; OCR runs on scanned pages. Each page becomes a `PageDoc` with `full_text` including `[PAGE n]` markers.

2. **PageDoc → BM25 index**: All page texts are tokenised and indexed. Structural pages (Annexure, Schedule, etc.) are flagged for boost.

3. **Group → retrieved pages**: For each of the 10 field groups, BM25 scores pages against the group's keywords+synonyms from `keywords.yaml`. Top-k pages plus neighbours are selected within a character budget.

4. **Retrieved pages → LLM prompt**: The system prompt, group-specific instructions with schema, few-shot examples, and the retrieved page texts (with `[PAGE n]` markers) are concatenated.

5. **LLM response → Pydantic model**: The JSON response is validated against the group's Pydantic model. On parse failure, a single retry with the error appended is made.

6. **Second pass**: If >50% of a group's fields are null/not_mentioned, retrieval is widened and a second LLM call is made. The results are merged, preferring non-null values.

7. **Postprocessing**: Amounts/dates/units are normalised. Evidence quotes and numeric values are verified against source text using rapidFuzz. Business rules are checked. Confidence scores are computed.

8. **Export**: Full JSON, flat QMS JSON, CSV, and a human-review Markdown report are written to `output/`.

## Key Design Decisions

| Decision | Rationale |
|---|---|
| No insurer templates | Generic keyword YAML + synonym expansion covers all layouts |
| FeatureValue for all benefits | Consistent structure enables uniform QMS mapping |
| BM25 retrieval | Free, fast, no embeddings needed, sufficient for keyword-heavy insurance docs |
| Character budget | Keeps prompts within free-tier context limits |
| Annexure override rule | GMC policies frequently modify base terms via endorsements |
| Second-pass widening | Handles sparse layouts where benefits are scattered |
| Disk cache | Avoids re-running expensive LLM calls on the same content |
| Grounding check | Catches hallucinated numbers without silently deleting them |
| Warnings (not crashes) | One bad group must not fail the whole extraction |
