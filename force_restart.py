import subprocess
import time
import requests
import sys
import os

print("=== FORCE RESTART SERVER ===")

# Kill existing server processes
try:
    print("1. Stopping existing server...")
    # Find and kill Python processes using port 5002
    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    
    for line in lines:
        if ':5002' in line and 'LISTENING' in line:
            parts = line.split()
            if len(parts) >= 5:
                pid = parts[-1]
                try:
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                    print(f"   Killed process {pid}")
                except:
                    pass
    
    time.sleep(2)
except:
    pass

# Start new server
print("2. Starting new server...")
try:
    # Use the same virtual environment and start server
    cmd = [sys.executable, 'run.py']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.getcwd())
    
    print("3. Waiting for server to start...")
    time.sleep(5)
    
    # Test if server is running
    try:
        response = requests.get('http://127.0.0.1:5002/health', timeout=3)
        print(f"   Health check: {response.status_code}")
        
        # Test genres endpoint
        response = requests.get('http://127.0.0.1:5002/api/genres', timeout=3)
        print(f"   Genres check: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Genres loaded: {len(data.get('genres', []))}")
        else:
            print(f"   ❌ Genres error: {response.text}")
            
    except Exception as e:
        print(f"   Server test failed: {e}")
    
    print("4. Server is running. Press Ctrl+C to stop.")
    print("   Check the server terminal for logs.")
    
    # Keep the process running
    for line in process.stdout:
        print(line.rstrip())
        
except KeyboardInterrupt:
    print("\n5. Stopping server...")
    process.terminate()
    print("   Server stopped.")
except Exception as e:
    print(f"❌ Error starting server: {e}")
