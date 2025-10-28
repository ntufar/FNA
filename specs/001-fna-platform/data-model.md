# Data Model: Financial Narrative Analyzer Platform

**Date**: 2025-10-29  
**Based on**: Feature specification entities and functional requirements

## Core Entities

### Company
Represents public companies being analyzed.

**Fields**:
- `id` (UUID, Primary Key)
- `ticker_symbol` (String, Unique, Index) - NYSE/NASDAQ symbol
- `company_name` (String) - Official company name
- `sector` (String) - Industry sector classification
- `industry` (String) - Specific industry category
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Relationships**:
- One-to-Many: Financial Reports
- One-to-Many: User Alert Preferences

**Validation Rules**:
- ticker_symbol: 1-5 uppercase characters, alphanumeric
- company_name: Required, 1-255 characters
- sector/industry: Optional, standardized categories

---

### User
System users with authentication and subscription management.

**Fields**:
- `id` (UUID, Primary Key)
- `email` (String, Unique) - Authentication identifier
- `password_hash` (String) - Hashed password
- `subscription_tier` (Enum) - Basic, Pro, Enterprise
- `created_at` (Timestamp)
- `last_login` (Timestamp)
- `is_active` (Boolean) - Account status

**Relationships**:
- One-to-Many: Analysis History
- One-to-Many: Alert Preferences
- One-to-Many: File Uploads

**Validation Rules**:
- email: Valid email format, unique across system
- subscription_tier: Must be valid tier enum value
- Account deactivation preserves data but blocks access

---

### FinancialReport
Document entity representing SEC filings and uploaded reports.

**Fields**:
- `id` (UUID, Primary Key)
- `company_id` (UUID, Foreign Key → Company)
- `report_type` (Enum) - 10-K, 10-Q, 8-K, Annual, Other
- `fiscal_period` (String) - Q1/Q2/Q3/Q4 YYYY or FY YYYY
- `filing_date` (Date) - Official SEC filing date
- `report_url` (String, Optional) - SEC.gov source URL
- `file_path` (String) - Local storage path
- `file_format` (Enum) - PDF, HTML, TXT, iXBRL
- `file_size_bytes` (Integer)
- `download_source` (Enum) - SEC_AUTO, MANUAL_UPLOAD
- `processing_status` (Enum) - PENDING, PROCESSING, COMPLETED, FAILED
- `created_at` (Timestamp)
- `processed_at` (Timestamp, Optional)

**Relationships**:
- Many-to-One: Company
- One-to-Many: Narrative Analyses
- One-to-Many: Narrative Deltas (as base or comparison report)

**State Transitions**:
- PENDING → PROCESSING (on analysis start)
- PROCESSING → COMPLETED (successful analysis)
- PROCESSING → FAILED (analysis error)
- FAILED → PENDING (retry allowed)

**Validation Rules**:
- file_size_bytes: Maximum 50MB (52,428,800 bytes)
- file_format: Must match actual file content type
- fiscal_period: Must follow standard format patterns

---

### NarrativeAnalysis
Analysis results from LLM processing of financial report narratives.

**Fields**:
- `id` (UUID, Primary Key)
- `report_id` (UUID, Foreign Key → FinancialReport)
- `optimism_score` (Float) - Range 0.0-1.0
- `optimism_confidence` (Float) - Range 0.0-1.0
- `risk_score` (Float) - Range 0.0-1.0
- `risk_confidence` (Float) - Range 0.0-1.0
- `uncertainty_score` (Float) - Range 0.0-1.0
- `uncertainty_confidence` (Float) - Range 0.0-1.0
- `key_themes` (JSON Array) - Extracted narrative themes
- `risk_indicators` (JSON Array) - Modal verbs and risk language
- `narrative_sections` (JSON Object) - Extracted MD&A, CEO letter text
- `financial_metrics` (JSON Object, Optional) - Cross-referenced iXBRL data
- `processing_time_seconds` (Integer) - Performance tracking
- `model_version` (String) - LLM model identifier
- `created_at` (Timestamp)

**Relationships**:
- Many-to-One: Financial Report
- One-to-Many: Narrative Deltas (as base or comparison analysis)

**Validation Rules**:
- All score fields: Range 0.0-1.0, required
- All confidence fields: Range 0.0-1.0, required
- key_themes: Array of strings, max 50 themes
- processing_time_seconds: Must be ≤ 60 per constitution

---

### NarrativeDelta
Comparison entity linking two reports with calculated change metrics.

