# **Product Requirements Document (PRD)**

### Product: *Financial Narrative Analyzer (FNA)*

### Owner: Nicolai Tufar

### Date: 2025-10-29

### Version: 1.0

## **1. Overview**

The **Financial Narrative Analyzer (FNA)** is an AI platform that reads,
interprets, and compares the *narrative tone and strategic messaging* in
corporate financial reports (e.g., 10-K, 10-Q, and annual reports).\
It quantifies *how management sentiment and risk disclosure evolve over
time* --- providing analysts and investors with early indicators of
strategic change or hidden distress before it's visible in financial
metrics.

## **2. Problem Statement**

Financial analysts and investors must sift through hundreds of pages of
text in corporate filings to detect subtle tone or sentiment shifts that
may signal changes in management outlook or hidden risk.\
Existing financial data tools focus on *numbers*, not *narratives*.\
This gap creates a major blind spot in understanding company trajectory,
especially for smaller firms or emerging markets where structured data
is limited.

## **3. Goals & Objectives**

  ---------------------------------------------------------------------------
  Goal              Description                             KPI
  ----------------- --------------------------------------- -----------------
  **Detect          Identify significant tone, risk, and    \>85% accuracy in
  narrative         optimism changes in management          tone
  shifts**          discussion sections across periods      classification

  **Quantify        Produce a "Narrative Sentiment Delta    Score stability
  sentiment         Score" for each company report          across test sets
  change**                                                  ±5%

  **Visualize       Provide easy-to-read comparison         Avg. user
  insights**        dashboards                              time-to-insight
                                                            \< 30s

  **Enable          Help analysts anticipate performance    Backtested
  proactive         inflections                             correlation
  investing**                                               between tone
                                                            shift and
                                                            next-quarter EPS
                                                            direction
  ---------------------------------------------------------------------------

## **4. Target Users**

  -----------------------------------------------------------------------
  Segment              Needs            Example Users
  -------------------- ---------------- ---------------------------------
  **Equity analysts /  Quick insights   Hedge funds, research firms
  fund managers**      into management  
                       tone & strategy  
                       changes          

  **Retail investors** Simplified       Individual investors using
                       summaries of     Robinhood, eToro, etc.
                       corporate        
                       narratives       

  **Corporate strategy Benchmark        IR & corporate development
  teams**              competitor       
                       communication    

  **ESG / compliance   Detect           ESG data providers
  auditors**           misleading or    
                       inconsistent     
                       language         
  -----------------------------------------------------------------------

## **5. Product Scope**

### **5.1 Core Features**

1.  **Report Ingestion & Parsing**
    -   Upload or automatically fetch annual/quarterly reports (PDF,
        HTML, TXT)
    -   Extract narrative sections (Management Discussion & Analysis,
        CEO letter)
2.  **Narrative Tone Analysis**
    -   LLM-based sentiment and tone classification (positive, neutral,
        negative, uncertain)
    -   Detect use of modal verbs ("may," "could," "should") for risk
        language
    -   Compare tone vs. previous filings
