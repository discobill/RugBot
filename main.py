import os
import random
import sqlite3
from flask import Flask, session, redirect, request, render_template_string
import discord
from discord.ext import commands
import threading
import requests

# --- ENV CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
FLASK_SECRET = os.getenv("FLASK_SECRET")
PORT = int(os.getenv("PORT"))
DEFAULT_COOKIE = os.getenv("DEFAULT_RUGPLAY_COOKIE")

# --- DISCORD BOT SETUP ---
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True
intents.message_content = True  # important for hybrid commands
bot = commands.Bot(command_prefix='/', intents=intents)

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

# --- COMMAND: /claim ---
@bot.hybrid_command(name="claim", description="Claim a Rugplay coin to a username.")
async def claim(ctx, username: str, coin: str):
    guild_id = str(ctx.guild.id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT cookie FROM rugplay_cookies WHERE guild_id = ?", (guild_id,))
    row = cur.fetchone()
    conn.close()

    cookie = row[0] if row else DEFAULT_COOKIE

    if not cookie:
        await ctx.send("❌ No Rugplay cookie available. Please register one using `/register_cookie`.", ephemeral=True)
        return

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
        await ctx.send(f"User **{username}** not found on Rugplay.", ephemeral=True)
    elif response.status_code == 200:
        await ctx.send(f"✅ Sent **{amount} {coin.upper()}** to **{username}**!")
    else:
        await ctx.send(f"❌ Failed to send coin: `{response.status_code}`\n{response.text}", ephemeral=True)

# --- COMMAND: /register_cookie (server owner only) ---
@bot.hybrid_command(name="register_cookie", description="Register your Rugplay session cookie (server owner only)")
async def register_cookie(ctx, cookie: str):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Only the server owner can register the cookie.", ephemeral=True)
        return

    conn = get_db()
    cur = conn.cursor()
    cur.execute("REPLACE INTO rugplay_cookies (guild_id, cookie) VALUES (?, ?)", (str(ctx.guild.id), cookie))
    conn.commit()
    conn.close()
    await ctx.send("✅ Cookie registered successfully!", ephemeral=True)

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
    <h2>Rugplay Guilds</h2><a href="/logout" class="btn btn-outline-danger">Logout</a>
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
def run_web():
    app.run(host="0.0.0.0", port=PORT)

def run_bot():
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()
