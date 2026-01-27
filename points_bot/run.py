import sys
sys.stdout.reconfigure(encoding='utf-8')

import subprocess
import threading
import time

def start_server():
    subprocess.run([sys.executable, "hosting-manager.py"], 
                  cwd=r"C:\Users\DELL\OneDrive\Desktop\Admin Point Bot\web")

print("=" * 60)
print("HOSTING MANAGER - PUBLIC ACCESS")
print("=" * 60)
print("\nStarting server on localhost:8080...")
print("Server will be accessible at:")
print("  - http://localhost:8080")
print("  - http://192.168.70.23:8080")
print("\nFor PUBLIC access:")
print("  1. Visit: https://dashboard.ngrok.com/signup")
print("  2. Sign up (FREE)")
print("  3. Get your authtoken")
print("  4. Run: ngrok config add-authtoken YOUR_TOKEN")
print("  5. Run: ngrok http 8080")
print("\nOR use Railway for permanent hosting:")
print("  https://railway.app")
print("=" * 60)
print("\nStarting...\n")

threading.Thread(target=start_server, daemon=True).start()
time.sleep(2)

print("\nServer is RUNNING!")
print("Open browser: http://localhost:8080")
print("\nPress Ctrl+C to stop")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nServer stopped!")
