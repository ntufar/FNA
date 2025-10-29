-- FNA Database Setup Script
-- Run with: psql -h localhost -U postgres -f setup_database.sql

-- Create database
DROP DATABASE IF EXISTS fna_development;
CREATE DATABASE fna_development;

-- Connect to the new database
\c fna_development;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT extname FROM pg_extension WHERE extname = 'vector';

-- Create initial schema (will be managed by Alembic later)
CREATE SCHEMA IF NOT EXISTS fna;

-- Grant permissions (adjust as needed for production)
GRANT ALL PRIVILEGES ON DATABASE fna_development TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA fna TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
