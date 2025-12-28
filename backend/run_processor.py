import uuid
from src.core.config import get_settings
from src.database.connection import SessionLocal, init_database
from src.models.financial_report import FinancialReport
from src.services.document_processor import DocumentProcessor

def run_processing():
    # Override settings for local DB
    from src.core.config import get_settings
    settings = get_settings()
    settings.database_url = "postgresql://ntufar@localhost:5432/fna_development"
    
    from src.database.connection import init_database
    init_database()
    
    from src.database.connection import SessionLocal
    db = SessionLocal()
    
    try:
        report_id = "ce3297ea-ceae-46c3-bc6c-a75556991217"
        report = db.query(FinancialReport).filter(FinancialReport.id == report_id).first()
        
        if not report:
            print(f"Report {report_id} not found")
            return
        
        print(f"Processing report: {report.id}")
        processor = DocumentProcessor()
        result = processor.process_financial_report(report, force_reprocess=True)
        
        print("Processing Summary:")
        print(result.get_summary())
        
        if result.is_successful():
            print("Successfully processed report!")
            db.commit()
        else:
            print("Processing failed.")
            for error in result.errors:
                print(f"Error: {error}")
            db.rollback()
            
    finally:
        db.close()

if __name__ == "__main__":
    run_processing()
