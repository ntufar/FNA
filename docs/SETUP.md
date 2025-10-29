# FNA Setup Instructions

## PostgreSQL Database Setup

✅ **Database Created**: `fna_development`  
⚠️ **pgvector Extension**: Requires separate installation

### Installing pgvector Extension

The pgvector extension is not included with standard PostgreSQL 17 installation. You have several options:

#### Option 1: Install precompiled pgvector
1. Download pgvector for PostgreSQL 17 from: https://github.com/pgvector/pgvector/releases
2. Follow Windows installation instructions
3. Restart PostgreSQL service
4. Run: `.\backend\setup_database.ps1` again

#### Option 2: Use alternative vector storage
- Temporarily use FAISS with local files (as mentioned in research.md alternatives)
- Switch to pgvector later when extension is available

#### Option 3: Use PostgreSQL with JSONB for MVP
- Store embeddings as JSONB arrays temporarily
- Less efficient but functional for development/testing

### Current Status
- ✅ PostgreSQL 17 installed and running
- ✅ Database `fna_development` created  
- ✅ Schema and permissions configured
- ⚠️ pgvector extension pending installation

### Connection Details
- **Host**: localhost:5432
- **Database**: fna_development  
- **User**: postgres
- **Password**: qwerty123
