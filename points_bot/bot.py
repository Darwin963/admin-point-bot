import discord
from discord.ext import commands, tasks
import sqlite3
import time
import os
import logging
import json
import random
import asyncio
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# ============================================================ 
# CONFIGURATION
# ============================================================ 

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logging.error("DISCORD_TOKEN environment variable not set.")
    exit(1)
PREFIX = "-"
LOG_CHANNEL_NAME = "staff・اللوقات・⦏👮🏻⦐"
DATABASE_URL = os.getenv("DATABASE_URL")
DB_TYPE = "postgres" if DATABASE_URL else "sqlite"


# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

# ============================================================ 
# DATABASE SETUP
# ============================================================ 
db = None
c = None

def init_db():
    """Initializes the database connection."""
    global db, c
    if DB_TYPE == "postgres":
        try:
            db = psycopg2.connect(DATABASE_URL, sslmode='require')
            c = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
            logging.info("Connected to PostgreSQL database.")
        except (psycopg2.OperationalError, psycopg2.Error) as e:
            logging.error(f"Could not connect to PostgreSQL database: {e}")
            db = None
            c = None
    elif DB_TYPE == "sqlite":
        db = sqlite3.connect("database/system.db")
        db.row_factory = sqlite3.Row
        c = db.cursor()
        logging.info("Connected to SQLite database.")
        # Create tables if they don't exist for SQLite
        c.execute("CREATE TABLE IF NOT EXISTS points (user_id BIGINT PRIMARY KEY, points INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS config (guild_id BIGINT PRIMARY KEY, points_channel BIGINT)")
        c.execute("CREATE TABLE IF NOT EXISTS salaries (user_id BIGINT PRIMARY KEY, last_salary REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS antifarm (user_id BIGINT PRIMARY KEY, last_msg TEXT, last_time REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS cooldowns (user_id BIGINT PRIMARY KEY, last_message REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id BIGINT PRIMARY KEY, reason TEXT, end_date REAL)")
        db.commit()

# ============================================================ 
# SETTINGS & IN-MEMORY DATA
# ============================================================ 

# Admin roles, copied from your setup
ADMIN_ROLES = [1092398849299058736, 1286654124527456317, 1371504049115107450, 1286656850871451688, 1293197081997086805, 1371504063086067782, 1092398849684938873, 1433877184803504439, 1433749601529233408, 1371504072582234286, 1433877098908614816, 1433749600920928286, 1433749606633832499, 1092398849299058738, 1371504076239405246, 1433749602867089498, 1433749600136593449, 1092398849647190027]

# XP requirements for each role
XP_FOR_ROLES = {
    1092398849647190027: 1,
    1433749600136593449: 90,
    1433749602867089498: 120,
    1371504076239405246: 350,
    1092398849299058738: 750,
    1433749606633832499: 1000,
    1433749600920928286: 1600,
    1433877098908614816: 2000,
    1371504072582234286: 2500,
    1433749601529233408: 3000,
    1433877184803504439: 4000,
    1092398849684938873: 10000
}

# Role tasks description
ROLE_TASKS = {
    1092398849647190027: "رد على التكتات وتفاعل ومحاسبه المخالفين",
    1433749600136593449: "رد على التكتات وتفاعل ومحاسبه المخالفين ومراقبة الادارة",
    1433749602867089498: "رد على التكتات وتفاعل ومحاسبه المخالفين وتنضيم الاداريين",
    1371504076239405246: "رد على التكتات وتفاعل ومراقبة لاعبين ماين كرافت",
    1092398849299058738: "مراقبة الاداريين في التكتات و مساعدتهم في حال احتاجوك",
    1433749606633832499: "مراقبة تكتات وماين كرافت وتفاعل",
    1433749600920928286: "مراقبة تكتات وماين كرافت وتفاعل",
    1433877098908614816: "مراقبة تكتات وماين كرافت وتفاعل ومسؤول عن الادمنز",
    1371504072582234286: "المسؤول عن قسم الادمن كامل",
    1433749601529233408: "مسؤول عن توضيف المشرفين",
    1433877184803504439: "مسؤول عن فصل وترقيات",
    1092398849647190032: "المسؤول عن قسم الفعاليات في الخادم",
    1092398849684938873: "نائب مسؤول القطاع الاداري",
    1371504063086067782: "مسؤول القطاع الاداري"
}

# Channel Names for various bot functions
LOG_CHANNEL_NAME = "staff・اللوقات・⦏👮🏻⦐"
LEVELS_CHANNEL_NAME = "المستويات"
DISMISSAL_BLACKLIST_CHANNEL_NAME = "الفصل-و-البلاكليست"
RANKS_CHANNEL_NAME = "الرتب"
ALERTS_CHANNEL_NAME = "التنبيهات"
PROMOTIONS_CHANNEL_NAME = "الترقيات"
NEWS_CHANNEL_NAME = "الاخبار"
POINTS_INFO_CHANNEL_NAME = "البوينتات"


AUTO_ROLES = {xp: role_id for role_id, xp in XP_FOR_ROLES.items()}

STAFF_SALARIES = {1092398849299058736: 150, 1286654124527456317: 130, 1371504049115107450: 120, 1286656850871451688: 110, 1293197081997086805: 100, 1092398849684938873: 75, 1433749601529233408: 65, 1433749606633832499: 45}

