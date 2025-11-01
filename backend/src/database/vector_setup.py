"""
PostgreSQL pgvector extension setup and vector operations.

Handles pgvector extension management, vector index creation,
and vector similarity search operations.
"""

import logging
from typing import List, Tuple, Optional, Any
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_db_session_context, engine
from ..core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class VectorSetupManager:
    """
    Manages pgvector extension setup and vector operations.
    """
    
    def __init__(self):
        self.extension_enabled = False
        self.indexes_created = False
    
    def check_pgvector_availability(self) -> bool:
        """
        Check if pgvector extension is available in PostgreSQL.
        
        Returns:
            bool: True if pgvector is available, False otherwise
        """
        try:
            with get_db_session_context() as session:
                # Check if extension is available
                result = session.execute(
                    text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
                )
                
                available = result.fetchone() is not None
                
                if available:
                    logger.info("pgvector extension is available")
                else:
                    logger.warning("pgvector extension is not available - falling back to JSONB storage")
                
                return available
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to check pgvector availability: {e}")
            return False
    
    def enable_pgvector_extension(self) -> bool:
        """
        Enable the pgvector extension in PostgreSQL.
        
        Returns:
            bool: True if extension was enabled successfully, False otherwise
        """
        try:
            with get_db_session_context() as session:
                # Try to create the extension
                session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                
                # Verify extension is loaded
                result = session.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                )
                
                enabled = result.fetchone() is not None
                
                if enabled:
                    logger.info("pgvector extension enabled successfully")
                    self.extension_enabled = True
                else:
                    logger.warning("Failed to enable pgvector extension")
                    
                return enabled
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to enable pgvector extension: {e}")
            return False
    
    def check_vector_column_exists(self, table_name: str, column_name: str) -> bool:
        """
        Check if a vector column exists in the specified table.
        
        Args:
            table_name: Name of the table to check
            column_name: Name of the vector column
            
        Returns:
            bool: True if vector column exists, False otherwise
        """
        try:
            inspector = inspect(engine)
            columns = inspector.get_columns(table_name)
            
            for column in columns:
                if column['name'] == column_name:
                    # Check if it's a vector type
                    column_type = str(column['type']).lower()
                    return 'vector' in column_type
            
            return False
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to check vector column existence: {e}")
            return False
    
    def create_vector_indexes(self) -> bool:
        """
        Create vector indexes for similarity search performance.
        
        Returns:
            bool: True if indexes were created successfully, False otherwise
        """
        try:
            # Obtain a connection; prefer session bind, fallback to module engine
            from sqlalchemy.engine import Connection
            conn: Optional[Connection] = None
            with get_db_session_context() as session:
                try:
                    bind = session.get_bind()
                    if bind is not None:
                        conn = bind.connect().execution_options(isolation_level="AUTOCOMMIT")
                    elif 'engine' in globals() and engine is not None:  # type: ignore[name-defined]
                        conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")  # type: ignore[misc]
                except Exception as e:
                    logger.debug(f"Autocommit connection unavailable, will fallback to non-concurrent indexes: {e}")
                # List of vector indexes to create
                vector_indexes = [
                    {
                        'name': 'idx_narrative_embeddings_vector_cosine',
                        'table': 'narrative_embeddings',
                        'column': 'embedding_vector',
                        'method': 'ivfflat',
                        'ops_class': 'vector_cosine_ops',
                        'options': 'lists = 100'
                    },
                    {
                        'name': 'idx_narrative_embeddings_vector_l2',
                        'table': 'narrative_embeddings', 
                        'column': 'embedding_vector',
                        'method': 'ivfflat',
                        'ops_class': 'vector_l2_ops',
                        'options': 'lists = 100'
                    },
                    {
                        'name': 'idx_narrative_embeddings_vector_ip',
                        'table': 'narrative_embeddings',
                        'column': 'embedding_vector', 
                        'method': 'ivfflat',
                        'ops_class': 'vector_ip_ops',
                        'options': 'lists = 100'
                    }
                ]
                
                created_count = 0
                
                for index_config in vector_indexes:
                    try:
                        # Check if vector column exists before creating index
                        if not self.check_vector_column_exists(
                            index_config['table'], 
                            index_config['column']
                        ):
                            logger.warning(
                                f"Vector column {index_config['table']}.{index_config['column']} "
                                "does not exist, skipping index creation"
                            )
                            continue
                        
                        # Create the index
                        index_sql = (
                            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_config['name']} "
                            f"ON {index_config['table']} "
                            f"USING {index_config['method']} ({index_config['column']} {index_config['ops_class']}) "
                            f"WITH ({index_config['options']})"
                        )
                        
                        if conn is not None:
                            try:
                                conn.execute(text(index_sql))
                            except SQLAlchemyError:
                                # Fallback: retry without CONCURRENTLY if autocommit not supported by DB
                                if 'CONCURRENTLY' in index_sql.upper():
                                    non_concurrent_sql = index_sql.upper().replace(' CONCURRENTLY', '')
                                    conn.execute(text(non_concurrent_sql))
                                else:
                                    raise
                        else:
                            # No autocommit-capable connection; run without CONCURRENTLY using session
                            non_concurrent_sql = index_sql.upper().replace(' CONCURRENTLY', '')
                            session.execute(text(non_concurrent_sql))
                        logger.info(f"Created vector index: {index_config['name']}")
                        created_count += 1
                        
                    except SQLAlchemyError as e:
                        logger.error(f"Failed to create index {index_config['name']}: {e}")
                        continue
                
                if created_count > 0:
                    self.indexes_created = True
                    logger.info(f"Successfully created {created_count} vector indexes")
                
                return created_count > 0
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create vector indexes: {e}")
            return False
    
    def create_performance_indexes(self) -> bool:
        """
        Create additional performance indexes for non-vector columns.
        
        Returns:
            bool: True if indexes were created successfully, False otherwise
        """
        try:
            # Obtain a connection; prefer session bind, fallback to module engine
            from sqlalchemy.engine import Connection
            conn: Optional[Connection] = None
            with get_db_session_context() as session:
                try:
                    bind = session.get_bind()
                    if bind is not None:
                        conn = bind.connect().execution_options(isolation_level="AUTOCOMMIT")
                    elif 'engine' in globals() and engine is not None:  # type: ignore[name-defined]
                        conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")  # type: ignore[misc]
                except Exception as e:
                    logger.debug(f"Autocommit connection unavailable, will fallback to non-concurrent indexes: {e}")
                # Performance indexes from data-model.md with existence checks
                performance_indexes = [
                    {
                        'sql': "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_ticker_symbol ON companies(ticker_symbol)",
                        'table': 'companies',
                        'columns': ['ticker_symbol'],
                    },
                    {
                        'sql': "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_reports_company_filing_date ON financial_reports(company_id, filing_date DESC)",
                        'table': 'financial_reports',
                        'columns': ['company_id', 'filing_date'],
                    },
                    {
                        'sql': "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narrative_analyses_report_id ON narrative_analyses(report_id)",
                        'table': 'narrative_analyses',
                        'columns': ['report_id'],
                    },
                    {
                        'sql': "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narrative_deltas_company_created ON narrative_deltas(company_id, created_at DESC)",
                        'table': 'narrative_deltas',
                        'columns': ['company_id', 'created_at'],
                    },
                    {
                        'sql': "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_user_read_created ON alerts(user_id, is_read, created_at DESC)",
                        'table': 'alerts',
                        'columns': ['user_id', 'is_read', 'created_at'],
                    },
                    {
                        'sql': "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_narrative_embeddings_analysis_section ON narrative_embeddings(analysis_id, section_type)",
                        'table': 'narrative_embeddings',
                        'columns': ['analysis_id', 'section_type'],
                    },
                ]
                
                created_count = 0
                
                inspector = None
                try:
                    inspector = inspect(bind) if 'bind' in locals() and bind is not None else inspect(engine)
                except Exception:
                    inspector = None

                for index in performance_indexes:
                    try:
                        # Skip index if required columns are missing
                        if inspector is not None:
                            existing_cols = {c['name'] for c in inspector.get_columns(index['table'])}
                            if not set(index['columns']).issubset(existing_cols):
                                logger.warning(
                                    f"Skipping index on {index['table']} - missing columns: "
                                    f"{set(index['columns']) - existing_cols}"
                                )
                                continue

                        sql_stmt = index['sql']

                        if conn is not None:
                            try:
                                conn.execute(text(sql_stmt))
                            except SQLAlchemyError:
                                # Fallback: retry without CONCURRENTLY
                                if 'CONCURRENTLY' in sql_stmt.upper():
                                    non_concurrent_sql = sql_stmt.upper().replace(' CONCURRENTLY', '')
                                    conn.execute(text(non_concurrent_sql))
                                else:
                                    raise
                        else:
                            # No autocommit-capable connection; run without CONCURRENTLY using session
                            non_concurrent_sql = sql_stmt.upper().replace(' CONCURRENTLY', '')
                            session.execute(text(non_concurrent_sql))
                        created_count += 1
                        logger.info(f"Created performance index: {sql_stmt.split('idx_')[1].split(' ON')[0]}")
                        
                    except SQLAlchemyError as e:
                        logger.error(f"Failed to create performance index: {e}")
                        continue
                
                logger.info(f"Successfully created {created_count} performance indexes")
                return created_count > 0
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create performance indexes: {e}")
            return False
    
    def setup_vector_environment(self) -> dict:
        """
        Complete vector environment setup including extension and indexes.
        
        Returns:
            dict: Setup status and results
        """
        setup_results = {
            'pgvector_available': False,
            'pgvector_enabled': False,
            'vector_indexes_created': False,
            'performance_indexes_created': False,
            'fallback_mode': False
        }
        
        try:
            # Check if pgvector is available
            setup_results['pgvector_available'] = self.check_pgvector_availability()
            
            if setup_results['pgvector_available']:
                # Enable pgvector extension
                setup_results['pgvector_enabled'] = self.enable_pgvector_extension()
                
                if setup_results['pgvector_enabled']:
                    # Create vector indexes
                    setup_results['vector_indexes_created'] = self.create_vector_indexes()
                else:
                    logger.warning("pgvector extension not enabled, using JSONB fallback")
                    setup_results['fallback_mode'] = True
            else:
                logger.warning("pgvector not available, using JSONB fallback")
                setup_results['fallback_mode'] = True
            
            # Create performance indexes (always)
            setup_results['performance_indexes_created'] = self.create_performance_indexes()
            
            # Log setup summary
            if setup_results['pgvector_enabled']:
                logger.info("Vector environment setup completed with pgvector support")
            else:
                logger.info("Vector environment setup completed in JSONB fallback mode")
                
            return setup_results
            
        except Exception as e:
            logger.error(f"Vector environment setup failed: {e}")
            setup_results['fallback_mode'] = True
            return setup_results


