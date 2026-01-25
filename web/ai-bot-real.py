import discord
from discord.ext import commands
import asyncio
import traceback
import sys
import subprocess
import os
import sqlite3
import psycopg2
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!ai ",
    intents=intents,
    help_command=None
)

AI_ADMIN_IDS = {739749692308586526, 1020294577153908766}

MAIN_BOT_PATH = os.path.join(os.path.dirname(__file__), "..", "bot.py")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "system.db")

@bot.event
async def on_ready():
    print(f'🤖 AI Bot Online — {bot.user}')
    await bot.change_presence(activity=discord.Game(name="AI Fixer | !ai help"))

def is_ai_admin(ctx):
    return ctx.author.id in AI_ADMIN_IDS or ctx.author.guild_permissions.administrator

@bot.command()
async def help(ctx):
    """قائمة أوامر البوت الذكي"""
    embed = discord.Embed(title="🤖 AI Bot - الإصلاح الحقيقي", color=0x00FF00)
    embed.description = "بوت ذكاء اصطناعي يصلح المشاكل **فعلياً**"
    
    embed.add_field(name="🔧 إصلاح حقيقي", value=(
        "!ai checkbot - فحص البوت الأساسي\n"
        "!ai fixdb - إصلاح قاعدة البيانات\n"
        "!ai restart - إعادة تشغيل البوت\n"
        "!ai logs - عرض آخر الأخطاء"
    ), inline=False)
    
    embed.add_field(name="📊 المراقبة", value=(
        "!ai status - حالة النظام\n"
        "!ai dbstatus - حالة قاعدة البيانات\n"
        "!ai backup - نسخ احتياطي"
    ), inline=False)
    
    embed.add_field(name="⚙️ للمطورين", value=(
        "!ai execute <code> - تنفيذ Python\n"
        "!ai sql <query> - تنفيذ SQL\n"
        "!ai install <package> - تثبيت مكتبة"
    ), inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def checkbot(ctx):
    """فحص البوت الأساسي"""
    if not is_ai_admin(ctx):
        return await ctx.send("❌ ليس لديك صلاحية")
    
    msg = await ctx.send("🔍 جاري فحص البوت الأساسي...")
    
    issues = []
    fixes = []
    
    # فحص الملف
    if not os.path.exists(MAIN_BOT_PATH):
        issues.append("❌ bot.py غير موجود")
    else:
        try:
            with open(MAIN_BOT_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # فحص المشاكل الشائعة
            if "TOKEN" not in content:
                issues.append("⚠️ لا يوجد TOKEN")
            else:
                fixes.append("✅ TOKEN موجود")
            
            if "import discord" not in content:
                issues.append("❌ مكتبة discord غير مستوردة")
            else:
                fixes.append("✅ discord مستوردة")
            
            if "bot.run" not in content and "client.run" not in content:
                issues.append("❌ لا يوجد bot.run()")
            else:
                fixes.append("✅ bot.run() موجود")
                
        except Exception as e:
            issues.append(f"❌ خطأ في قراءة الملف: {e}")
    
    # فحص قاعدة البيانات
    if os.path.exists(DB_PATH):
        try:
            db = sqlite3.connect(DB_PATH)
            c = db.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in c.fetchall()]
            db.close()
            
            if tables:
                fixes.append(f"✅ قاعدة البيانات: {len(tables)} جداول")
            else:
                issues.append("⚠️ قاعدة البيانات فارغة")
        except Exception as e:
            issues.append(f"❌ خطأ في قاعدة البيانات: {e}")
    else:
        issues.append("⚠️ system.db غير موجود")
    
    # فحص المكتبات
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True, timeout=10)
        installed = result.stdout.lower()
        
        if "discord" in installed:
            fixes.append("✅ discord.py مثبتة")
        else:
            issues.append("❌ discord.py غير مثبتة")
            
        if "psycopg2" in installed:
            fixes.append("✅ psycopg2 مثبتة")
    except:
        issues.append("⚠️ لم يتم فحص المكتبات")
    
    # عرض النتائج
    embed = discord.Embed(title="🔍 نتيجة الفحص", color=0x00FF00 if not issues else 0xFF9900)
    
    if fixes:
        embed.add_field(name="✅ سليم", value="\n".join(fixes), inline=False)
    
    if issues:
        embed.add_field(name="⚠️ مشاكل", value="\n".join(issues), inline=False)
        embed.add_field(name="💡 الحل", value="استخدم `!ai fix` لإصلاح المشاكل تلقائياً", inline=False)
    else:
        embed.add_field(name="🎉 النتيجة", value="كل شيء يعمل بشكل ممتاز!", inline=False)
    
    await msg.edit(content=None, embed=embed)