PROTECTED_IDS = {739749692308586526, 1020294577153908766}


POINTS_PER_MESSAGE = 1
CHAT_COOLDOWN = 30  # seconds
DAILY_MIN = 20
DAILY_MAX = 200
DAILY_COOLDOWN = 86400  # 24h
SALARY_COOLDOWN = 86400 # 24h

# In-memory stores
daily_claims = {}

# ============================================================ 
# HELPER FUNCTIONS
# ============================================================ 

def is_admin(member: discord.Member) -> bool:
    # Unified admin check
    return member.guild_permissions.administrator or any(role.id in ADMIN_ROLES for role in member.roles)

def get_points(user_id: int) -> int:
    if not db or not c: return 0
    
    query = "SELECT points FROM points WHERE user_id = %s" if DB_TYPE == "postgres" else "SELECT points FROM points WHERE user_id = ?"
    c.execute(query, (user_id,))
    row = c.fetchone()
    return row["points"] if row else 0

def set_points(user_id: int, amount: int):
    if not db or not c: return

    if DB_TYPE == "postgres":
        query = "INSERT INTO points (user_id, points) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET points = EXCLUDED.points"
    else: # sqlite
        query = "INSERT OR REPLACE INTO points (user_id, points) VALUES (?, ?)" 
    
    c.execute(query, (user_id, amount))
    db.commit()

def add_points(user_id: int, amount: int):
    if user_id in PROTECTED_IDS:
        return
    set_points(user_id, get_points(user_id) + amount)

async def send_to_channel_by_name(guild, channel_name, title, description, color=0xFFD700):
    """Sends an embed message to a channel specified by its name."""
    try:
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            logging.warning(f"Channel '{channel_name}' not found in guild {guild.name}")
            return
        embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
        await channel.send(embed=embed)
    except Exception as e:
        logging.error(f"Failed to send message to channel '{channel_name}': {e}")

async def send_log(guild, title, description, color=0xFFD700):
    """Sends a log message to the predefined log channel."""
    await send_to_channel_by_name(guild, LOG_CHANNEL_NAME, title, description, color)

async def check_auto_roles(member):
    if member.id in PROTECTED_IDS:
        return
    points = get_points(member.id)
    eligible_role_id = None

    for req_points, role_id in sorted(AUTO_ROLES.items(), reverse=True):
        if points >= req_points:
            eligible_role_id = role_id
            break

    if not eligible_role_id:
        return

    role = member.guild.get_role(eligible_role_id)
    if role and role not in member.roles:
        try:
            # Remove other auto roles before adding the new one
            for rid in AUTO_ROLES.values():
                if rid != eligible_role_id:
                    r = member.guild.get_role(rid)
                    if r and r in member.roles:
                        await member.remove_roles(r)
            
            await member.add_roles(role)
            await send_log(
                member.guild,
                "🏅 Auto Role",
                f"{member.mention} حصل على رتبة **{role.name}** ({points} نقطة)",
                0x57F287
            )
        except discord.errors.Forbidden:
            logging.error(f"Missing 'Manage Roles' permission in guild {member.guild.name} to auto-assign roles.")

# ============================================================ 
# EVENTS
# ============================================================ 

