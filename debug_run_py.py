import sys
import os

# Simulate run.py environment
print("=== DEBUGGING RUN.PY LOGIC ===")

def main():
    """Main function dengan error handling"""
    try:
        # Coba import app yang lengkap
        from app import create_app
        print("🚀 Starting FilmKu API (Full Version)...")
        return create_app, "full"
    except ImportError as e:
        print(f"⚠️  Cannot import full app: {e}")
        print("🔄 Falling back to simple version...")
        
        # Fallback ke simple version
        try:
            from run_simple import create_simple_app as create_app
            print("✅ Using simple version")
            return create_app, "simple"
        except ImportError as e2:
            print(f"❌ Cannot import simple app: {e2}")
            print("💡 Please install required dependencies:")
            print("   pip install flask flask-cors pandas scikit-learn")
            return None, None

# Test the logic
create_app_func, version = main()

if create_app_func:
    print(f"✅ Using {version} version")
    try:
        app = create_app_func()
        print(f"✅ App created successfully with {len(list(app.url_map.iter_rules()))} routes")
    except Exception as e:
        print(f"❌ Error creating app: {e}")
else:
    print("❌ No app available")