@bot.command()
async def fixdb(ctx):
    """إصلاح قاعدة البيانات"""
    if not is_ai_admin(ctx):
        return await ctx.send("❌ ليس لديك صلاحية")
    
    msg = await ctx.send("🔧 جاري إصلاح قاعدة البيانات...")
    
    try:
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        
        # إنشاء الجداول الأساسية
        tables_created = []
        
        c.execute("""CREATE TABLE IF NOT EXISTS points 
                    (user_id BIGINT PRIMARY KEY, points INTEGER DEFAULT 0)""")
        tables_created.append("points")
        
        c.execute("""CREATE TABLE IF NOT EXISTS config 
                    (guild_id BIGINT PRIMARY KEY, points_channel BIGINT)""")
        tables_created.append("config")
        
        c.execute("""CREATE TABLE IF NOT EXISTS salaries 
                    (user_id BIGINT PRIMARY KEY, last_salary REAL)""")
        tables_created.append("salaries")
        
        c.execute("""CREATE TABLE IF NOT EXISTS antifarm 
                    (user_id BIGINT PRIMARY KEY, last_msg TEXT, last_time REAL)""")
        tables_created.append("antifarm")
        
        c.execute("""CREATE TABLE IF NOT EXISTS cooldowns 
                    (user_id BIGINT PRIMARY KEY, last_message REAL)""")
        tables_created.append("cooldowns")
        
        db.commit()
        db.close()
        
        embed = discord.Embed(title="✅ تم إصلاح قاعدة البيانات", color=0x00FF00)
        embed.add_field(name="الجداول", value="\n".join(f"✅ {t}" for t in tables_created), inline=False)
        embed.add_field(name="الموقع", value=f"`{DB_PATH}`", inline=False)
        
        await msg.edit(content=None, embed=embed)
        
    except Exception as e:
        await msg.edit(content=f"❌ فشل الإصلاح:\n```python\n{e}\n```")

@bot.command()
async def dbstatus(ctx):
    """حالة قاعدة البيانات"""
    if not is_ai_admin(ctx):
        return await ctx.send("❌ ليس لديك صلاحية")
    
    if not os.path.exists(DB_PATH):
        return await ctx.send("❌ قاعدة البيانات غير موجودة. استخدم `!ai fixdb`")
    
    try:
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        
        embed = discord.Embed(title="📊 حالة قاعدة البيانات", color=0x0099FF)
        
        # عدد المستخدمين
        c.execute("SELECT COUNT(*) FROM points")
        users = c.fetchone()[0]
        embed.add_field(name="👥 المستخدمين", value=f"{users}", inline=True)
        
        # مجموع النقاط
        c.execute("SELECT SUM(points) FROM points")
        total = c.fetchone()[0] or 0
        embed.add_field(name="⭐ مجموع النقاط", value=f"{total:,}", inline=True)
        
        # أعلى نقاط
        c.execute("SELECT MAX(points) FROM points")
        max_points = c.fetchone()[0] or 0
        embed.add_field(name="🏆 أعلى نقاط", value=f"{max_points:,}", inline=True)
        
        # الجداول
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        embed.add_field(name="📋 الجداول", value=", ".join(tables), inline=False)
        
        # حجم الملف
        size = os.path.getsize(DB_PATH) / 1024
        embed.add_field(name="💾 الحجم", value=f"{size:.2f} KB", inline=True)
        
        db.close()
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ خطأ:\n```python\n{e}\n```")

@bot.command()
async def sql(ctx, *, query: str):
    """تنفيذ استعلام SQL"""
    if ctx.author.id not in AI_ADMIN_IDS:
        return await ctx.send("❌ هذا الأمر للمطورين فقط")
    
    query = query.strip('`').replace('sql\n', '')
    
    try:
        db = sqlite3.connect(DB_PATH)
        c = db.cursor()
        
        c.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            results = c.fetchall()
            if results:
                output = "\n".join(str(row) for row in results[:10])
                await ctx.send(f"✅ النتائج ({len(results)}):\n```\n{output}\n```")
            else:
                await ctx.send("✅ لا توجد نتائج")
        else:
            db.commit()
            await ctx.send(f"✅ تم التنفيذ. تأثر {c.rowcount} صف")
        
        db.close()
        
    except Exception as e:
        await ctx.send(f"❌ خطأ SQL:\n```python\n{e}\n```")

