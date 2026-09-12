#!/usr/bin/env python3
"""
Direct runner for full app - no fallback to simple version
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def main():
    """Force run full app"""
    print("=== STARTING FULL APP (NO FALLBACK) ===")
    
    try:
        # Force import full app
        from app import create_app
        print("✅ Full app imported successfully")
        
        # Create app
        app = create_app()
        print("✅ App created successfully")
        
        # Setup logging
        os.makedirs('logs', exist_ok=True)
        
        # Get port
        port = int(os.environ.get('PORT', 5002))
        
        print(f"🌐 Starting full app server on http://localhost:{port}")
        print(f"📚 API Documentation: http://localhost:{port}/api/welcome")
        print(f"🏥 Health Check: http://localhost:{port}/health")
        print("⏹️  Press CTRL+C to stop")
        print("-" * 50)
        
        # Run app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=True
        )
        
    except ImportError as e:
        print(f"❌ Cannot import full app: {e}")
        print("💡 Please install required dependencies:")
        print("   pip install flask flask-cors flask-caching pandas scikit-learn")
        return 1
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
