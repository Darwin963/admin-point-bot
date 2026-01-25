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

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

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
        db = sqlite3.connect("system.db")
        db.row_factory = sqlite3.Row
        c = db.cursor()
        logging.info("Connected to SQLite database.")
        # Create tables if they don't exist for SQLite
        c.execute("CREATE TABLE IF NOT EXISTS points (user_id BIGINT PRIMARY KEY, points INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS config (guild_id BIGINT PRIMARY KEY, points_channel BIGINT)")
        c.execute("CREATE TABLE IF NOT EXISTS salaries (user_id BIGINT PRIMARY KEY, last_salary REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS antifarm (user_id BIGINT PRIMARY KEY, last_msg TEXT, last_time REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS cooldowns (user_id BIGINT PRIMARY KEY, last_message REAL)")
        db.commit()

# ============================================================ 
# SETTINGS & IN-MEMORY DATA
# ============================================================ 

ADMIN_ROLES = [1092398849299058736, 1286654124527456317, 1371504049115107450, 1286656850871451688, 1293197081997086805, 1371504063086067782, 1092398849684938873, 1433877184803504439, 1433749601529233408, 1371504072582234286, 1433877098908614816, 1433749600920928286, 1433749606633832499, 1092398849299058738, 1371504076239405246, 1433749602867089498, 1433749600136593449, 1092398849647190027]
AUTO_ROLES = {50: 1092398849647190027, 100: 1433749600136593449, 150: 1433749602867089498, 200: 1371504076239405246, 300: 1092398849299058738, 400: 1433749606633832499, 500: 1433749601529233408, 600: 1092398849684938873, 700: 1293197081997086805, 800: 1286656850871451688, 900: 1371504049115107450, 1000: 1286654124527456317, 1200: 1092398849299058736}
STAFF_SALARIES = {1092398849299058736: 150, 1286654124527456317: 130, 1371504049115107450: 120, 1286656850871451688: 110, 1293197081997086805: 100, 1092398849684938873: 75, 1433749601529233408: 65, 1433749606633832499: 45}

PROTECTED_IDS = {739749692308586526, 1020294577153908766}


POINTS_PER_MESSAGE = 1
CHAT_COOLDOWN = 30  # seconds
DAILY_MIN = 20
DAILY_MAX = 200
DAILY_COOLDOWN = 86400  # 24h
SALARY_COOLDOWN = 86400 # 24h
TOP_BROADCAST_INTERVAL = 180  # 3 minutes

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

