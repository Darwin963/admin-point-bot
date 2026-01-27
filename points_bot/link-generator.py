"""
موقع إدارة الروابط العامة - يعطيك روابط ngrok تلقائياً
"""
from flask import Flask, render_template_string, request, jsonify
import subprocess
import threading
import time
import json
import os

app = Flask(__name__)

# حالة الروابط النشطة
active_tunnels = {}
tunnel_processes = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌐 مولد الروابط العامة</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 15px;
        }
        
        .header p {
            color: #666;
            font-size: 1.2em;
        }
        
        .section {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: bold;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            transition: transform 0.2s;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .link-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 15px;
        }
        
        .link-card h3 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .link-url {
            background: #667eea;
            color: white;
            padding: 15px;
            border-radius: 10px;
            font-size: 1.1em;
            word-break: break-all;
            margin: 10px 0;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .link-url:hover {
            background: #764ba2;
        }
        
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .status.active {
            background: #28a745;
            color: white;
        }
        
        .status.inactive {
            background: #dc3545;
            color: white;
        }
        
        .alert {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        
        .alert.success {
            background: #d4edda;
            color: #155724;
        }
        
        .alert.error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .alert.info {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .setup-steps {
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .setup-steps h3 {
            color: #856404;
            margin-bottom: 15px;
        }
        
        .setup-steps ol {
            margin-right: 20px;
        }
        
        .setup-steps li {
            margin-bottom: 10px;
            color: #856404;
        }
        
        .copy-btn {
            background: #28a745;
            color: white;
            padding: 8px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 مولد الروابط العامة</h1>
            <p>احصل على رابط عام مجاني لموقعك أو بوتك - يعمل من أي مكان في العالم</p>
        </div>
        
        <div id="alert" class="alert"></div>
        
        <div class="setup-steps" id="setupSteps">
            <h3>⚙️ إعداد سريع (مرة واحدة فقط):</h3>
            <ol>
                <li>سجل في ngrok: <a href="https://dashboard.ngrok.com/signup" target="_blank">https://dashboard.ngrok.com/signup</a> (مجاني)</li>
                <li>احصل على التوكن: <a href="https://dashboard.ngrok.com/get-started/your-authtoken" target="_blank">Get Token</a></li>
                <li>انسخ التوكن والصقه أدناه</li>
            </ol>
        </div>
        
        <div class="section">
            <h2>🔑 ضبط التوكن</h2>
            <form id="tokenForm">
                <div class="form-group">
                    <label>Ngrok Authtoken:</label>
                    <input type="text" id="authtoken" placeholder="2abc...xyz" required>
                </div>
                <button type="submit" class="btn">💾 حفظ التوكن</button>
            </form>
        </div>
        
        <div class="section">
            <h2>➕ إنشاء رابط جديد</h2>
            <form id="createLinkForm">
                <div class="form-group">
                    <label>المنفذ (Port):</label>
                    <input type="number" id="port" value="8080" required>
                </div>
                <div class="form-group">
                    <label>اسم الرابط (اختياري):</label>
                    <input type="text" id="linkName" placeholder="my-website">
                </div>
                <button type="submit" class="btn">🚀 إنشاء رابط عام</button>
            </form>
        </div>
        
        <div class="section">
            <h2>📋 الروابط النشطة</h2>
            <div id="linksList"></div>
        </div>
    </div>
    
    <script>
        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert ${type}`;
            alert.style.display = 'block';
            setTimeout(() => alert.style.display = 'none', 5000);
        }
        
        document.getElementById('tokenForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const token = document.getElementById('authtoken').value;
            
            try {
                const response = await fetch('/api/set-token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token})
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert('تم حفظ التوكن بنجاح! يمكنك الآن إنشاء روابط', 'success');
                    document.getElementById('setupSteps').style.display = 'none';
                } else {
                    showAlert(result.message, 'error');
                }
            } catch (error) {
                showAlert('خطأ: ' + error.message, 'error');
            }
        });
        
        document.getElementById('createLinkForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const port = document.getElementById('port').value;
            const name = document.getElementById('linkName').value;
            
            try {
                const response = await fetch('/api/create-tunnel', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({port, name})
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert('تم إنشاء الرابط بنجاح!', 'success');
                    loadLinks();
                } else {
                    showAlert(result.message, 'error');
                }
            } catch (error) {
                showAlert('خطأ: ' + error.message, 'error');
            }
        });
        
        async function loadLinks() {
            try {
                const response = await fetch('/api/tunnels');
                const tunnels = await response.json();
                
                const linksList = document.getElementById('linksList');
                linksList.innerHTML = '';
                
                if (Object.keys(tunnels).length === 0) {
                    linksList.innerHTML = '<p style="text-align:center;color:#666;">لا توجد روابط نشطة</p>';
                    return;
                }
                
                for (const [name, info] of Object.entries(tunnels)) {
                    const card = document.createElement('div');
                    card.className = 'link-card';
                    card.innerHTML = `
                        <h3>🔗 ${name}</h3>
                        <div class="link-url" onclick="copyToClipboard('${info.url}')" title="اضغط للنسخ">
                            ${info.url}
                        </div>
                        <p>المنفذ المحلي: localhost:${info.port}</p>
                        <span class="status active">نشط</span>
                        <button class="copy-btn" onclick="copyToClipboard('${info.url}')">📋 نسخ</button>
                    `;
                    linksList.appendChild(card);
                }
            } catch (error) {
                console.error('Error loading links:', error);
            }
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text);
            showAlert('تم نسخ الرابط!', 'success');
        }
        
        setInterval(loadLinks, 5000);
        loadLinks();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/set-token', methods=['POST'])
def set_token():
    """حفظ توكن ngrok"""
    try:
        data = request.json
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({"success": False, "message": "التوكن مطلوب"})
        
        # حفظ التوكن
        result = subprocess.run(
            ['ngrok', 'config', 'add-authtoken', token],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return jsonify({"success": True, "message": "تم حفظ التوكن"})
        else:
            return jsonify({"success": False, "message": result.stderr})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/create-tunnel', methods=['POST'])
def create_tunnel():
    """إنشاء نفق ngrok"""
    try:
        data = request.json
        port = int(data.get('port', 8080))
        name = data.get('name', f'tunnel-{port}')
        
        if name in tunnel_processes:
            return jsonify({"success": False, "message": "الرابط موجود بالفعل"})
        
        # تشغيل ngrok
        process = subprocess.Popen(
            ['ngrok', 'http', str(port), '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        tunnel_processes[name] = process
        
        # انتظار الحصول على الرابط
        time.sleep(3)
        
        # الحصول على الرابط من API
        import requests
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            tunnels_data = response.json()
            
            if tunnels_data.get('tunnels'):
                public_url = tunnels_data['tunnels'][0]['public_url']
                
                active_tunnels[name] = {
                    'url': public_url,
                    'port': port,
                    'created': time.time()
                }
                
                return jsonify({
                    "success": True,
                    "url": public_url,
                    "message": f"تم إنشاء الرابط: {public_url}"
                })
        except:
            pass
        
        return jsonify({
            "success": True,
            "message": "تم بدء النفق - جاري الحصول على الرابط..."
        })
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/tunnels')
def get_tunnels():
    """الحصول على الروابط النشطة"""
    return jsonify(active_tunnels)

if __name__ == '__main__':
    print("=" * 60)
    print("  Link Generator - Ngrok Manager")
    print("=" * 60)
    print("  Website: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
