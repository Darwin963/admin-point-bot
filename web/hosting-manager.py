"""
🤖 Bot Hosting Manager
موقع استضافة بوتات Discord - إضافة عدد لا محدود من البوتات
"""

from flask import Flask, render_template_string, request, jsonify
import subprocess
import os
import sys
import json
import threading
import time
from datetime import datetime

app = Flask(__name__)

# مسار تخزين البوتات
BOTS_DIR = os.path.dirname(os.path.abspath(__file__))
BOTS_CONFIG_FILE = os.path.join(BOTS_DIR, "bots_config.json")

# تخزين معلومات البوتات النشطة
active_bots = {}
bot_processes = {}

def load_bots_config():
    """تحميل إعدادات البوتات"""
    if os.path.exists(BOTS_CONFIG_FILE):
        with open(BOTS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_bots_config(config):
    """حفظ إعدادات البوتات"""
    with open(BOTS_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def start_bot(bot_name, file_path, token=None):
    """تشغيل بوت"""
    try:
        if bot_name in bot_processes and bot_processes[bot_name].poll() is None:
            return {"success": False, "message": "البوت يعمل بالفعل"}
        
        env = os.environ.copy()
        if token:
            env[f"{bot_name.upper()}_TOKEN"] = token
        
        process = subprocess.Popen(
            [sys.executable, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=BOTS_DIR
        )
        
        bot_processes[bot_name] = process
        active_bots[bot_name] = {
            "status": "running",
            "file": file_path,
            "started": datetime.now().isoformat(),
            "pid": process.pid
        }
        
        return {"success": True, "message": f"تم تشغيل {bot_name}", "pid": process.pid}
    
    except Exception as e:
        return {"success": False, "message": str(e)}

def stop_bot(bot_name):
    """إيقاف بوت"""
    try:
        if bot_name in bot_processes:
            process = bot_processes[bot_name]
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
            
            del bot_processes[bot_name]
            if bot_name in active_bots:
                active_bots[bot_name]["status"] = "stopped"
            
            return {"success": True, "message": f"تم إيقاف {bot_name}"}
        
        return {"success": False, "message": "البوت غير نشط"}
    
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_bot_status(bot_name):
    """الحصول على حالة البوت"""
    if bot_name in bot_processes:
        process = bot_processes[bot_name]
        if process.poll() is None:
            return "running"
        else:
            return "crashed"
    return "stopped"

# صفحة الويب الرئيسية
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 استضافة البوتات</title>
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
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .stat-card p {
            color: #666;
        }
        
        .add-bot-section {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .add-bot-section h2 {
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
        
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group textarea {
            min-height: 200px;
            font-family: 'Courier New', monospace;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .bots-list {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .bots-list h2 {
            color: #667eea;
            margin-bottom: 20px;
        }
        
        .bot-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .bot-info h3 {
            color: #333;
            margin-bottom: 5px;
        }
        
        .bot-info p {
            color: #666;
            font-size: 0.9em;
        }
        
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-top: 5px;
        }
        
        .status.running {
            background: #28a745;
            color: white;
        }
        
        .status.stopped {
            background: #dc3545;
            color: white;
        }
        
        .status.crashed {
            background: #ffc107;
            color: black;
        }
        
        .bot-controls {
            display: flex;
            gap: 10px;
        }
        
        .btn-small {
            padding: 8px 20px;
            font-size: 0.9em;
        }
        
        .btn-success {
            background: #28a745;
        }
        
        .btn-danger {
            background: #dc3545;
        }
        
        .btn-info {
            background: #17a2b8;
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
            border: 1px solid #c3e6cb;
        }
        
        .alert.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 استضافة البوتات Discord</h1>
            <p>أضف وأدر عدد لا محدود من البوتات - مجاناً للأبد</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3 id="totalBots">0</h3>
                <p>إجمالي البوتات</p>
            </div>
            <div class="stat-card">
                <h3 id="runningBots">0</h3>
                <p>بوتات نشطة</p>
            </div>
            <div class="stat-card">
                <h3 id="stoppedBots">0</h3>
                <p>بوتات متوقفة</p>
            </div>
        </div>
        
        <div class="add-bot-section">
            <h2>➕ إضافة بوت جديد</h2>
            <div id="alert" class="alert"></div>
            
            <form id="addBotForm">
                <div class="form-group">
                    <label>اسم البوت:</label>
                    <input type="text" id="botName" placeholder="مثال: my-awesome-bot" required>
                </div>
                
                <div class="form-group">
                    <label>توكن البوت (اختياري):</label>
                    <input type="text" id="botToken" placeholder="MTExNjY2ODY2NDI2NDAxMTc3Ng...">
                </div>
                
                <div class="form-group">
                    <label>كود البوت (Python):</label>
                    <textarea id="botCode" placeholder="import discord&#10;from discord.ext import commands&#10;&#10;bot = commands.Bot(command_prefix='!')&#10;&#10;@bot.event&#10;async def on_ready():&#10;    print(f'{bot.user} is ready!')&#10;&#10;bot.run('TOKEN')" required></textarea>
                </div>
                
                <button type="submit" class="btn">إضافة البوت</button>
            </form>
        </div>
        
        <div class="bots-list">
            <h2>📋 البوتات المستضافة</h2>
            <div id="botsList"></div>
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
        
        async function loadBots() {
            try {
                const response = await fetch('/api/bots');
                const bots = await response.json();
                
                const botsList = document.getElementById('botsList');
                botsList.innerHTML = '';
                
                let total = 0, running = 0, stopped = 0;
                
                for (const [name, info] of Object.entries(bots)) {
                    total++;
                    if (info.status === 'running') running++;
                    else stopped++;
                    
                    const card = document.createElement('div');
                    card.className = 'bot-card';
                    card.innerHTML = `
                        <div class="bot-info">
                            <h3>🤖 ${name}</h3>
                            <p>📄 ${info.file || 'N/A'}</p>
                            <span class="status ${info.status}">${info.status}</span>
                        </div>
                        <div class="bot-controls">
                            <button class="btn btn-small btn-success" onclick="startBot('${name}')">▶️ تشغيل</button>
                            <button class="btn btn-small btn-danger" onclick="stopBot('${name}')">⏹️ إيقاف</button>
                            <button class="btn btn-small btn-info" onclick="restartBot('${name}')">🔄 إعادة</button>
                        </div>
                    `;
                    botsList.appendChild(card);
                }
                
                document.getElementById('totalBots').textContent = total;
                document.getElementById('runningBots').textContent = running;
                document.getElementById('stoppedBots').textContent = stopped;
                
                if (total === 0) {
                    botsList.innerHTML = '<p style="text-align:center;color:#666;">لا توجد بوتات. أضف بوتك الأول!</p>';
                }
            } catch (error) {
                console.error('Error loading bots:', error);
            }
        }
        
        document.getElementById('addBotForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const name = document.getElementById('botName').value;
            const token = document.getElementById('botToken').value;
            const code = document.getElementById('botCode').value;
            
            try {
                const response = await fetch('/api/bots/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, token, code})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    document.getElementById('addBotForm').reset();
                    loadBots();
                } else {
                    showAlert(result.message, 'error');
                }
            } catch (error) {
                showAlert('حدث خطأ: ' + error.message, 'error');
            }
        });
        
        async function startBot(name) {
            try {
                const response = await fetch(`/api/bots/${name}/start`, {method: 'POST'});
                const result = await response.json();
                showAlert(result.message, result.success ? 'success' : 'error');
                loadBots();
            } catch (error) {
                showAlert('حدث خطأ: ' + error.message, 'error');
            }
        }
        
        async function stopBot(name) {
            try {
                const response = await fetch(`/api/bots/${name}/stop`, {method: 'POST'});
                const result = await response.json();
                showAlert(result.message, result.success ? 'success' : 'error');
                loadBots();
            } catch (error) {
                showAlert('حدث خطأ: ' + error.message, 'error');
            }
        }
        
        async function restartBot(name) {
            await stopBot(name);
            setTimeout(() => startBot(name), 2000);
        }
        
        // تحديث كل 5 ثواني
        setInterval(loadBots, 5000);
        loadBots();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/bots')
def get_bots():
    """الحصول على قائمة البوتات"""
    config = load_bots_config()
    
    # تحديث حالة البوتات
    for bot_name in config:
        config[bot_name]['status'] = get_bot_status(bot_name)
    
    return jsonify(config)

@app.route('/api/bots/add', methods=['POST'])
def add_bot():
    """إضافة بوت جديد"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        token = data.get('token', '').strip()
        code = data.get('code', '').strip()
        
        if not name or not code:
            return jsonify({"success": False, "message": "الاسم والكود مطلوبان"})
        
        # تنظيف اسم الملف
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).lower()
        file_path = os.path.join(BOTS_DIR, f"{safe_name}.py")
        
        # حفظ الكود
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # حفظ الإعدادات
        config = load_bots_config()
        config[safe_name] = {
            "file": file_path,
            "token": token if token else None,
            "status": "stopped",
            "created": datetime.now().isoformat()
        }
        save_bots_config(config)
        
        return jsonify({"success": True, "message": f"تم إضافة البوت {safe_name} بنجاح"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/bots/<bot_name>/start', methods=['POST'])
def api_start_bot(bot_name):
    """تشغيل بوت"""
    config = load_bots_config()
    
    if bot_name not in config:
        return jsonify({"success": False, "message": "البوت غير موجود"})
    
    result = start_bot(bot_name, config[bot_name]['file'], config[bot_name].get('token'))
    return jsonify(result)

@app.route('/api/bots/<bot_name>/stop', methods=['POST'])
def api_stop_bot(bot_name):
    """إيقاف بوت"""
    result = stop_bot(bot_name)
    return jsonify(result)

@app.route('/api/bots/<bot_name>', methods=['DELETE'])
def delete_bot(bot_name):
    """حذف بوت"""
    try:
        # إيقاف البوت أولاً
        stop_bot(bot_name)
        
        # حذف الملف
        config = load_bots_config()
        if bot_name in config:
            file_path = config[bot_name]['file']
            if os.path.exists(file_path):
                os.remove(file_path)
            
            del config[bot_name]
            save_bots_config(config)
        
        return jsonify({"success": True, "message": f"تم حذف {bot_name}"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

def auto_start_bots():
    """تشغيل البوتات تلقائياً عند البدء"""
    config = load_bots_config()
    for bot_name, info in config.items():
        if info.get('auto_start', False):
            start_bot(bot_name, info['file'], info.get('token'))

if __name__ == '__main__':
    print("🤖 Bot Hosting Manager")
    print("=" * 50)
    print("📡 Server: http://0.0.0.0:8080")
    print("🌐 Access: http://localhost:8080")
    print("=" * 50)
    
    # تشغيل البوتات التلقائية
    threading.Thread(target=auto_start_bots, daemon=True).start()
    
    app.run(host='0.0.0.0', port=8080, debug=False)
