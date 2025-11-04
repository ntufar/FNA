# Tasks: Financial Narrative Analyzer Platform

**Input**: Design documents from `/specs/001-fna-platform/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/` (per plan.md structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan.md (backend/, frontend/, docs/)
- [x] T002 Initialize Python 3.11+ backend project with FastAPI dependencies in backend/requirements.txt
- [x] T003 [P] Initialize React 18+ TypeScript frontend project with Vite in frontend/package.json
- [x] T004 [P] Configure PostgreSQL database with pgvector extension
- [x] T005 [P] Configure backend linting and formatting (black, isort, mypy)
- [x] T006 [P] Configure frontend linting and formatting (ESLint, Prettier, TypeScript)
- [x] T007 Setup Alembic database migrations framework in backend/alembic/
- [x] T008 Create environment configuration files (.env templates for backend and frontend)
- [x] T009 [P] Install and configure Qwen3-4B model with 4-bit quantization per research.md
- [x] T010 [P] Install Arelle library for iXBRL parsing per research.md
- [x] T011 [P] Configure sentence-transformers MiniLM-L6-v2 for embeddings per research.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T012 Setup database schema and create all entity tables in backend/alembic/versions/
- [x] T013 [P] Create base SQLAlchemy models (User, Company) in backend/src/models/base.py
- [x] T014 [P] Implement JWT authentication middleware in backend/src/core/security.py
- [x] T015 [P] Setup FastAPI routing structure in backend/src/api/v1/
- [x] T016 [P] Create database connection and session management in backend/src/database/connection.py
- [x] T017 [P] Implement error handling and logging infrastructure in backend/src/core/exceptions.py
- [x] T018 [P] Configure CORS and security middleware in backend/src/main.py
- [x] T019 [P] Create API client service in frontend/src/services/api.ts
- [x] T020 [P] Setup React routing and authentication context in frontend/src/
- [x] T021 [P] Configure pgvector extension and create vector indexes per data-model.md

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Analyze Financial Reports (Priority: P1) 🎯 MVP

**Goal**: Enable users to upload reports or auto-download from SEC.gov and receive multi-dimensional sentiment analysis

**Independent Test**: Upload a PDF report or enter ticker "AAPL" → receive optimism, risk, uncertainty scores with themes in <60 seconds

### Implementation for User Story 1

- [x] T022 [P] [US1] Create User model with authentication in backend/src/models/user.py
- [x] T023 [P] [US1] Create Company model with ticker validation in backend/src/models/company.py
- [x] T024 [P] [US1] Create FinancialReport model with processing status in backend/src/models/financial_report.py
- [x] T025 [P] [US1] Create NarrativeAnalysis model with multi-dimensional scores in backend/src/models/narrative_analysis.py
- [x] T026 [US1] Implement SentimentAnalyzer service with Qwen3-4B in backend/src/services/sentiment_analyzer.py
- [x] T027 [US1] Implement SECDownloader service with EDGAR API in backend/src/services/sec_downloader.py
- [x] T028 [US1] Implement iXBRLParser service with Arelle in backend/src/services/ixbrl_parser.py
- [x] T029 [US1] Implement DocumentProcessor service orchestrating parsing and analysis in backend/src/services/document_processor.py
- [x] T030 [US1] Create authentication endpoints (/auth/login, /auth/register) in backend/src/api/v1/auth.py
- [x] T031 [US1] Create company management endpoints (/companies) in backend/src/api/v1/companies.py
- [x] T032 [US1] Create report upload endpoint (/reports/upload) in backend/src/api/v1/reports.py
- [x] T033 [US1] Create report download endpoint (/reports/download) in backend/src/api/v1/reports.py
- [x] T034 [US1] Create analysis retrieval endpoint (/reports/{id}/analysis) in backend/src/api/v1/reports.py
- [x] T035 [US1] Create login/register components in frontend/src/components/auth/
- [x] T036 [US1] Create company search component in frontend/src/components/companies/CompanySearch.tsx
- [x] T037 [US1] Create file upload component in frontend/src/components/reports/ReportUpload.tsx
- [x] T038 [US1] Create analysis display component in frontend/src/components/analysis/AnalysisResults.tsx
- [x] T039 [US1] Create main analysis page in frontend/src/pages/AnalysisPage.tsx
- [x] T040 [US1] Implement async processing with status updates for long-running analysis
- [x] T041 [US1] Add input validation and error handling for file uploads and ticker symbols
- [x] T042 [US1] Add logging for analysis operations and SEC API interactions

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compare Narrative Changes Over Time (Priority: P2)

**Goal**: Enable comparison of reports from same company to identify narrative shifts and generate delta analysis

**Independent Test**: Upload/download two AAPL reports → view narrative delta showing theme changes and sentiment shifts

### Implementation for User Story 2

- [x] T043 [P] [US2] Create NarrativeDelta model with change metrics in backend/src/models/narrative_delta.py
- [x] T044 [US2] Implement DeltaAnalyzer service for report comparison in backend/src/services/delta_analyzer.py
- [x] T045 [US2] Create comparison endpoint (/analysis/compare) in backend/src/api/v1/analysis.py
- [x] T046 [US2] Create report comparison interface in frontend/src/components/analysis/ReportComparison.tsx
- [x] T047 [US2] Create delta visualization component in frontend/src/components/analysis/DeltaVisualization.tsx
- [x] T048 [US2] Create comparison results page in frontend/src/pages/ComparisonPage.tsx
- [x] T049 [US2] Implement theme evolution tracking (added, removed, changed emphasis)
- [x] T050 [US2] Add significance calculation (MINOR, MODERATE, MAJOR, CRITICAL) based on change thresholds
- [x] T051 [US2] Integrate comparison functionality with existing analysis workflow

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Dashboard Visualization and Trends (Priority: P3)

**Goal**: Provide interactive dashboards showing sentiment trends and timeline visualizations across multiple reports

**Independent Test**: View dashboard for company with multiple reports → see timeline charts and trend analysis

### Implementation for User Story 3

- [x] T052 [P] [US3] Create Alert model with user preferences in backend/src/models/alert.py
- [x] T053 [P] [US3] Create NarrativeEmbedding model for vector search in backend/src/models/narrative_embedding.py
- [x] T054 [US3] Implement TrendAnalyzer service for historical patterns in backend/src/services/trend_analyzer.py
- [x] T055 [US3] Implement AlertService with configurable thresholds in backend/src/services/alert_service.py
- [x] T056 [US3] Create trends endpoint (/companies/{id}/trends) in backend/src/api/v1/companies.py
- [x] T057 [US3] Create alerts endpoints (/alerts) in backend/src/api/v1/alerts.py
- [x] T058 [US3] Create dashboard visualization components in frontend/src/components/dashboard/
- [x] T059 [US3] Create timeline chart component using Recharts in frontend/src/components/charts/TimelineChart.tsx
- [x] T060 [US3] Create sentiment trend component in frontend/src/components/dashboard/SentimentTrends.tsx
- [x] T061 [US3] Create alerts management component in frontend/src/components/alerts/AlertsPanel.tsx
- [x] T062 [US3] Create main dashboard page in frontend/src/pages/DashboardPage.tsx
- [x] T063 [US3] Implement user-configurable alert thresholds (5-50% range per spec)
- [x] T064 [US3] Add industry-based intelligent defaults for alert thresholds
- [x] T065 [US3] Create alert preferences management interface

**Checkpoint**: All core user stories should now be independently functional

---

## Phase 6: User Story 4 - API Access for Integration (Priority: P4)

**Goal**: Provide programmatic API access for enterprise integration and batch processing

**Independent Test**: Make authenticated API calls → receive structured sentiment data and process batch requests

### Implementation for User Story 4

- [x] T066 [P] [US4] Implement API key authentication in backend/src/core/api_auth.py
- [x] T067 [P] [US4] Create batch processing endpoint (/reports/batch) in backend/src/api/v1/reports.py
- [x] T068 [US4] Implement BatchProcessor service with 10-report limit in backend/src/services/batch_processor.py
- [x] T069 [US4] Create vector similarity search endpoint (/search/similar) in backend/src/api/v1/analysis.py
- [x] T070 [US4] Implement EmbeddingService with sentence-transformers in backend/src/services/embedding_service.py
- [x] T071 [US4] Add rate limiting middleware per API tier (Basic/Pro/Enterprise) in backend/src/middleware/rate_limiting.py
- [x] T072 [US4] Implement subscription tier access control in backend/src/middleware/subscription_check.py
- [x] T073 [US4] Create webhook endpoints for enterprise notifications in backend/src/api/webhooks/handlers.py
- [x] T074 [US4] Add comprehensive API documentation and examples in docs/api/
- [x] T075 [US4] Create batch status tracking and progress updates (implemented in BatchProcessor)
- [x] T076 [US4] Implement async job queue for batch processing

**Checkpoint**: All user stories should now be fully functional with enterprise features

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T077 [P] Add comprehensive error handling and user-friendly error messages across all endpoints
- [ ] T078 [P] Implement caching for expensive operations (model inference, embeddings)
- [ ] T079 [P] Add performance monitoring and metrics collection
- [ ] T080 [P] Create comprehensive API documentation in docs/api/
- [ ] T081 [P] Add security hardening (input sanitization, SQL injection prevention)
- [ ] T082 [P] Implement cross-referenced financial metrics analysis per FR-020
- [ ] T083 [P] Add data export functionality (Excel, CSV) for analysis results
- [ ] T084 [P] Create admin interface for user and subscription management
- [ ] T085 [P] Add system health checks and monitoring endpoints
- [ ] T086 [P] Optimize database queries and add missing indexes
- [ ] T087 [P] Create deployment scripts and production configuration
- [ ] T088 Run quickstart.md validation to ensure setup process works
- [ ] T089 [P] Implement accuracy validation system for FR-011 compliance (85% sentiment classification vs human experts)
- [ ] T090 [P] Create data retention and lifecycle management system for FR-015 indefinite storage requirements
- [ ] T091 Performance optimization and load testing validation
- [ ] T092 Security audit and penetration testing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 models but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses US1/US2 data but independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Exposes existing functionality via API

### Within Each User Story

- Models before services
- Services before endpoints  
- Backend implementation before frontend components
- Core functionality before integration and UI
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task T022: "Create User model with authentication in backend/src/models/user.py"
Task T023: "Create Company model with ticker validation in backend/src/models/company.py"
Task T024: "Create FinancialReport model with processing status in backend/src/models/financial_report.py" 
Task T025: "Create NarrativeAnalysis model with multi-dimensional scores in backend/src/models/narrative_analysis.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (Tasks T001-T011)
2. Complete Phase 2: Foundational (Tasks T012-T021) - CRITICAL
3. Complete Phase 3: User Story 1 (Tasks T022-T042)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Tasks T022-T042)
   - Developer B: User Story 2 (Tasks T043-T051)
   - Developer C: User Story 3 (Tasks T052-T065)
   - Developer D: User Story 4 (Tasks T066-T076)
