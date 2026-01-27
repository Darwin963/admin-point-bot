"""
نشر الموقع برابط عام مؤقت - بدون تسجيل
استخدم localtunnel او serveo
"""
import subprocess
import sys
import threading
import time

def start_hosting():
    """تشغيل موقع الاستضافة"""
    subprocess.run([sys.executable, "hosting-manager.py"], 
                  cwd=r"C:\Users\DELL\OneDrive\Desktop\Admin Point Bot\web")

def create_tunnel_ssh():
    """إنشاء نفق SSH عبر serveo (مجاني بدون تسجيل)"""
    print("\n" + "=" * 70)
    print("جاري إنشاء رابط عام عبر SSH Tunnel...")
    print("=" * 70 + "\n")
    
    try:
        # serveo.net - مجاني تماماً بدون تسجيل
        cmd = 'ssh -o StrictHostKeyChecking=no -R 80:localhost:8080 serveo.net'
        subprocess.run(cmd, shell=True)
    except KeyboardInterrupt:
        print("\n\nتم إيقاف الخدمة")

if __name__ == "__main__":
    print("=" * 70)
    print("  مولد الروابط العامة - استضافة البوتات")
    print("=" * 70)
    print("\nسيتم:")
    print("1. تشغيل موقع الاستضافة على localhost:8080")
    print("2. إنشاء رابط عام يمكن لأي شخص الوصول إليه")
    print("\nانتظر لحظة...")
    print("=" * 70 + "\n")
    
    # تشغيل الموقع في خلفية
    hosting_thread = threading.Thread(target=start_hosting, daemon=True)
    hosting_thread.start()
    
    # انتظار بدء الخادم
    time.sleep(3)
    
    # إنشاء النفق
    try:
        create_tunnel_ssh()
    except KeyboardInterrupt:
        print("\n\nشكراً لاستخدامك الخدمة!")