def setup_vector_environment() -> dict:
    """
    Convenience function to setup vector environment.
    
    Returns:
        dict: Setup status and results
    """
    manager = VectorSetupManager()
    return manager.setup_vector_environment()


def perform_similarity_search(
    query_vector: List[float],
    limit: int = 10,
    threshold: Optional[float] = None,
    section_type: Optional[str] = None
) -> List[Tuple[str, float]]:
    """
    Perform vector similarity search on narrative embeddings.
    
    Args:
        query_vector: Query vector for similarity search
        limit: Maximum number of results to return
        threshold: Similarity threshold (0.0 to 1.0)
        section_type: Optional filter by section type
        
    Returns:
        List of tuples containing (embedding_id, similarity_score)
    """
    try:
        with get_db_session_context() as session:
            # Build base query
            base_query = """
            SELECT 
                id,
                1 - (embedding_vector <=> %s::vector) as similarity_score
            FROM narrative_embeddings
            """
            
            where_conditions = []
            params = [str(query_vector)]
            
            # Add section type filter if provided
            if section_type:
                where_conditions.append("section_type = %s")
                params.append(section_type)
            
            # Add threshold filter if provided
            if threshold:
                where_conditions.append("1 - (embedding_vector <=> %s::vector) >= %s")
                params.extend([str(query_vector), threshold])
            
            # Construct final query
            if where_conditions:
                query = f"{base_query} WHERE {' AND '.join(where_conditions)}"
            else:
                query = base_query
            
            query += " ORDER BY embedding_vector <=> %s::vector LIMIT %s"
            params.extend([str(query_vector), limit])
            
            # Execute search
            result = session.execute(text(query), params)
            results = [(row[0], row[1]) for row in result.fetchall()]
            
            logger.info(f"Similarity search returned {len(results)} results")
            return results
            
    except SQLAlchemyError as e:
        logger.error(f"Similarity search failed: {e}")
        raise DatabaseError(f"Vector similarity search failed: {e}")


def get_vector_stats() -> dict:
    """
    Get statistics about vector storage and indexes.
    
    Returns:
        dict: Vector storage statistics
    """
    try:
        with get_db_session_context() as session:
            stats = {}
            
            # Count total embeddings
            result = session.execute(text("SELECT COUNT(*) FROM narrative_embeddings"))
            stats['total_embeddings'] = result.scalar()
            
            # Check if pgvector is enabled
            result = session.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            stats['pgvector_enabled'] = result.fetchone() is not None
            
            # Get index information
            result = session.execute(text("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE indexname LIKE 'idx_%vector%'
            """))
            stats['vector_indexes'] = [row[0] for row in result.fetchall()]
            
            # Get table size
            result = session.execute(text("""
                SELECT pg_size_pretty(pg_total_relation_size('narrative_embeddings'))
            """))
            stats['table_size'] = result.scalar()
            
            return stats
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to get vector stats: {e}")
        return {'error': str(e)}