3. Stories complete and integrate independently

---

## Task Count Summary

- **Total Tasks**: 92 tasks
- **Setup Phase**: 11 tasks
- **Foundational Phase**: 10 tasks (BLOCKING)
- **User Story 1 (MVP)**: 21 tasks
- **User Story 2**: 9 tasks
- **User Story 3**: 14 tasks
- **User Story 4**: 11 tasks
- **Polish Phase**: 16 tasks

### Parallel Opportunities Identified

- **Setup Phase**: 6 parallel tasks ([P] marked)
- **Foundational Phase**: 9 parallel tasks ([P] marked)
- **User Story Models**: Multiple models per story can be built in parallel
- **Cross-Story Parallelism**: All user stories can be developed simultaneously after foundational phase

### Independent Test Criteria

- **US1**: Upload/download report → receive sentiment scores in <60s
- **US2**: Compare two reports → view narrative delta analysis
- **US3**: Access dashboard → view trend charts and manage alerts
- **US4**: Make API calls → receive structured data and process batches

### Suggested MVP Scope

**Minimum Viable Product**: Complete Phases 1-3 only (Tasks T001-T042) - 42 tasks total
- Core functionality: Upload reports, auto-download from SEC, multi-dimensional analysis
- Essential features: User authentication, company management, sentiment analysis
- Ready for market validation with core value proposition

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
