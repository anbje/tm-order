# TM-Order Setup Guide

## ✅ **Current Status**

Docker containers are running:
- ✅ `db` (Postgres) - running
- ✅ `api` (FastAPI) - running
- ✅ `web` (Quasar PWA) - running
- ✅ `caddy` (reverse proxy) - running
- ❌ `bot` (Telegram) - needs valid token

---

## 🔧 **Next Steps: Configure Telegram Bot**

### 1. Create a Telegram Bot

Open Telegram on your phone and message **@BotFather**:

```
/newbot
```

Follow the prompts:
- **Name**: TM Order (or any name you like)
- **Username**: Must end in "bot", e.g., `your_tmorder_bot`

BotFather will respond with a token like:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. Update `.env` File

Edit `/home/av/RAMA/tm_order/.env`:

```bash
# Replace the placeholder token with your real token from BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Change this to a random secret for calendar feed security
SECRET_CALENDAR_TOKEN=your_random_secret_here_change_me

# Database config (leave as-is for now)
DB_HOST=db
DB_PORT=5432
DB_NAME=tmorder
DB_USER=tmorder
DB_PASSWORD=tmorder_secret_123

# API config (leave as-is)
API_URL=http://api:8000
```

### 3. Restart the Bot Container

```bash
cd /home/av/RAMA/tm_order
sudo docker-compose restart bot
```

### 4. Check Bot Status

```bash
sudo docker-compose logs -f bot
```

You should see: `Bot started` and `Webhook set to...` (or polling started).

---

## 🌐 **Access the Web UI**

1. Open browser: **https://localhost**
2. Accept the self-signed certificate warning
3. You should see the TM-Order interface

---

## 📱 **Test the Telegram Mini-App**

1. Start a chat with your bot in Telegram
2. You should see a "+ New Order" button
3. Tap it to open the mini-app
4. Fill in the order details and save
5. Check the web UI — the order should appear instantly

---

## 📅 **Calendar Feed**

Subscribe to your calendar feed:

```
https://localhost/calendar/ics?token=your_random_secret_here_change_me
```

Add this URL to:
- Thunderbird (File → New Calendar → On the Network)
- Google Calendar (Other calendars → From URL)
- Apple Calendar (File → New Calendar Subscription)

All deadlines will appear as all-day events.

---

## 🐛 **Troubleshooting**

### Check Container Status
```bash
cd /home/av/RAMA/tm_order
sudo docker-compose ps
```

### View Logs
```bash
sudo docker-compose logs -f api    # FastAPI backend
sudo docker-compose logs -f bot    # Telegram bot
sudo docker-compose logs -f db     # Database
```

### Restart All Containers
```bash
sudo docker-compose restart
```

### Stop All Containers
```bash
sudo docker-compose down
```

### Rebuild and Restart
```bash
sudo docker-compose up -d --build
```

---

## 🔒 **Security Notes**

1. **Never commit `.env` to git** — it contains secrets
2. The current setup uses **self-signed certificates** (OK for local dev)
3. For production deployment:
   - Use a real domain name
   - Configure Let's Encrypt for HTTPS
   - Change all default passwords
   - Move to a VPS with proper firewall rules

---

## 📝 **What's Next?**

Once the bot is working:

1. **Test order creation** (Telegram → Web UI)
2. **Test file upload** (check if #17 is fixed)
3. **Test customer search** (check if #19 is fixed)
4. **Configure invoice template** (Jinja2 + WeasyPrint)
5. **Test deadline reminders** (manually set deadline to < 24h)

---

## 💡 **Quick Reference**

| Service | URL | Credentials |
|---------|-----|-------------|
| Web UI | https://localhost | - |
| API Docs | https://localhost/api/docs | - |
| Postgres | localhost:5432 | `tmorder` / `tmorder_secret_123` |
| Calendar | https://localhost/calendar/ics?token=SECRET | - |

---

**Last Updated**: 2025-10-15