@bot.event
async def on_ready():
    init_db()
    logging.info(f'🔥 SYSTEM ONLINE — Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="إدارة النقاط"))
    
    # Start background tasks
    if not salary_loop.is_running():
        salary_loop.start()
    if not blacklist_check_loop.is_running():
        blacklist_check_loop.start()


@bot.event
async def on_disconnect():
    logging.warning("Bot disconnected.")

@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Command error in '{ctx.command}': {error}")
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("الأمر غير موجود.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("ليس لديك صلاحية لاستخدام هذا الأمر.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"الرجاء توفير كافة المتطلبات. الاستخدام: `{PREFIX}{ctx.command.name} {ctx.command.signature}`")
    else:
        await ctx.send("حدث خطأ غير متوقع.")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not db or not c:
        return

    # First, process commands so they aren't blocked
    await bot.process_commands(message)

    user_id = message.author.id
    now = time.time()

    # ===== Anti-Farm (Spam Protection) =====
    query = "SELECT last_msg, last_time FROM antifarm WHERE user_id = %s" if DB_TYPE == "postgres" else "SELECT last_msg, last_time FROM antifarm WHERE user_id = ?"
    c.execute(query, (user_id,))
    r = c.fetchone()
    if r:
        # Simple spam check: same message or too fast
        if r["last_msg"] == message.content or (now - r["last_time"]) < 2:
            return # Ignore message for points, but commands still work
    
    if DB_TYPE == "postgres":
        c.execute("INSERT INTO antifarm (user_id, last_msg, last_time) VALUES (%s,%s,%s) ON CONFLICT (user_id) DO UPDATE SET last_msg = EXCLUDED.last_msg, last_time = EXCLUDED.last_time", (user_id, message.content, now))
    else: # sqlite
        c.execute("INSERT OR REPLACE INTO antifarm VALUES (?,?,?)", (user_id, message.content, now))
    db.commit()

    # ===== Chat Points Cooldown =====
    query = "SELECT last_message FROM cooldowns WHERE user_id = %s" if DB_TYPE == "postgres" else "SELECT last_message FROM cooldowns WHERE user_id = ?"
    c.execute(query, (user_id,))
    r = c.fetchone()
    if not r or (now - r["last_message"]) >= CHAT_COOLDOWN:
        add_points(user_id, POINTS_PER_MESSAGE)
        if DB_TYPE == "postgres":
            c.execute("INSERT INTO cooldowns (user_id, last_message) VALUES (%s,%s) ON CONFLICT (user_id) DO UPDATE SET last_message = EXCLUDED.last_message", (user_id, now))
        else: # sqlite
            c.execute("INSERT OR REPLACE INTO cooldowns VALUES (?,?)", (user_id, now))
        db.commit()
        await check_auto_roles(message.author) # Check roles after points change


# ============================================================ 
# COMMANDS
# ============================================================ 

@bot.command(name="help")
async def help_command(ctx, category: str = None):
    """(AR) يعرض قائمة المساعدة الشاملة."""
    prefix = PREFIX
    if not category:
        embed = discord.Embed(
            title=" قائمة المساعدة لنظام النقاط",
            description=f"استخدم `{prefix}help <الفئة>` لعرض المزيد من المعلومات.",
            color=0x5865F2
        )
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.add_field(name="اوامر", value=f"عرض جميع أوامر البوت المتاحة.\n`{prefix}help commands`", inline=True)
        embed.add_field(name="الرتب", value=f"عرض الرتب الإدارية والمهام والنقاط المطلوبة.\n`{prefix}help ranks`", inline=True)
        embed.add_field(name="معلومات", value=f"معلومات عن القنوات والنظام بشكل عام.\n`{prefix}help info`", inline=True)
        
        await ctx.send(embed=embed)
        return

    category = category.lower()

    if category == "commands":
        embed = discord.Embed(title="📖 أوامر البوت", color=0x5865F2)
        embed.add_field(name=f"{prefix}points [member]", value="لمعرفة نقاطك أو نقاط عضو آخر.", inline=False)
        embed.add_field(name=f"{prefix}level [member]", value="لعرض مستوى العضو ونقاطه للترقية التالية.", inline=False)
        embed.add_field(name=f"{prefix}daily", value="للحصول على المكافأة اليومية.", inline=False)
        embed.add_field(name=f"{prefix}top", value="لعرض قائمة أعلى الأعضاء نقاطًا.", inline=False)
        embed.add_field(name=f"{prefix}ranks", value="لعرض الرتب والمتطلبات.", inline=False)
        embed.add_field(name=f"{prefix}status", value="للاطلاع على حالة أنظمة البوت.", inline=False)
        
        if is_admin(ctx.author):
            embed.add_field(name="--- 👮🏻 أوامر الإدارة ---", value=" ", inline=False)
            embed.add_field(name=f"{prefix}addpoints <@user> <amount>", value="إضافة نقاط لعضو.", inline=False)
            embed.add_field(name=f"{prefix}removepoints <@user> <amount>", value="خصم نقاط من عضو.", inline=False)
            embed.add_field(name=f"{prefix}blacklist <@user> <days> <reason>", value="إضافة عضو للقائمة السوداء.", inline=False)
            embed.add_field(name=f"{prefix}unblacklist <@user>", value="إزالة عضو من القائمة السوداء.", inline=False)
            embed.add_field(name=f"{prefix}blacklistcheck <@user>", value="التحقق من حالة عضو في القائمة السوداء.", inline=False)
            embed.add_field(name=f"{prefix}announce <#channel> <title> <message>", value="إرسال إعلان عام في قناة معينة.", inline=False)
            embed.add_field(name=f"{prefix}promotion <@user> <@role> <reason>", value=" للإعلان عن ترقية عضو.", inline=False)
            embed.add_field(name=f"{prefix}news <message>", value="لنشر خبر جديد.", inline=False)
            embed.add_field(name=f"{prefix}alert <message>", value="لإرسال تنبيه إداري.", inline=False)
            embed.add_field(name=f"{prefix}setup", value="لإعداد قناة النقاط.", inline=False)
            embed.add_field(name=f"{prefix}panel", value="لإظهار لوحة تحكم الإدارة.", inline=False)
        
        await ctx.send(embed=embed)
    
    elif category == "ranks":
        await ranks_command(ctx) # Use the existing ranks command
        
    elif category == "info":
        embed = discord.Embed(title="معلومات عن النظام", color=0x3498DB)
        embed.description = "هنا شرح للقنوات المختلفة التي يستخدمها البوت والغرض منها."
        
        embed.add_field(name="اللوقات (Logs)", value="يتم في هذه القناة تسجيل جميع الإجراءات المهمة التي يقوم بها البوت أو الإداريون، مثل إضافة/خصم النقاط، الترقيات، وغيرها.", inline=False)
        embed.add_field(name="المستويات (Levels)", value="يتم استخدامها لعرض معلومات عن مستويات الأعضاء الإداريين بناءً على نقاطهم.", inline=False)
        embed.add_field(name="الفصل والبلاكليست", value="يتم هنا الإعلان عن فصل الأعضاء غير المتفاعلين أو إضافة أعضاء إلى القائمة السوداء (Blacklist) ومنعهم من التقديم لفترة محددة.", inline=False)
        embed.add_field(name="التنبيهات (Alerts)", value="قناة للقرارات الصادرة من الإدارة العليا، مثل التنبيهات حول الأداء، الأخطاء، أو العقوبات.", inline=False)
        embed.add_field(name="الترقيات (Promotions)", value="يتم فيها الإعلان عن ترقيات الأعضاء من رتبة إلى أخرى مع ذكر السبب والمسؤول عن الترقية.", inline=False)
        embed.add_field(name="الأخبار (News)", value="للأخبار والإعلانات الصادرة من الإدارة العليا.", inline=False)
        embed.add_field(name="البوينتات (Points)", value="لعرض معلومات عامة عن نظام النقاط وقائمة الرتب.", inline=False)
        
        await ctx.send(embed=embed)

    else:
        await ctx.send(f"الفئة `{prefix} غير موجودة. استخدم `{prefix}help` لرؤية الفئات المتاحة.")

@bot.command()
async def points(ctx, member: discord.Member = None):
    """عرض نقاطك أو نقاط عضو آخر"""
    target = member or ctx.author
    await ctx.send(f"⭐ نقاط {target.display_name}: **{get_points(target.id)}**")

@bot.command(name="level")
async def level_command(ctx, member: discord.Member = None):
    """يعرض مستوى العضو ونقاطه للترقية التالية"""
    target = member or ctx.author
    points = get_points(target.id)

    sorted_roles = sorted(XP_FOR_ROLES.items(), key=lambda item: item[1])
    
    current_role = None
    next_role = None
    xp_for_next = 0

    for role_id, xp_req in sorted_roles:
        if points >= xp_req:
            current_role = ctx.guild.get_role(role_id)
        else:
            next_role = ctx.guild.get_role(role_id)
            xp_for_next = xp_req
            break
    
    embed = discord.Embed(title=f"🏆 Level Information for {target.display_name}", color=target.color)
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="Points", value=f"`{points}`", inline=False)
    
    if current_role:
        embed.add_field(name="Current Level", value=current_role.mention, inline=False)
    else:
        embed.add_field(name="Current Level", value="No rank", inline=False)

    if next_role:
        points_needed = xp_for_next - points
        embed.add_field(name="Next Level", value=f"{next_role.mention}", inline=False)
        embed.add_field(name="Points to Next Level", value=f"`{points_needed}` more points required.", inline=False)
        # Simple progress bar
        progress = int((points / xp_for_next) * 20)
        embed.add_field(name="Progress", value=f"[`{'=' * progress}{' ' * (20 - progress)}`]", inline=False)
    else:
        embed.add_field(name="Next Level", value="You are at the highest level! 🎉", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def addpoints(ctx, member: discord.Member, amount: int):
    """إضافة نقاط (إداري)"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")
    if member.id in PROTECTED_IDS:
        return await ctx.send("❌ لا يمكن تعديل نقاط هذا العضو لأنه محمي.")
    if amount <= 0:
        return await ctx.send("❌ يرجى تحديد رقم موجب.")

    add_points(member.id, amount)
    await ctx.send(f"✅ تم إضافة {amount} نقطة لـ {member.mention}")
    await send_log(ctx.guild, "➕ Add Points", f"{ctx.author.mention} أضاف {amount} نقطة لـ {member.mention}")
    await check_auto_roles(member)

@bot.command()
async def removepoints(ctx, member: discord.Member, amount: int):
    """خصم نقاط (إداري)"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")
    if member.id in PROTECTED_IDS:
        return await ctx.send("❌ لا يمكن تعديل نقاط هذا العضو لأنه محمي.")
    if amount <= 0:
        return await ctx.send("❌ يرجى تحديد رقم موجب.")

    add_points(member.id, -amount)
    await ctx.send(f"➖ تم خصم {amount} نقطة من {member.mention}")
    await send_log(ctx.guild, "➖ Remove Points", f"{ctx.author.mention} خصم {amount} نقطة من {member.mention}")
    await check_auto_roles(member)
    
