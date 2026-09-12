#!/usr/bin/env python3
"""
Direct Flask app runner without debug mode
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=== DIRECT FLASK RUNNER ===")
    
    try:
        # Import app
        from app import create_app
        print("✅ App imported")
        
        # Create app
        app = create_app()
        print("✅ App created")
        
        # Test app context
        with app.app_context():
            print("✅ App context works")
        
        # Run without debug mode
        print("🌐 Starting server on http://127.0.0.1:5002")
        app.run(host='127.0.0.1', port=5002, debug=False)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