**Fields**:
- `id` (UUID, Primary Key)
- `company_id` (UUID, Foreign Key → Company)
- `base_analysis_id` (UUID, Foreign Key → NarrativeAnalysis) - Earlier report
- `comparison_analysis_id` (UUID, Foreign Key → NarrativeAnalysis) - Later report
- `optimism_delta` (Float) - Change in optimism (-1.0 to 1.0)
- `risk_delta` (Float) - Change in risk score (-1.0 to 1.0)
- `uncertainty_delta` (Float) - Change in uncertainty (-1.0 to 1.0)
- `overall_sentiment_delta` (Float) - Composite sentiment change
- `themes_added` (JSON Array) - New themes in comparison report
- `themes_removed` (JSON Array) - Themes absent in comparison report
- `themes_evolved` (JSON Object) - Themes with significant emphasis changes
- `shift_significance` (Enum) - MINOR, MODERATE, MAJOR, CRITICAL
- `created_at` (Timestamp)

**Relationships**:
- Many-to-One: Company
- Many-to-One: Base Analysis
- Many-to-One: Comparison Analysis
- One-to-Many: Alerts (if thresholds exceeded)

**Validation Rules**:
- Delta fields: Range -1.0 to 1.0
- base_analysis and comparison_analysis: Must be different, same company
- Temporal constraint: comparison_analysis must be more recent than base_analysis

---

### Alert
Notification entity for significant narrative changes.

**Fields**:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key → User)
- `company_id` (UUID, Foreign Key → Company)
- `delta_id` (UUID, Foreign Key → NarrativeDelta)
- `alert_type` (Enum) - SENTIMENT_SHIFT, RISK_INCREASE, THEME_CHANGE
- `threshold_percentage` (Float) - User-configured trigger threshold
- `actual_change_percentage` (Float) - Measured change that triggered alert
- `alert_message` (Text) - Human-readable alert description
- `is_read` (Boolean) - User acknowledgment status
- `delivery_method` (Enum) - IN_APP, EMAIL, WEBHOOK
- `created_at` (Timestamp)
- `delivered_at` (Timestamp, Optional)

**Relationships**:
- Many-to-One: User
- Many-to-One: Company  
- Many-to-One: Narrative Delta

**Validation Rules**:
- threshold_percentage: Range 5.0-50.0 (per specification)
- actual_change_percentage: Must exceed threshold_percentage
- alert_message: Required, max 500 characters

---

### NarrativeEmbedding
Vector embeddings for semantic search and similarity analysis.

**Fields**:
- `id` (UUID, Primary Key)
- `analysis_id` (UUID, Foreign Key → NarrativeAnalysis)
- `section_type` (Enum) - MD_A, CEO_LETTER, RISK_FACTORS, OTHER
- `text_content` (Text) - Original text section
- `embedding_vector` (Vector) - 384-dimension pgvector
- `chunk_index` (Integer) - Position in document
- `created_at` (Timestamp)

**Relationships**:
- Many-to-One: Narrative Analysis

**Vector Operations**:
- Similarity search: `embedding_vector <-> query_vector`
- Index: IVFFlat on embedding_vector for fast similarity search

---

## Database Indexes

### Performance Indexes
- `companies.ticker_symbol` (Unique)
- `financial_reports.company_id, filing_date` (Composite)
- `narrative_analyses.report_id`
- `narrative_deltas.company_id, created_at` (Composite)
- `alerts.user_id, is_read, created_at` (Composite)

### Vector Indexes
- `narrative_embeddings.embedding_vector` (IVFFlat with vector_cosine_ops)

## Data Relationships Diagram

```text
Company (1) ──── (N) FinancialReport (1) ──── (N) NarrativeAnalysis
   │                                               │
   │                                               │
   └── (N) Alert ←── (N) NarrativeDelta ──────────┘
   │                        │
   │                        └── (1) NarrativeAnalysis (comparison)
   │
   └── (N) User ──── (N) Alert
           │
           └── (N) AlertPreference
```

## Storage Estimates

Based on expected usage (100 companies, 400 reports/year, 5-year retention):

| Entity | Estimated Records | Storage per Record | Total Storage |
|--------|------------------|-------------------|---------------|
| Company | 100 | 1KB | 100KB |
| FinancialReport | 2,000/year | 2KB + file storage | 40MB/year |
| NarrativeAnalysis | 2,000/year | 50KB | 100MB/year |
| NarrativeDelta | 1,000/year | 10KB | 10MB/year |
| NarrativeEmbedding | 20,000/year | 2KB | 40MB/year |
| Alert | 500/year | 1KB | 500KB/year |

**Total structured data growth**: ~200MB/year
**File storage growth**: ~2GB/year (average 1MB per report)

Vector search performance should remain sub-200ms with proper indexing up to 100K embeddings.

