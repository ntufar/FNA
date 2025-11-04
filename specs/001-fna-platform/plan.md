# Implementation Plan: Financial Narrative Analyzer Platform

**Branch**: `001-fna-platform` | **Date**: 2025-10-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-fna-platform/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

AI-powered Financial Narrative Analyzer platform that automatically downloads financial reports from SEC.gov, extracts narrative content from multiple formats (PDF, HTML, TXT, iXBRL), and performs multi-dimensional sentiment analysis (optimism, risk, uncertainty) with comparison capabilities across reporting periods. Core value: automated detection of narrative tone shifts in management communications that may signal strategic changes or emerging risks before they appear in financial metrics.

**Technical Approach**: FastAPI backend with Qwen3-4B LLM for sentiment analysis, PostgreSQL with pgvector for data storage and vector search, Celery with PostgreSQL broker/backend for asynchronous batch processing, React frontend for visualization, and programmatic API access for enterprise integration. Cross-references narrative sentiment with structured financial data from iXBRL parsing for enhanced insights.

## Technical Context

**Language/Version**: Python 3.11+ (backend), React 18+ with TypeScript (frontend)  
**Primary Dependencies**: FastAPI, Transformers library, Qwen3-4B LLM, PostgreSQL, pgvector, SQLAlchemy, Celery, Kombu (SQLAlchemy transport), React, Tailwind CSS  
**Storage**: PostgreSQL with pgvector extension for structured data and vector embeddings, local filesystem for uploaded documents  
**Testing**: pytest (backend), Jest/React Testing Library (frontend)  
**Target Platform**: Linux server (containerized deployment), modern web browsers  
**Project Type**: web (FastAPI backend + React frontend)  
**Performance Goals**: <60s document processing, <200ms API response times, <3s dashboard interactions, support 100 concurrent users  
**Constraints**: ≥85% sentiment analysis accuracy, ≥95% system uptime, <500ms integration API responses, batch limit 10 reports  
**Scale/Scope**: Multi-tenant SaaS platform with tiered access (Basic/Pro/Enterprise), unlimited historical data retention, cross-referenced financial analysis

**Technical Decisions Finalized**: All clarifications resolved - see research.md for detailed technology choices and implementation strategies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Compliance

✅ **I. AI-First Analysis**: Feature leverages Qwen3-4B LLM for multi-dimensional sentiment analysis (optimism, risk, uncertainty) with confidence scoring. All text processing automated through fine-tuned model.

✅ **II. Data Accuracy & Reliability**: Spec requires ≥85% sentiment classification accuracy with continuous monitoring. Cross-referencing with financial metrics provides additional validation.

✅ **III. Performance Optimization**: <60s document processing, <200ms API responses align with constitution requirements. Model quantization (4-bit GGUF) planned for cost optimization.

✅ **IV. API-First Design**: All analytical capabilities exposed via REST API with JSON responses. Frontend built on public APIs with authentication and rate limiting.

✅ **V. Scalability & Cost Management**: PostgreSQL with pgvector enables horizontal scaling. Qwen3-4B (4B vs 7B parameters) reduces inference costs by 60%. Batch processing limits ensure resource control.

### Technical Standards Issues

⚠️ **ML Framework Deviation**: Constitution specifies Mistral 7B/Phi-3-mini, but feature spec uses Qwen3-4B (4B parameters) for enhanced financial text comprehension and 256K context window.

**JUSTIFICATION REQUIRED**: Qwen3-4B provides superior financial document analysis capabilities with larger context window for full 10-K processing and 60% cost reduction vs 7B models.

⚠️ **Storage Architecture**: Constitution specifies PostgreSQL + MinIO, but feature uses PostgreSQL + local filesystem for document storage.

**JUSTIFICATION REQUIRED**: Simplified architecture reduces complexity for MVP while PostgreSQL + pgvector eliminates need for separate vector database. MinIO can be added in Phase 2 scaling.

### Post-Phase 1 Re-Evaluation ✅

**Design Artifacts Review**: All Phase 1 deliverables (data-model.md, contracts/, quickstart.md, agent context) have been completed and reviewed against constitution principles.

**Constitution Compliance Confirmed**:
- ✅ **AI-First Analysis**: Multi-dimensional sentiment analysis with Qwen3-4B properly integrated
- ✅ **Data Accuracy**: 85% accuracy requirements built into data model and API contracts
- ✅ **Performance**: <60s processing constraints reflected in API design and database schema
- ✅ **API-First**: Complete REST API specification created with all capabilities exposed
- ✅ **Scalability**: PostgreSQL + pgvector architecture supports horizontal scaling needs

**Justified Deviations**: Model choice (Qwen3-4B vs Mistral 7B) and storage architecture (local filesystem vs MinIO) documented in complexity tracking with business rationale. Both deviations reduce complexity and cost while maintaining constitutional compliance.

**Gate Status**: PASSED - Ready to proceed to Phase 2 (Task Planning)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/           # SQLAlchemy ORM models (User, Company, Report, Analysis)
│   ├── services/         # Business logic (sentiment_analyzer, sec_downloader, ixbrl_parser)
│   ├── api/             # FastAPI routers and endpoints
│   │   ├── v1/          # API version 1 routes
│   │   ├── auth/        # Authentication endpoints
│   │   └── webhooks/    # External integration hooks
│   ├── core/            # Configuration, security, dependencies
│   ├── database/        # Database configuration and migrations
│   └── utils/           # Shared utilities (parsing, validation)
├── tests/
│   ├── unit/            # Unit tests for services and models
│   ├── integration/     # API integration tests
│   └── performance/     # Load testing and benchmarks
├── requirements.txt     # Python dependencies
└── alembic/            # Database migrations

frontend/
├── src/
│   ├── components/      # Reusable React components
│   │   ├── analysis/    # Analysis-specific components
│   │   ├── dashboard/   # Dashboard visualizations
│   │   └── common/      # Shared UI components
│   ├── pages/           # Route-level page components
│   ├── services/        # API client and data fetching
│   ├── hooks/           # Custom React hooks
│   ├── utils/           # Frontend utilities
│   └── types/           # TypeScript type definitions
├── tests/
│   ├── components/      # Component unit tests
│   ├── integration/     # End-to-end tests
│   └── __mocks__/       # Test mocks and fixtures
├── package.json         # Node dependencies
└── public/             # Static assets

docs/
├── api/                # API documentation
├── deployment/         # Deployment guides
└── development/        # Development setup
```

**Structure Decision**: Web application structure selected due to FastAPI backend + React frontend architecture. Backend handles ML inference and data processing, frontend provides user interface and visualizations. Clear separation enables independent scaling and development.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Qwen3-4B vs Mistral 7B/Phi-3-mini | Financial documents require 256K context window for full 10-K processing. Enhanced financial text comprehension and 60% cost reduction critical for MVP viability. | Mistral 7B lacks financial domain optimization and has smaller context window limiting document analysis capabilities. Phi-3-mini insufficient for complex financial narrative understanding. |
| Local filesystem vs MinIO | MVP requires simplified deployment and reduced operational complexity. PostgreSQL + pgvector eliminates separate vector database need. | MinIO adds deployment complexity, additional service dependencies, and operational overhead without immediate MVP benefit. Can migrate to object storage in Phase 2 scaling. |