@bot.command()
async def daily(ctx):
    user_id = ctx.author.id
    now = time.time()
    last_claim = daily_claims.get(user_id, 0)
    
    if (now - last_claim) < DAILY_COOLDOWN:
        remaining = int(DAILY_COOLDOWN - (now - last_claim))
        hours, rem = divmod(remaining, 3600)
        minutes, _ = divmod(rem, 60)
        return await ctx.send(f"⏳ تقدر تاخذ الديلي بعد {hours} ساعة و {minutes} دقيقة")

    roll = random.randint(1, 100)
    if roll == 100: reward = 200
    elif roll >= 90: reward = random.randint(120, 180)
    else: reward = random.randint(DAILY_MIN, 80)

    add_points(user_id, reward)
    daily_claims[user_id] = now
    
    await ctx.send(f"🎁 حصلت على **{reward} نقطة** (ديلي)\n⭐ نقاطك الآن: {get_points(user_id)}")
    await send_log(ctx.guild, "🎁 Daily Reward", f"{ctx.author.mention} حصل على {reward} نقطة")
    await check_auto_roles(ctx.author)

@bot.command()
async def top(ctx):
    if not db or not c: return await ctx.send("❌ لا يوجد بيانات")

    c.execute("SELECT user_id, points FROM points ORDER BY points DESC LIMIT 10")
    rows = c.fetchall()

    if not rows:
        return await ctx.send("❌ لا يوجد بيانات")

    embed = discord.Embed(title="🏆 أعلى 10 نقاط", color=0x00FFAA)
    for i, row in enumerate(rows, start=1):
        user = ctx.guild.get_member(row['user_id'])
        name = user.display_name if user else f"ID: {row['user_id']}"
        embed.add_field(name=f"#{i} — {name}", value=f"{row['points']} نقطة", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def status(ctx):
    embed = discord.Embed(title="📡 System Status", color=0x00FFAA)
    embed.add_field(name="💬 Chat Points", value="🟢 يعمل", inline=True)
    embed.add_field(name="🎁 Daily Rewards", value="🟢 يعمل", inline=True)
    embed.add_field(name="🚫 Anti-Farm", value="🟢 يعمل", inline=True)
    embed.add_field(name="🏅 Auto Roles", value="🟢 يعمل", inline=True)
    embed.add_field(name="💰 Staff Salaries", value="🟢 يعمل", inline=True)
    embed.add_field(name="🛠 Control Panel", value="🟢 يعمل", inline=True)
    
    if db and c:
        query = "SELECT points_channel FROM config WHERE guild_id = %s" if DB_TYPE == "postgres" else "SELECT points_channel FROM config WHERE guild_id = ?"
        c.execute(query, (ctx.guild.id,))
        r = c.fetchone()
        if r:
            channel = ctx.guild.get_channel(r["points_channel"])
            embed.add_field(name="📌 Points Channel", value=channel.mention if channel else "❌ غير موجود", inline=False)
        else:
            embed.add_field(name="📌 Points Channel", value="❌ لم يتم الإعداد", inline=False)
            
    await ctx.send(embed=embed)

@bot.command(name="ranks")
async def ranks_command(ctx):
    """يعرض قائمة بالرتب ومهامها ومتطلباتها"""
    embed = discord.Embed(title="📜 الرتب والمهام والمتطلبات", color=0x3498DB)
    
    # Create a reverse mapping from role ID to XP for sorting
    role_id_to_xp = {v: k for k, v in XP_FOR_ROLES.items()}
    
    # Sort roles by XP requirement
    sorted_role_ids = sorted(ROLE_TASKS.keys(), key=lambda r: role_id_to_xp.get(r, float('inf')))

    for role_id in sorted_role_ids:
        task = ROLE_TASKS.get(role_id, "No task defined.")
        xp_req = role_id_to_xp.get(role_id)
        role = ctx.guild.get_role(role_id)
        if role:
            embed.add_field(
                name=f"{role.name}",
                value=f"**المهام:** {task}\n**النقاط المطلوبة:** {xp_req if xp_req is not None else 'N/A'}",
                inline=False
            )
            
    await ctx.send(embed=embed)

# ============================================================
# ANNOUNCEMENT COMMANDS
# ============================================================

@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, title: str, *, message: str):
    """إرسال إعلان إلى قناة محددة"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")
    
    await send_to_channel_by_name(ctx.guild, channel.name, title, message)
    await ctx.send(f"✅ تم إرسال الإعلان إلى {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def promotion(ctx, member: discord.Member, role: discord.Role, *, reason: str):
    """الإعلان عن ترقية عضو"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")

    description = f"**Congratulations to {member.mention} on their promotion to {role.mention}!**\n\n**Reason:** {reason}\n\nPromoted by: {ctx.author.mention}"
    await send_to_channel_by_name(ctx.guild, PROMOTIONS_CHANNEL_NAME, "🎉 Promotion", description, 0x00FF00)
    await ctx.send("✅ تم إعلان الترقية.")

