import os
import sys

def main():
    """Main function dengan error handling"""
    try:
        # Coba import app yang lengkap
        from app import create_app
        print("Starting FilmKu API (Full Version)...")
    except ImportError as e:
        print(f"Cannot import full app: {e}")
        print("Falling back to simple version...")
        
        # Fallback ke simple version
        try:
            from run_simple import create_simple_app as create_app
            print("Using simple version")
        except ImportError as e2:
            print(f"Cannot import simple app: {e2}")
            print("Please install required dependencies:")
            print("   pip install flask flask-cors pandas scikit-learn")
            return
    
    try:
        app = create_app()
        
        # Pastikan direktori untuk file log ada
        os.makedirs('logs', exist_ok=True)
        
        # Ambil port dari argumen command line atau gunakan 5002 sebagai default
        port = 5002  # Default port
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            port = int(sys.argv[1])
        
        # Jalankan aplikasi
        print(f"🌐 Server starting on http://localhost:{port}")
        print("📚 API Documentation: http://localhost:{}/api/welcome".format(port))
        print("🏥 Health Check: http://localhost:{}/health".format(port))
        print("⏹️  Press CTRL+C to stop")
        print("-" * 50)
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Try installing dependencies: pip install -r requirements.txt")
        print("🔄 Or use: python run_simple.py")

if __name__ == '__main__':
    main()