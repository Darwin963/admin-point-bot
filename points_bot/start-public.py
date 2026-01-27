"""
نشر الموقع برابط عام عبر ngrok
"""
import sys
import os

# إصلاح مشكلة الترميز في Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from pyngrok import ngrok
import subprocess

# فتح نفق ngrok
print("جاري إنشاء رابط عام...")
public_url = ngrok.connect(8080)
print("\n" + "=" * 60)
print("الموقع متاح الآن عبر الرابط التالي:")
print(f"LINK: {public_url}")
print("=" * 60)
print("\nشارك هذا الرابط مع أي شخص في العالم!")
print("اضغط Ctrl+C لإيقاف الخدمة\n")

# تشغيل الموقع
try:
    subprocess.run([sys.executable, "hosting-manager.py"], cwd=os.path.dirname(__file__))
except KeyboardInterrupt:
    print("\n\nتم إيقاف الخدمة")
    ngrok.disconnect(public_url)
