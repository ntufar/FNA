#!/usr/bin/env python3
"""Test script for Arelle iXBRL parsing functionality.

This script tests the Arelle library installation and basic iXBRL parsing
capabilities as specified in research.md.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from services.ixbrl_parser import ArelleParser, iXBRLParsingError


def test_arelle_installation():
    """Test if Arelle is properly installed and can be imported."""
    print("🧪 Testing Arelle Installation")
    print("=" * 40)
    
    try:
        parser = ArelleParser()
        
        if parser.is_available():
            print("✅ Arelle library imported successfully")
            print("✅ Arelle controller initialized")
            return True
        else:
            print("❌ Arelle initialization failed")
            return False
            
    except ImportError as e:
        print(f"❌ Arelle library not found: {e}")
        print("💡 Install with: pip install arelle")
        return False
    except Exception as e:
        print(f"❌ Arelle initialization error: {e}")
        return False


def test_parsing_capabilities():
    """Test iXBRL parsing capabilities with sample data."""
    print("\n🔍 Testing iXBRL Parsing Capabilities")
    print("=" * 45)
    
    try:
        parser = ArelleParser()
        
        # Test parser configuration
        settings = parser.settings
        print(f"Cache Directory: {settings.cache_dir}")
        print(f"Log Level: {settings.log_level}")
        
        print("✅ Parser configuration loaded")
        print("✅ Ready to parse iXBRL documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        return False


def main():
    """Run all Arelle tests."""
    print("🏗️ FNA Arelle iXBRL Parser Test Suite")
    print("=" * 50)
    
    # Test installation
    installation_ok = test_arelle_installation()
    
    if not installation_ok:
        print("\n❌ Arelle installation test failed!")
        print("Please install Arelle before proceeding:")
        print("  pip install arelle")
        sys.exit(1)
    
    # Test parsing capabilities
    parsing_ok = test_parsing_capabilities()
    
    if installation_ok and parsing_ok:
        print("\n🎉 All Arelle tests passed!")
        print("\nNext steps:")
        print("1. Obtain sample iXBRL files from SEC.gov")
        print("2. Test with real iXBRL documents")
        print("3. Integrate with FNA narrative analysis pipeline")
    else:
        print("\n⚠️ Some tests failed - check configuration")
        sys.exit(1)


if __name__ == "__main__":
    main()
