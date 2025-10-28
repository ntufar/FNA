# Research: Financial Narrative Analyzer Platform

**Date**: 2025-10-29  
**Purpose**: Resolve technical clarifications from implementation planning

## Research Tasks

### R1: Qwen3-4B Deployment Strategy

**Decision**: Self-hosted deployment with GGUF quantization via transformers library

**Rationale**: 
- Local deployment provides data privacy for financial documents
- GGUF 4-bit quantization reduces memory footprint to ~2GB
- Transformers library with auto-quantization simplifies integration
- Avoids API costs and latency from cloud inference

**Alternatives considered**:
- LM Studio: Good for development but limited production scalability
- Cloud hosting (OpenAI/Anthropic): High cost for continuous inference, data privacy concerns
- HuggingFace Inference API: Vendor lock-in, less control over model behavior

**Implementation**: Use `transformers.AutoModelForCausalLM` with `load_in_4bit=True` and BitsAndBytesConfig for quantization.

---

### R2: iXBRL Parsing Library Selection

**Decision**: Arelle library with custom SEC filing extensions

**Rationale**:
- Arelle is the industry standard for XBRL processing, maintained by SEC
- Native support for inline XBRL (iXBRL) format used in modern SEC filings
- Extensive documentation and active community
- Can extract both structured financial data and narrative text content

**Alternatives considered**:
- python-xbrl: Limited iXBRL support, less maintained
- Beautiful Soup HTML parsing: Would miss structured data relationships
- Custom parser: Significant development overhead for complex XBRL taxonomy

**Implementation**: `pip install arelle`, use ModelXbrl class to load filings, extract facts and narrative sections.

---

### R3: SEC.gov Integration Method

**Decision**: SEC EDGAR REST API with rate limiting and caching

**Rationale**:
- SEC provides official REST API for EDGAR database access
- 10 requests per second rate limit (documented)
- Structured JSON responses for filing metadata
- Direct download links for report files (HTML, iXBRL)

**Alternatives considered**:
- Web scraping: Against SEC terms of service, unreliable
- Third-party data providers: Expensive, dependency on external service
- Bulk download archives: Complex processing, storage overhead

**Implementation**: 
- Base URL: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
- User-Agent header required: `Company Name contact@email.com`
- Implement exponential backoff for rate limit compliance

---

### R4: Model Quantization Approach

**Decision**: BitsAndBytesConfig with 4-bit NormalFloat quantization

**Rationale**:
- 4-bit quantization reduces VRAM usage by ~75% 
- NormalFloat (nf4) quantization maintains model performance better than integer
- double_quant reduces memory further with minimal quality loss
- Compatible with LoRA fine-tuning if needed later

**Alternatives considered**:
- 8-bit quantization: Less memory savings, still significant performance
- GGML/llama.cpp: Requires model conversion, less Python integration
- No quantization: 4B model still ~8GB VRAM requirement

**Implementation**:
```python
from transformers import BitsAndBytesConfig
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True
)
```

---

### R5: Vector Embedding Model Choice

**Decision**: sentence-transformers/all-MiniLM-L6-v2 with financial fine-tuning

**Rationale**:
- Lightweight model (80MB) with good semantic understanding
- 384-dimension embeddings balance accuracy and storage efficiency
- Pre-trained on diverse text including financial content
- Fast inference (~100ms for typical document sections)

**Alternatives considered**:
- OpenAI text-embedding-ada-002: Expensive API costs, external dependency
- all-mpnet-base-v2: Larger model (420MB), better quality but slower
- Financial domain-specific models: Limited availability, training overhead

**Implementation**: Load via sentence-transformers library, store embeddings in PostgreSQL vector columns with pgvector.

---

### R6: Frontend Deployment Strategy

**Decision**: Vite build with Vercel deployment and CDN distribution

**Rationale**:
- Vite provides fast development and optimized production builds
- Vercel offers seamless React deployment with automatic CDN
- Environment-based configuration for API endpoints
- Built-in performance optimization and caching

**Alternatives considered**:
- Create React App: Slower builds, less optimized output
- Manual CDN setup: Additional configuration complexity
- Same-server deployment: Couples frontend/backend scaling

**Implementation**: 
- Development: `npm run dev` with proxy to backend
- Production: `npm run build` → Vercel deployment
- Environment variables for API_BASE_URL configuration

---

## Technology Stack Summary

| Component | Technology | Justification |
|-----------|------------|---------------|
| **LLM** | Qwen3-4B + 4-bit quantization | Financial text optimization, large context, cost efficiency |
| **iXBRL Parser** | Arelle library | Industry standard, SEC compliance, structured data extraction |
| **SEC Integration** | EDGAR REST API | Official source, structured responses, rate limit compliance |
| **Embeddings** | sentence-transformers MiniLM-L6-v2 | Lightweight, fast, semantic understanding |
| **Backend** | FastAPI + PostgreSQL + pgvector | Constitution compliance, vector search, performance |
| **Frontend** | React + TypeScript + Vite + Vercel | Modern stack, optimized builds, scalable deployment |

All choices align with constitution requirements and provide clear migration paths for future scaling needs.
