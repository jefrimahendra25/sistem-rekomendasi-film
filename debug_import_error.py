import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=== DEBUGGING IMPORT ERROR ===")

try:
    print("1. Testing app import...")
    from app import create_app
    print("   ✅ app.create_app imported successfully")
    
except ImportError as e:
    print(f"❌ Cannot import full app: {e}")
    print("🔄 Trying to debug the import issue...")
    
    try:
        print("2. Testing app.movie_service import...")
        from app.movie_service import movie_service
        print("   ✅ movie_service imported")
        
        print("3. Testing app.routes import...")
        from app.routes import main
        print("   ✅ routes imported")
        
        print("4. Testing app.utils import...")
        from app.utils import handle_api_errors
        print("   ✅ utils imported")
        
        print("5. Testing app.__init__ import...")
        import app
        print(f"   ✅ app module imported: {app}")
        print(f"   Available attributes: {[attr for attr in dir(app) if not attr.startswith('_')]}")
        
    except ImportError as e2:
        print(f"❌ Import error details: {e2}")
        import traceback
        traceback.print_exc()

print("=== DEBUG COMPLETE ===")
