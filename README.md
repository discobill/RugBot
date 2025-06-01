# 🤖 Rugplay Discord Bot

A powerful and simple Discord bot that lets server owners send Rugplay coins to users via `/claim`. Comes with a modern web dashboard to manage server cookies and bot access.

---

## 📦 Features

- `/claim <username> <coin>` — Sends 5–500 coins to a Rugplay user using the registered session cookie.
- `/register_cookie <cookie>` — Lets the **server owner** register their Rugplay session cookie.
- 🧠 Caches usernames and handles invalid recipients.
- 🌐 Web-based admin dashboard (Flask) to view & manage cookie registrations.
- 🔐 Secure admin login using an environment-based password (ex: `AD_OMNI_L7Q8MX`).
- 📁 SQLite backend for storing cookies.

---

## 📋 Commands

| Command | Description |
|--------|-------------|
| `/claim <username> <coin>` | Send a random amount of coins (5–500) to a Rugplay username. |
| `/register_cookie <cookie>` | Register a Rugplay session cookie (server owner only). |

---

## 🚀 Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/discobill/RugBot.git
cd RugBot
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables
### Create a .env file (or set these in Railway/Replit/Render):

```env
DISCORD_TOKEN="your_discord_bot_token"
ADMIN_TOKEN="AD_OMNI_L7Q8MX" or you can set this to literally anything idc
BOT_OWNER_ID="your_discord_user_id"  # Used for showing this in the dashboard if needed
FLASK_SECRET="your_flask_secret_key"
PORT=8080
```

### Generate a Flask secret with:

```python
import secrets
print(secrets.token_hex(32))
```

### Generate an admin token like:

```python
import random, string
print("AD_OMNI_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
```

---

## 🧪 Running Locally

```bash
python main.py
```

* Flask dashboard will run at http://localhost:8080
* Discord bot will connect and be ready

## 🌐 Self-Hosting Options

---

## ✅ Railway (Recommended)

1. Push this repo to GitHub

2. Go to https://railway.app

3. Click "New Project" > "Deploy from GitHub"

4. Select your repo

5. Add your environment variables under the Variables tab

6. Set start command to: 
```bash
 python main.py
```

✅ Done! Dashboard and bot will run 24/7.

---

## 🟡 Replit

1. Create a new Python Repl

2. Upload your files or paste them into main.py

3. Add the environment variables using Replit Secrets

4. Use flask run or python main.py

5. Use UptimeRobot to keep it awake (for free)

--- 

## ⚙️ Manual (e.g., VPS)

Just follow the install instructions and run with:
```bash
python main.py
```

Use `tmux` or `pm2` to keep it running in the background.

---

## 📸 Admin Dashboard

* Visit http://localhost:8080 (or your hosted URL)

* Log in with your ADMIN_TOKEN

* View & clear registered guild cookies

---

## 🤝 Contributing

Pull requests are welcome! Please follow the existing format and comment your code where necessary.

--- 

## 🧠 Credits

* Created by discobill and ChatGPT

* Powered by Discord.py, Flask, SQLite

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---