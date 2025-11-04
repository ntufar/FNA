"""
Quickstart Validation Script for FNA Platform.

Validates that the quickstart setup process works correctly by testing:
1. Environment configuration
2. Database connectivity
3. Service availability (LM Studio, Arelle)
4. API endpoints
5. Basic functionality

Run this after completing the quickstart guide to verify setup.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import requests
from datetime import datetime

# Add backend/src to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))

try:
    from src.core.config import get_settings
    from src.database.connection import get_db_session
    from src.services.sentiment_analyzer import SentimentAnalyzer
    from src.services.ixbrl_parser import get_ixbrl_parser
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the backend directory with virtual environment activated")
    sys.exit(1)


class ValidationResult:
    """Container for validation test results."""
    
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.details: List[str] = []
    
    def fail(self, message: str, details: List[str] = None):
        """Mark test as failed."""
        self.passed = False
        self.message = message
        self.details = details or []
    
    def success(self, message: str = "OK", details: List[str] = None):
        """Mark test as passed."""
        self.passed = True
        self.message = message
        self.details = details or []


def validate_environment_config() -> ValidationResult:
    """Validate environment configuration files."""
    result = ValidationResult("Environment Configuration")
    
    backend_env = backend_dir / ".env"
    frontend_env = backend_dir.parent / "frontend" / ".env"
    
    if not backend_env.exists():
        result.fail(".env file not found", [
            f"Expected: {backend_env}",
            "Create backend/.env file with required configuration (see quickstart.md)"
        ])
        return result
    
    # Check for required backend environment variables
    required_vars = [
        "DATABASE_URL",
        "MODEL_NAME",
        "MODEL_API_URL",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    with open(backend_env) as f:
        env_content = f.read()
        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
    
    if missing_vars:
        result.fail(f"Missing required environment variables: {', '.join(missing_vars)}")
        return result
    
    details = [f"✓ Backend .env found: {backend_env}"]
    if frontend_env.exists():
        details.append(f"✓ Frontend .env found: {frontend_env}")
    else:
        details.append(f"⚠ Frontend .env not found (optional): {frontend_env}")
    
    result.success("Environment files configured", details)
    return result


def validate_database_connection() -> ValidationResult:
    """Validate database connectivity and schema."""
    result = ValidationResult("Database Connection")
    
    try:
        settings = get_settings()
        db_url = settings.database_url
        
        if not db_url:
            result.fail("DATABASE_URL not configured")
            return result
        
        # Test database connection
        with get_db_session() as session:
            # Test query
            result_query = session.execute("SELECT version()")
            version = result_query.fetchone()[0]
            
            # Check for pgvector extension (if available)
            try:
                vector_check = session.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                has_vector = vector_check.fetchone()[0]
            except Exception:
                has_vector = False
            
            details = [
                f"✓ Connected to: {db_url.split('@')[-1] if '@' in db_url else 'database'}",
                f"✓ PostgreSQL version: {version.split(',')[0]}"
            ]
            
            if has_vector:
                details.append("✓ pgvector extension available")
            else:
                details.append("⚠ pgvector extension not available (optional)")
            
            result.success("Database connection successful", details)
            
    except Exception as e:
        result.fail(f"Database connection failed: {str(e)}", [
            "Check DATABASE_URL in .env file",
            "Verify PostgreSQL is running",
            "Check database credentials"
        ])
    
    return result


def validate_lm_studio() -> ValidationResult:
    """Validate LM Studio connection and model availability."""
    result = ValidationResult("LM Studio Integration")
    
    try:
        settings = get_settings()
        model_url = settings.model_api_url
        
        if not model_url:
            result.fail("MODEL_API_URL not configured")
            return result
        
        # Test connection
        try:
            response = requests.get(f"{model_url}/v1/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                model_list = models.get('data', [])
                
                details = [
                    f"✓ LM Studio server reachable: {model_url}",
                    f"✓ Available models: {len(model_list)}"
                ]
                
                # Check if expected model is loaded
                expected_model = settings.model_name
                loaded_models = [m.get('id', '') for m in model_list]
                
                if any(expected_model in m for m in loaded_models):
                    details.append(f"✓ Expected model available: {expected_model}")
                    result.success("LM Studio connection successful", details)
                else:
                    details.append(f"⚠ Expected model not found: {expected_model}")
                    details.append(f"  Available: {', '.join(loaded_models[:3])}")
                    result.fail("Expected model not loaded", details)
            else:
                result.fail(f"LM Studio API returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            result.fail("Cannot connect to LM Studio server", [
                f"URL: {model_url}",
                "Make sure LM Studio is running",
                "Verify Local Server is started in LM Studio",
                "Check MODEL_API_URL in .env"
            ])
        except requests.exceptions.Timeout:
            result.fail("LM Studio connection timeout", [
                "Server may be slow to respond",
                "Check MODEL_API_URL configuration"
            ])
            
    except Exception as e:
        result.fail(f"LM Studio validation error: {str(e)}")
    
    return result


def validate_arelle() -> ValidationResult:
    """Validate Arelle iXBRL parser availability."""
    result = ValidationResult("Arelle iXBRL Parser")
    
    try:
        parser = get_ixbrl_parser()
        
        if parser.is_available():
            health = parser.health_check()
            details = [
                "✓ Arelle library available",
                f"✓ Parser initialized: {health.get('status', 'unknown')}"
            ]
            result.success("Arelle parser available", details)
        else:
            result.fail("Arelle parser not available", [
                "Install with: pip install arelle",
                "Arelle is optional for iXBRL file parsing"
            ])
            
    except ImportError:
        result.fail("Arelle library not installed", [
            "Install with: pip install arelle",
            "Note: Arelle is optional for iXBRL parsing"
        ])
    except Exception as e:
        result.fail(f"Arelle validation error: {str(e)}")
    
    return result


def validate_api_endpoints() -> ValidationResult:
    """Validate API endpoints are accessible."""
    result = ValidationResult("API Endpoints")
    
    try:
        settings = get_settings()
        api_url = f"http://localhost:8000"
        
        # Test health endpoint
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                details = [
                    f"✓ Health endpoint: {api_url}/health",
                    f"✓ Status: {health_data.get('status', 'unknown')}"
                ]
                
                if health_data.get('model_ready'):
                    details.append("✓ Model ready for inference")
                else:
                    details.append("⚠ Model not ready")
                
                result.success("API endpoints accessible", details)
            else:
                result.fail(f"Health endpoint returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            result.fail("Cannot connect to API server", [
                f"URL: {api_url}",
                "Make sure backend server is running:",
                "  cd backend && uvicorn src.main:app --reload"
            ])
        except requests.exceptions.Timeout:
            result.fail("API connection timeout")
            
    except Exception as e:
        result.fail(f"API validation error: {str(e)}")
    
    return result


def validate_dependencies() -> ValidationResult:
    """Validate Python dependencies are installed."""
    result = ValidationResult("Python Dependencies")
    
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "alembic",
        "pydantic",
        "requests"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        result.fail(f"Missing packages: {', '.join(missing)}", [
            "Install with: pip install -r requirements.txt"
        ])
    else:
        details = [f"✓ All required packages installed ({len(required_packages)} packages)"]
        result.success("Dependencies installed", details)
    
    return result


def validate_project_structure() -> ValidationResult:
    """Validate project directory structure."""
    result = ValidationResult("Project Structure")
    
    required_dirs = [
        backend_dir / "src",
        backend_dir / "alembic",
        backend_dir / "tests",
        backend_dir.parent / "frontend",
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing.append(str(dir_path.relative_to(backend_dir.parent)))
    
    if missing:
        result.fail(f"Missing directories: {', '.join(missing)}")
    else:
        details = [f"✓ All required directories present ({len(required_dirs)} directories)"]
        result.success("Project structure valid", details)
    
    return result


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("FNA Platform Quickstart Validation")
    print("=" * 60)
    print(f"Validation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        validate_project_structure,
        validate_dependencies,
        validate_environment_config,
        validate_database_connection,
        validate_lm_studio,
        validate_arelle,
        validate_api_endpoints,
    ]
    
    results: List[ValidationResult] = []
    
    for test_func in tests:
        print(f"Testing: {test_func.__name__.replace('validate_', '').replace('_', ' ').title()}")
        result = test_func()
        results.append(result)
        
        if result.passed:
            print(f"  ✓ {result.message}")
            for detail in result.details:
                print(f"    {detail}")
        else:
            print(f"  ❌ {result.message}")
            for detail in result.details:
                print(f"    {detail}")
        print()
    
    # Summary
    print("=" * 60)
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"Validation Summary: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("\nQuickstart setup is complete and ready to use.")
        print("\nNext steps:")
        print("  1. Start backend: cd backend && uvicorn src.main:app --reload")
        print("  2. Start frontend: cd frontend && npm run dev")
        print("  3. Visit http://localhost:5173 to access the platform")
        return 0
    else:
        print("\n⚠️ Some validation tests failed.")
        print("\nPlease review the errors above and:")
        print("  1. Follow the quickstart guide: specs/001-fna-platform/quickstart.md")
        print("  2. Fix configuration issues")
        print("  3. Re-run this validation: python scripts/validate_quickstart.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())

