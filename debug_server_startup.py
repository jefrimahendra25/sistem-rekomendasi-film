import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=== DEBUGGING SERVER STARTUP ===")

try:
    print("1. Testing run.py import...")
    import run
    print("   ✅ run.py imported successfully")
    
    print("2. Testing create_app from run...")
    app = run.create_app()
    print("   ✅ App created successfully")
    
    print("3. Testing app routes...")
    with app.app_context():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.rule} -> {rule.endpoint}")
        
        print(f"   ✅ Found {len(routes)} routes")
        print("   Sample routes:")
        for route in routes[:5]:
            print(f"     {route}")
    
    print("=== SERVER STARTUP SUCCESSFUL ===")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