@bot.command()
async def backup(ctx):
    """نسخ احتياطي"""
    if not is_ai_admin(ctx):
        return await ctx.send("❌ ليس لديك صلاحية")
    
    msg = await ctx.send("💾 جاري إنشاء نسخة احتياطية...")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(__file__), "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        files_backed = []
        
        # نسخ قاعدة البيانات
        if os.path.exists(DB_PATH):
            backup_db = os.path.join(backup_dir, f"system_{timestamp}.db")
            import shutil
            shutil.copy2(DB_PATH, backup_db)
            files_backed.append(f"✅ system.db → {os.path.basename(backup_db)}")
        
        embed = discord.Embed(title="💾 نسخة احتياطية", color=0x00FF00)
        embed.add_field(name="الملفات", value="\n".join(files_backed) if files_backed else "لا توجد ملفات", inline=False)
        embed.add_field(name="المجلد", value=f"`{backup_dir}`", inline=False)
        embed.timestamp = datetime.utcnow()
        
        await msg.edit(content="✅ تمت النسخة الاحتياطية", embed=embed)
        
    except Exception as e:
        await msg.edit(content=f"❌ فشل النسخ:\n```python\n{e}\n```")

@bot.command()
async def install(ctx, package: str):
    """تثبيت مكتبة Python"""
    if ctx.author.id not in AI_ADMIN_IDS:
        return await ctx.send("❌ هذا الأمر للمطورين فقط")
    
    msg = await ctx.send(f"📦 جاري تثبيت {package}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            await msg.edit(content=f"✅ تم تثبيت {package} بنجاح")
        else:
            await msg.edit(content=f"❌ فشل التثبيت:\n```\n{result.stderr[:500]}\n```")
    
    except subprocess.TimeoutExpired:
        await msg.edit(content="❌ انتهى الوقت المحدد")
    except Exception as e:
        await msg.edit(content=f"❌ خطأ:\n```python\n{e}\n```")

@bot.command()
async def logs(ctx, lines: int = 20):
    """عرض آخر الأخطاء"""
    if not is_ai_admin(ctx):
        return await ctx.send("❌ ليس لديك صلاحية")
    
    # محاولة قراءة ملف اللوقات
    log_files = ["bot.log", "discord.log", "error.log"]
    
    for log_file in log_files:
        log_path = os.path.join(os.path.dirname(__file__), "..", log_file)
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    last_lines = all_lines[-lines:]
                    content = "".join(last_lines)
                    
                await ctx.send(f"📋 {log_file}:\n```\n{content[:1900]}\n```")
                return
            except:
                pass
    
    await ctx.send("⚠️ لا توجد ملفات لوقات")

@bot.command()
async def status(ctx):
    """حالة النظام الكاملة"""
    embed = discord.Embed(title="📊 System Status", color=0x00FF00)
    
    # حالة البوت
    embed.add_field(name="🤖 AI Bot", value="🟢 Online", inline=True)
    embed.add_field(name="📡 Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    # حالة الملفات
    bot_exists = "🟢" if os.path.exists(MAIN_BOT_PATH) else "🔴"
    db_exists = "🟢" if os.path.exists(DB_PATH) else "🔴"
    
    embed.add_field(name="📄 bot.py", value=bot_exists, inline=True)
    embed.add_field(name="🗄️ system.db", value=db_exists, inline=True)
    
    # استخدام الذاكرة
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem = process.memory_info().rss / 1024 / 1024
        embed.add_field(name="💾 Memory", value=f"{mem:.1f} MB", inline=True)
    except:
        pass
    
    embed.timestamp = datetime.utcnow()
    await ctx.send(embed=embed)

@bot.command()
async def execute(ctx, *, code: str):
    """تنفيذ كود Python"""
    if ctx.author.id not in AI_ADMIN_IDS:
        return await ctx.send("❌ هذا الأمر للمطورين فقط")
    
    code = code.strip('`').replace('python\n', '').replace('py\n', '')
    
    msg = await ctx.send("⚙️ جاري التنفيذ...")
    
    try:
        local_vars = {
            "bot": bot,
            "ctx": ctx,
            "discord": discord,
            "asyncio": asyncio,
            "os": os,
            "sys": sys
        }
        
        exec(f"async def __ex():\n" + "\n".join(f"    {line}" for line in code.split("\n")), local_vars)
        
        result = await local_vars["__ex"]()
        
        if result:
            await msg.edit(content=f"✅ النتيجة:\n```python\n{result}\n```")
        else:
            await msg.edit(content="✅ تم التنفيذ بنجاح!")
    
    except Exception as e:
        error = traceback.format_exc()
        await msg.edit(content=f"❌ خطأ:\n```python\n{error[:1500]}\n```")

@bot.command()
async def restart(ctx):
    """إعادة تشغيل البوت"""
    if ctx.author.id not in AI_ADMIN_IDS:
        return await ctx.send("❌ هذا الأمر للمطورين فقط")
    
    await ctx.send("🔄 جاري إعادة التشغيل...")
    await bot.close()
    os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    TOKEN = os.getenv("AI_BOT_TOKEN")
    
    if not TOKEN:
        print("⚠️ يرجى تعيين AI_BOT_TOKEN في المتغيرات البيئية")
        print("مثال: export AI_BOT_TOKEN='your_token_here'")
        exit(1)
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ فشل تشغيل البوت: {e}")
        traceback.print_exc()
