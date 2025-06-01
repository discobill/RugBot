import os
import random
import sqlite3
from flask import Flask, session, redirect, url_for, request, render_template_string
import discord
from discord.ext import commands
from discord import app_commands
import threading
import requests

# --- ENV CONFIG ---
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
FLASK_SECRET = os.getenv("FLASK_SECRET")
PORT = int(os.getenv("PORT"))

# --- DISCORD BOT SETUP (HYBRID) ---
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")

# --- DATABASE SETUP ---
def get_db():
    conn = sqlite3.connect("rugplay.db")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rugplay_cookies (
            guild_id TEXT PRIMARY KEY,
            cookie TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    return conn

# --- SLASH COMMAND: /claim ---
@bot.tree.command(name="claim", description="Claim a Rugplay coin to a username.")
@app_commands.describe(username="Rugplay username", coin="Coin symbol")
async def claim(interaction: discord.Interaction, username: str, coin: str):
    guild_id = str(interaction.guild.id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT cookie FROM rugplay_cookies WHERE guild_id = ?", (guild_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        await interaction.response.send_message("No Rugplay cookie registered for this server. Ask the server owner to register.", ephemeral=True)
        return

    cookie = row[0]
    amount = random.randint(5, 500)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Cookie": cookie,
    }
    body = {
        "recipientUsername": username,
        "type": "COIN",
        "amount": amount,
        "coinSymbol": coin.upper()
    }

    response = requests.post("https://rugplay.com/api/transfer", headers=headers, json=body)

    if response.status_code == 404 or "Recipient not found" in response.text:
        await interaction.response.send_message(f"User **{username}** not found on Rugplay.", ephemeral=True)
    elif response.status_code == 200:
        await interaction.response.send_message(f"✅ Sent **{amount} {coin.upper()}** to **{username}**!")
    else:
        await interaction.response.send_message(
            f"❌ Failed to send coin: `{response.status_code}`\n{response.text}",
            ephemeral=True
        )

# --- SLASH COMMAND: /register_cookie ---
@bot.tree.command(name="register_cookie", description="Register Rugplay session cookie (server owner only)")
@app_commands.describe(cookie="Your Rugplay session cookie")
async def register_cookie(interaction: discord.Interaction, cookie: str):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Only the server owner can register the cookie.", ephemeral=True)
        return

    conn = get_db()
    cur = conn.cursor()
    cur.execute("REPLACE INTO rugplay_cookies (guild_id, cookie) VALUES (?, ?)", (str(interaction.guild.id), cookie))
    conn.commit()
    conn.close()

    await interaction.response.send_message("✅ Cookie registered successfully!", ephemeral=True)

# --- FLASK ADMIN DASHBOARD ---
app = Flask(__name__)
app.secret_key = FLASK_SECRET

LOGIN_TEMPLATE = """
<!DOCTYPE html><html><head><title>Login</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body class="bg-dark text-light"><div class="container mt-5"><h2>Admin Login</h2>
{% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
<form method="POST">
  <input type="password" class="form-control mb-3" name="token" placeholder="Enter Admin Token" required>
  <button class="btn btn-primary">Login</button>
</form></div></body></html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html><html><head><title>Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body><div class="container mt-5">
  <div class="d-flex justify-content-between">
    <h2>Rugplay Guilds</h2><a href="{{ url_for('logout') }}" class="btn btn-outline-danger">Logout</a>
  </div>
  <table class="table table-bordered mt-3">
    <thead><tr><th>Guild ID</th><th>Registered At</th><th>Actions</th></tr></thead><tbody>
      {% for row in rows %}
      <tr>
        <td>{{ row[0] }}</td>
        <td>{{ row[1] }}</td>
        <td>
          <form method="POST"><input type="hidden" name="clear_guild" value="{{ row[0] }}">
            <button class="btn btn-sm btn-danger">Clear</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div></body></html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["token"] == ADMIN_TOKEN:
            session["authed"] = True
            return redirect("/dashboard")
        return render_template_string(LOGIN_TEMPLATE, error="Invalid token")
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("authed"): return redirect("/")
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        gid = request.form.get("clear_guild")
        if gid:
            cur.execute("DELETE FROM rugplay_cookies WHERE guild_id = ?", (gid,))
            conn.commit()
    cur.execute("SELECT guild_id, registered_at FROM rugplay_cookies")
    rows = cur.fetchall()
    return render_template_string(DASHBOARD_TEMPLATE, rows=rows)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# --- RUN BOT + WEB ---
def run_web(): app.run(host="0.0.0.0", port=PORT)
def run_bot(): bot.run(BOT_TOKEN)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()