async def send_log(guild, title, description, color=0xFFD700):
    try:
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if not channel:
            logging.warning(f"Log channel '{LOG_CHANNEL_NAME}' not found in guild {guild.name}")
            return
        embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
        await channel.send(embed=embed)
    except Exception as e:
        logging.error(f"Failed to send log: {e}")

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
    if not auto_top_loop.is_running():
        auto_top_loop.start()


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
async def help_command(ctx):
    embed = discord.Embed(title="📖 Help — Points System", color=0x5865F2)
    embed.add_field(name=f"{PREFIX}points", value="معرفة نقاطك", inline=False)
    embed.add_field(name=f"{PREFIX}daily", value="استلام المكافأة اليومية", inline=False)
    embed.add_field(name=f"{PREFIX}top", value="أعلى نقاط بالسيرفر", inline=False)
    embed.add_field(name=f"{PREFIX}status", value="حالة أنظمة البوت", inline=False)
    if is_admin(ctx.author):
        embed.add_field(name="--- Admin Commands ---", value="\u200b", inline=False)
        embed.add_field(name=f"{PREFIX}addpoints <@user> <amount>", value="إضافة نقاط لعضو", inline=False)
        embed.add_field(name=f"{PREFIX}removepoints <@user> <amount>", value="خصم نقاط من عضو", inline=False)
        embed.add_field(name=f"{PREFIX}setup", value="إعداد روم النقاط", inline=False)
        embed.add_field(name=f"{PREFIX}panel", value="لوحة تحكم الإدارة", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def points(ctx, member: discord.Member = None):
    """عرض نقاطك أو نقاط عضو آخر"""
    target = member or ctx.author
    await ctx.send(f"⭐ نقاط {target.display_name}: **{get_points(target.id)}**")

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

# ============================================================ 
# ADMIN COMMANDS & SETUP
# ============================================================ 

class SetupView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild
        
        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in self.guild.text_channels
        ]
        
        if len(options) > 25:
            logging.warning(f"Guild {guild.name} has more than 25 text channels. Only showing the first 25.")
            options = options[:25]

        self.children[0].options = options

    @discord.ui.select(placeholder="📌 اختر روم النقاط")
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        if not db or not c:
            return await interaction.response.send_message("❌ Database not connected.", ephemeral=True)
            
        channel_id = int(select.values[0])

        if DB_TYPE == "postgres":
            query = "INSERT INTO config (guild_id, points_channel) VALUES (%s, %s) ON CONFLICT (guild_id) DO UPDATE SET points_channel = EXCLUDED.points_channel"
        else: # sqlite
            query = "INSERT OR REPLACE INTO config (guild_id, points_channel) VALUES (?, ?)"
        
        c.execute(query, (interaction.guild.id, channel_id))
        db.commit()
        await interaction.response.send_message("✅ تم تحديد روم النقاط بنجاح", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    if not db or not c:
        return await ctx.send("❌ Database not connected.")
    embed = discord.Embed(title="⚙️ Setup Points System", description="اختر الروم الذي سيظهر فيه نظام النقاط", color=0xFFD700)
    view = SetupView(ctx.guild)
    await ctx.send(embed=embed, view=view)

class ControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Check for admin role on every interaction with this view
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🔄 Reset Points", style=discord.ButtonStyle.danger, custom_id="cpanel_reset")
    async def reset_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not db or not c:
            return await interaction.response.send_message("❌ Database not connected.", ephemeral=True)
            
        c.execute("DELETE FROM points")
        db.commit()
        await interaction.response.send_message("✅ تم تصفير جميع النقاط", ephemeral=True)
        await send_log(interaction.guild, "🔄 Reset", f"{interaction.user.mention} قام بتصفير جميع النقاط", 0xFF0000)

    @discord.ui.button(label="📊 My Points", style=discord.ButtonStyle.secondary, custom_id="cpanel_mypoints")
    async def my_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"⭐ نقاطك: {get_points(interaction.user.id)}", ephemeral=True)

@bot.command()
async def panel(ctx):
    if not is_admin(ctx.author):
        return await ctx.send("❌ ما عندك صلاحية")
    embed = discord.Embed(title="🛠 Control Panel", color=0xFFD700)
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
                        else: # sqlite
                            c.execute("INSERT OR REPLACE INTO salaries VALUES (?,?)", (member.id, now))
                        db.commit()
                        
                        await send_log(guild, "💰 Salary", f"{member.mention} استلم راتب {amount} نقطة", 0x00FF00)
                        await check_auto_roles(member)
                    break # Process only the highest salary role

@tasks.loop(seconds=TOP_BROADCAST_INTERVAL)
async def auto_top_loop():
    if not db or not c: return
    
    for guild in bot.guilds:
        query = "SELECT points_channel FROM config WHERE guild_id = %s" if DB_TYPE == "postgres" else "SELECT points_channel FROM config WHERE guild_id = ?"
        c.execute(query, (guild.id,))
        r = c.fetchone()
        if not r: continue
        
        channel = guild.get_channel(r["points_channel"])
        if not channel: continue

        c.execute("SELECT user_id, points FROM points ORDER BY points DESC LIMIT 5")
        rows = c.fetchall()
        if not rows: continue

        desc = ""
        for i, row in enumerate(rows, start=1):
            member = guild.get_member(row['user_id'])
            name = member.mention if member else f"<@{row['user_id']}>"
            desc += f"**#{i}** {name} — `{row['points']}` نقطة\n"

        embed = discord.Embed(title="🏆 أعلى النقاط", description=desc, color=0xFFD700)
        
        try:
            await channel.send(embed=embed)
        except discord.errors.Forbidden:
            logging.warning(f"Missing permissions to send message in {channel.name} in {guild.name}")
        except Exception as e:
            logging.error(f"Error in auto_top_loop: {e}")

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