3.  **Narrative Shift Detection**
    -   Quantify how sentiment and key topics evolved (e.g., "AI
        investments," "cost pressure")
    -   Highlight new or removed themes\
    -   Output: *Narrative Delta Report* (text + chart)
4.  **Visualization Dashboard**
    -   Timeline of sentiment scores\
    -   Word clouds / topic clusters per year\
    -   Alert system: "Significant tone shift detected since last
        filing."
5.  **API Access**
    -   REST API returning tone scores, delta metrics, and key excerpts\
    -   Integration with investment research platforms

### **5.2 Future Features (Phase 2)**

-   **Predictive Correlation Engine:** link tone shift to next-quarter
    EPS / stock movement.\
-   **Multilingual support** for EU and Asian filings.\
-   **Portfolio view**: track tone across multiple holdings.

## **6. Technical Overview**

  ---------------------------------------------------------------------------
  Layer               Components                  Description
  ------------------- --------------------------- ---------------------------
  **Frontend**        React + Tailwind            Interactive dashboard and
                                                  upload interface

  **Backend**         FastAPI / Python            Handles ingestion, parsing,
                                                  analysis, storage

  **Model**           Small LLM (e.g., Mistral    Used for tone, sentiment,
                      7B, Phi-3-mini) fine-tuned  and risk extraction
                      on financial texts          

  **Embedding Store** ChromaDB or FAISS           Vector retrieval for
                                                  context and comparison

  **Data Storage**    PostgreSQL + MinIO (for     Stores metadata, reports,
                      files)                      and analytics results

  **Visualization**   Plotly or Recharts          Sentiment trends and
                                                  comparisons
  ---------------------------------------------------------------------------

## **7. Data Sources**

-   SEC EDGAR (U.S. filings)\
-   European equivalents (ESEF, AMF, FCA)\
-   Company investor relations websites\
-   Optional: news & press releases for correlation analysis

## **8. Success Metrics**

  Metric                                             Target
  -------------------------------------------------- -----------------------
  Average report processing time                     \< 60 seconds
  Accuracy of tone classification vs. human labels   ≥ 85%
  User retention after first month                   ≥ 60%
  Correlation between tone delta and EPS trend       \> 0.4 (backtested)
  Subscription conversion rate                       \> 10% of trial users

## **9. Monetization Strategy**

-   **Freemium model:** analyze up to 3 reports/month for free.\
-   **Pro Plan (€29/mo):** unlimited reports + API access.\
-   **Enterprise Plan (€299/mo):** bulk upload, integrations, export to
    Excel/Power BI.\
-   Optional: white-label API for trading platforms.

## **10. Competitive Landscape**

  ------------------------------------------------------------------------
  Competitor              Weakness            FNA Advantage
  ----------------------- ------------------- ----------------------------
  AlphaSense              Expensive           Lightweight, SMB-friendly
                          enterprise model    pricing

  Amenity Analytics       Focuses on news     Focused on filings & tone
                                              shifts

  Bloomberg Terminal      Closed ecosystem    Open API and modern UX

  ChatGPT / Gemini        Generic             Specialized in financial
                          summarization       narrative dynamics
  ------------------------------------------------------------------------

## **11. Risks & Mitigations**

  -----------------------------------------------------------------------
  Risk                   Mitigation
  ---------------------- ------------------------------------------------
  Poor accuracy on niche Industry-specific fine-tuning datasets
  industry jargon        

  Regulatory /           Use only public filings and compliant text
  compliance risk        processing

  Model drift            Regular retraining with latest filings

  Cost of LLM inference  Use quantized small models (GGUF 4-bit) and
                         cache embeddings
  -----------------------------------------------------------------------

## **12. Timeline**

  -----------------------------------------------------------------------
  Phase            Duration               Deliverables
  ---------------- ---------------------- -------------------------------
  **Phase 1 --     6 weeks                Ingestion, tone analysis, delta
  MVP**                                   computation, simple UI

  **Phase 2 --     4 weeks                Dashboard, API endpoints
  Visualization &                         
  API**                                   

  **Phase 3 --     6 weeks                EPS correlation and alert
  Prediction                              system
  Layer**                                 

  **Phase 4 --     Continuous             Marketing, partnerships, user
  Launch &                                feedback loop
  Growth**                                
  -----------------------------------------------------------------------

## **13. Example Output**

> **Company:** NVIDIA\
> **Reports Compared:** FY2023 vs FY2024\
> **Narrative Delta Score:** +18% (More optimistic)\
> **Key Themes Added:** "AI training efficiency," "cloud partnerships"\
> **Risk Tone:** -7% (Reduced uncertainty)\
> **Summary:** Management shifted tone toward growth and AI ecosystem
> expansion; decreased focus on supply chain constraints.