@bot.command()
@commands.has_permissions(administrator=True)
async def news(ctx, *, message: str):
    """نشر خبر في قناة الأخبار"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")

    await send_to_channel_by_name(ctx.guild, NEWS_CHANNEL_NAME, "📰 News", message, 0x3498DB)
    await ctx.send("✅ تم نشر الخبر.")

@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message: str):
    """إرسال تنبيه إلى قناة التنبيهات"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")

    await send_to_channel_by_name(ctx.guild, ALERTS_CHANNEL_NAME, "️ Alert", message, 0xFFCC00)
    await ctx.send("✅ تم إرسال التنبيه.")

# ============================================================
# BLACKLIST COMMANDS
# ============================================================

@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist(ctx, member: discord.Member, duration: int, *, reason: str):
    """حظر عضو من التقديمات"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")
    
    end_date = time.time() + (duration * 86400) # days to seconds
    
    if DB_TYPE == "postgres":
        query = "INSERT INTO blacklist (user_id, reason, end_date) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET reason = EXCLUDED.reason, end_date = EXCLUDED.end_date"
    else: # sqlite
        query = "INSERT OR REPLACE INTO blacklist (user_id, reason, end_date) VALUES (?, ?, ?)"
    
    c.execute(query, (member.id, reason, end_date))
    db.commit()
    
    await ctx.send(f"✅ تم إضافة {member.mention} إلى القائمة السوداء لمدة {duration} يوم.")
    await send_to_channel_by_name(ctx.guild, DISMISSAL_BLACKLIST_CHANNEL_NAME, "🚫 Blacklisted", f"**User:** {member.mention}\n**By:** {ctx.author.mention}\n**Duration:** {duration} days\n**Reason:** {reason}", 0xFF0000)

@bot.command()
@commands.has_permissions(administrator=True)
async def unblacklist(ctx, member: discord.Member):
    """إزالة عضو من القائمة السوداء"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")

    if DB_TYPE == "postgres":
        query = "DELETE FROM blacklist WHERE user_id = %s"
    else: # sqlite
        query = "DELETE FROM blacklist WHERE user_id = ?"
    
    c.execute(query, (member.id,))
    db.commit()

    await ctx.send(f"✅ تم إزالة {member.mention} من القائمة السوداء.")
    await send_to_channel_by_name(ctx.guild, DISMISSAL_BLACKLIST_CHANNEL_NAME, "✅ Unblacklisted", f"**User:** {member.mention}\n**By:** {ctx.author.mention}", 0x00FF00)

@bot.command()
async def blacklistcheck(ctx, member: discord.Member):
    """التحقق من وجود عضو في القائمة السوداء"""
    query = "SELECT reason, end_date FROM blacklist WHERE user_id = %s" if DB_TYPE == "postgres" else "SELECT reason, end_date FROM blacklist WHERE user_id = ?"
    c.execute(query, (member.id,))
    r = c.fetchone()
    if r:
        remaining_seconds = r["end_date"] - time.time()
        if remaining_seconds > 0:
            remaining_days = int(remaining_seconds / 86400)
            await ctx.send(f"🔴 {member.mention} في القائمة السوداء.\n**السبب:** {r['reason']}\n**متبقي:** {remaining_days} يوم.")
        else:
            await ctx.send(f"🟢 {member.mention} ليس في القائمة السوداء.")
    else:
        await ctx.send(f"🟢 {member.mention} ليس في القائمة السوداء.")


# ============================================================ 
# ADMIN COMMANDS & SETUP
# ============================================================ 

class ChannelSetupModal(discord.ui.Modal, title="إعداد قناة النقاط"):
    def __init__(self, guild):
        super().__init__()
        self.guild = guild
        self.channel_id = discord.ui.TextInput(
            label="معرف القناة (ID)",
            placeholder="أدخل معرف القناة فقط (مثلاً: 123456789)",
            required=True,
            min_length=17,
            max_length=20
        )
        self.add_item(self.channel_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        if not db or not c:
            return await interaction.response.send_message("❌ Database not connected.", ephemeral=True)
        
        try:
            channel_id = int(self.channel_id.value)
            channel = self.guild.get_channel(channel_id)
            
            if not channel:
                return await interaction.response.send_message("❌ لم يتم العثور على القناة.", ephemeral=True)
            
            if DB_TYPE == "postgres":
                query = "INSERT INTO config (guild_id, points_channel) VALUES (%s, %s) ON CONFLICT (guild_id) DO UPDATE SET points_channel = EXCLUDED.points_channel"
            else:
                query = "INSERT OR REPLACE INTO config (guild_id, points_channel) VALUES (?, ?)"
            
            c.execute(query, (interaction.guild.id, channel_id))
            db.commit()
            
            await interaction.response.send_message(f"✅ تم تحديد {channel.mention} كقناة للنقاط", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ الرجاء إدخال معرف صالح.", ephemeral=True)


class ChannelSelectView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild
        self.selected_channel = None
    
    @discord.ui.select(
        placeholder="📌 اختر قناة النقاط",
        min_values=1,
        max_values=1
    )
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        if not db or not c:
            return await interaction.response.send_message("❌ Database not connected.", ephemeral=True)
        
        channel_id = int(select.values[0])
        channel = self.guild.get_channel(channel_id)
        
        if DB_TYPE == "postgres":
            query = "INSERT INTO config (guild_id, points_channel) VALUES (%s, %s) ON CONFLICT (guild_id) DO UPDATE SET points_channel = EXCLUDED.points_channel"
        else:
            query = "INSERT OR REPLACE INTO config (guild_id, points_channel) VALUES (?, ?)"
        
        c.execute(query, (interaction.guild.id, channel_id))
        db.commit()
        
        self.selected_channel = channel.mention
        await interaction.response.send_message(f"✅ تم تحديد {channel.mention} كقناة للنقاط", ephemeral=True)
        self.stop()
    
    @discord.ui.button(label="📝 إدخال يدوي", style=discord.ButtonStyle.secondary, emoji="⌨️")
    async def manual_input(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChannelSetupModal(self.guild))


class SetupView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild
        
        # Get all text channels and create options (max 25 due to Discord limit)
        channels = [ch for ch in guild.text_channels]
        options = [
            discord.SelectOption(label=ch.name[:100], value=str(ch.id), description=ch.category.name if ch.category else "No Category")
            for ch in channels[:25]
        ]
        
        if len(channels) > 25:
            logging.warning(f"Guild {guild.name} has more than 25 text channels. Only showing the first 25.")
        
        self.add_item(ChannelSelectSelect(custom_id="setup_select", options=options, placeholder="📌 اختر قناة النقاط"))


class ChannelSelectSelect(discord.ui.Select):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def callback(self, interaction: discord.Interaction):
        if not db or not c:
            return await interaction.response.send_message("❌ Database not connected.", ephemeral=True)
        
        channel_id = int(self.values[0])
        channel = interaction.guild.get_channel(channel_id)
        
        if DB_TYPE == "postgres":
            query = "INSERT INTO config (guild_id, points_channel) VALUES (%s, %s) ON CONFLICT (guild_id) DO UPDATE SET points_channel = EXCLUDED.points_channel"
        else:
            query = "INSERT OR REPLACE INTO config (guild_id, points_channel) VALUES (?, ?)"
        
        c.execute(query, (interaction.guild.id, channel_id))
        db.commit()
        
        await interaction.response.send_message(f"✅ تم تحديد {channel.mention} كقناة للنقاط", ephemeral=True)


@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """إعداد قناة النقاط"""
    if not db or not c:
        return await ctx.send("❌ Database not connected.")
    
    # Create a view with channel selection
    view = discord.ui.View(timeout=60)
    
    channels = [ch for ch in ctx.guild.text_channels]
    options = [
        discord.SelectOption(label=ch.name[:100], value=str(ch.id))
        for ch in channels[:25]
    ]
    
    async def select_callback(interaction: discord.Interaction):
        if not db or not c:
            return await interaction.response.send_message("❌ Database not connected.", ephemeral=True)
        
        channel_id = int(interaction.data["values"][0])
        channel = ctx.guild.get_channel(channel_id)
        
        if DB_TYPE == "postgres":
            query = "INSERT INTO config (guild_id, points_channel) VALUES (%s, %s) ON CONFLICT (guild_id) DO UPDATE SET points_channel = EXCLUDED.points_channel"
        else:
            query = "INSERT OR REPLACE INTO config (guild_id, points_channel) VALUES (?, ?)"
        
        c.execute(query, (ctx.guild.id, channel_id))
        db.commit()
        
        await interaction.response.send_message(f"✅ تم تحديد {channel.mention} كقناة للنقاط", ephemeral=True)
    
    select = discord.ui.Select(
        placeholder="📌 اختر قناة النقاط",
        options=options,
        custom_id="setup_select"
    )
    select.callback = select_callback
    view.add_item(select)
    
    # Add manual input button
    async def modal_callback(interaction: discord.Interaction):
        await interaction.response.send_modal(ChannelSetupModal(ctx.guild))
    
    manual_btn = discord.ui.Button(
        label="📝 إدخال يدوي",
        style=discord.ButtonStyle.secondary,
        emoji="⌨️",
        custom_id="manual_input"
    )
    manual_btn.callback = modal_callback
    view.add_item(manual_btn)
    
    embed = discord.Embed(
        title="⚙️ إعداد نظام النقاط",
        description="اختر القناة التي سيظهر فيها نظام النقاط.\n\n💡 يمكنك إدخال معرف القناة يدوياً إذا لم تجدها في القائمة.",
        color=0xFFD700
    )
    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def removesetup(ctx):
    """إزالة إعداد قناة النقاط"""
    if not db or not c:
        return await ctx.send("❌ Database not connected.")
    
    if DB_TYPE == "postgres":
        query = "DELETE FROM config WHERE guild_id = %s"
    else:
        query = "DELETE FROM config WHERE guild_id = ?"
    
    c.execute(query, (ctx.guild.id,))
    db.commit()
    
    await ctx.send("✅ تم إزالة إعداد قناة النقاط بنجاح")
    await send_log(ctx.guild, "⚙️ Remove Setup", f"{ctx.author.mention} قام بإزالة إعداد قناة النقاط", 0xFF9900)

class ControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Check for admin role on every interaction with this view
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👤 إضافة نقاط", style=discord.ButtonStyle.success, emoji="➕", custom_id="panel_addpoints")
    async def add_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="➕ إضافة نقاط",
            description="استخدم الأمر: `-addpoints <@member> <amount>`\n\nمثال: `-addpoints @user 100`",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="👤 خصم نقاط", style=discord.ButtonStyle.danger, emoji="➖", custom_id="panel_removepoints")
    async def remove_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="➖ خصم نقاط",
            description="استخدم الأمر: `-removepoints <@member> <amount>`\n\nمثال: `-removepoints @user 50`",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🚫 القائمة السوداء", style=discord.ButtonStyle.danger, emoji="⛔", custom_id="panel_blacklist")
    async def blacklist(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🚫 القائمة السوداء",
            description="**أمر الحظر:**\n`-blacklist <@member> <days> <reason>`\n\nمثال: `-blacklist @user 30 Spam`\n\n**إزالة الحظر:**\n`-unblacklist <@member>`\n\n**التحقق:**\n`-blacklistcheck <@member>`",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📢 إعلان", style=discord.ButtonStyle.primary, emoji="📣", custom_id="panel_announce")
    async def announce(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📢 إرسال إعلان",
            description="استخدم الأمر: `-announce <#channel> <title> <message>`\n\nمثال: `-announce #general ⚠️ تنبيه هام`\n\nأو استخدم أوامر الإدارة الأخرى:\n- `-promotion` - للترقيات\n- `-news` - للأخبار\n- `-alert` - للتنبيهات",
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📊 النقاط", style=discord.ButtonStyle.secondary, emoji="⭐", custom_id="panel_points")
    async def points_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⭐ أوامر النقاط",
            description="**-points [member]** - عرض نقاطك أو نقاط عضو آخر\n\n**-level [member]** - عرض المستوى ونقاط الترقية\n\n**-top** - عرض أعلى النقاط\n\n**-ranks** - عرض الرتب والمتطلبات",
            color=0xFFD700
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="💰 اليومية", style=discord.ButtonStyle.success, emoji="🎁", custom_id="panel_daily")
    async def daily(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎁 المكافأة اليومية",
            description="استخدم الأمر: `-daily`\n\nللحصول على نقاط يومية عشوائية (20-200 نقطة)\n\n⚠️ يمكنك المطالبة مرة كل 24 ساعة فقط",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📈 الحالة", style=discord.ButtonStyle.secondary, emoji="📡", custom_id="panel_status")
    async def status(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📡 حالة النظام",
            description="استخدم الأمر: `-status`\n\nلعرض حالة جميع أنظمة البوت",
            color=0x00FFAA
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚙️ الإعداد", style=discord.ButtonStyle.secondary, emoji="🔧", custom_id="panel_setup")
    async def setup_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚙️ إعداد نظام النقاط",
            description="**-setup** - لتحديد قناة النقاط\n\n**-removesetup** - لإزالة إعداد قناة النقاط",
            color=0xFFD700
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command()
async def panel(ctx):
    """لوحة تحكم الإدارة"""
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")
    
    embed = discord.Embed(
        title="🛠 لوحة تحكم الإدارة",
        description="**أوامر الإدارة المتاحة:**\n\n" +
        "➕ **إضافة نقاط:** `-addpoints <@member> <amount>`\n" +
        "➖ **خصم نقاط:** `-removepoints <@member> <amount>`\n" +
        "⛔ **القائمة السوداء:** `-blacklist <@member> <days> <reason>`\n" +
        "✅ **إزالة الحظر:** `-unblacklist <@member>`\n" +
        "🔍 **التحقق:** `-blacklistcheck <@member>`\n" +
        "📢 **إعلان:** `-announce <#channel> <title> <message>`\n" +
        "🎉 **ترقية:** `-promotion <@member> <@role> <reason>`\n" +
        "📰 **خبر:** `-news <message>`\n" +
        "⚠️ **تنبيه:** `-alert <message>`\n" +
        "⚙️ **إعداد:** `-setup`\n" +
        "❌ **إزالة الإعداد:** `-removesetup`",
        color=0xFFD700
    )
    embed.set_footer(text="جميع هذه الأوامر متاحة فقط للإدارة العليا")
    await ctx.send(embed=embed, view=ControlPanel())


# ============================================================ 
# BACKGROUND TASKS
# ============================================================ 

@tasks.loop(hours=1)
async def salary_loop():
    if not db or not c: return
    
    now = time.time()
    for guild in bot.guilds:
        for member in guild.members:
            if member.bot: continue
            for role in member.roles:
                if role.id in STAFF_SALARIES:
                    
                    query = "SELECT last_salary FROM salaries WHERE user_id = %s" if DB_TYPE == "postgres" else "SELECT last_salary FROM salaries WHERE user_id = ?"
                    c.execute(query, (member.id,))
                    r = c.fetchone()

                    if not r or (now - r["last_salary"]) >= SALARY_COOLDOWN:
                        amount = STAFF_SALARIES[role.id]
                        add_points(member.id, amount)

                        if DB_TYPE == "postgres":
                            c.execute("INSERT INTO salaries (user_id, last_salary) VALUES (%s,%s) ON CONFLICT (user_id) DO UPDATE SET last_salary = EXCLUDED.last_salary", (member.id, now))
                        else:
                            c.execute("INSERT OR REPLACE INTO salaries VALUES (?,?)", (member.id, now))
                        db.commit()
                        
                        await send_log(guild, "💰 Salary", f"{member.mention} استلم راتب {amount} نقطة", 0x00FF00)
                        await check_auto_roles(member)
                    break # Process only the highest salary role

@tasks.loop(hours=1)
async def blacklist_check_loop():
    if not db or not c: return

    query = "SELECT user_id, reason, end_date FROM blacklist"
    c.execute(query)
    rows = c.fetchall()
    now = time.time()

    for row in rows:
        if now > row["end_date"]:
            if DB_TYPE == "postgres":
                del_query = "DELETE FROM blacklist WHERE user_id = %s"
            else:
                del_query = "DELETE FROM blacklist WHERE user_id = ?"
            c.execute(del_query, (row["user_id"],))
            db.commit()

            for guild in bot.guilds:
                member = guild.get_member(row["user_id"])
                if member:
                    await send_to_channel_by_name(guild, DISMISSAL_BLACKLIST_CHANNEL_NAME, "⌛️ Blacklist Expired", f"**User:** {member.mention}'s blacklist has expired.", 0x00FF00)


# ============================================================ 
# BOT RUN
# ============================================================ 

def run_bot():
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        logging.error("Invalid token. Check DISCORD_TOKEN environment variable.")
    except Exception as e:
        logging.error(f"Bot crashed: {e}. Restarting in 5 seconds...")
        time.sleep(5)
        run_bot() # Recursive call to restart
    finally:
        if db:
            db.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    keep_alive()
    run_bot()
