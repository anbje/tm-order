# TM-Order: Translation Management System

Minimal freelance translation business management: orders, deadlines, reminders, invoices.

## 🎯 **Features**

- 📱 **Telegram Mini-App**: Create orders from phone (5 seconds)
- 💻 **Web UI**: Manage orders on desktop
- 📅 **Calendar Sync**: iCal feed for Thunderbird/Google Calendar
- ⏰ **Deadline Reminders**: Telegram push 24h before deadline
- 📄 **File Upload**: Store source & target files
- 💰 **Invoice Generation**: Simple PDF generator (coming soon)

## 🏗️ **Architecture**

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Telegram │────▶│  FastAPI │────▶│ Postgres │
│   Bot    │     │   API    │     │    DB    │
└──────────┘     └──────────┘     └──────────┘
                       │
                       ▼
                 ┌──────────┐
                 │  Quasar  │
                 │  Web UI  │
                 └──────────┘
```

**Stack:**
- Backend: FastAPI + SQLAlchemy + Postgres
- Frontend: Quasar (Vue.js) PWA
- Bot: python-telegram-bot
- Proxy: Caddy (auto-HTTPS)
- Deployment: Docker Compose

## 🚀 **Quick Start**

See [`SETUP.md`](./SETUP.md) for detailed instructions.

**TL;DR:**
```bash
cd /home/av/RAMA/tm_order

# 1. Get Telegram bot token from @BotFather
# 2. Edit .env and add your token
# 3. Start containers
sudo docker-compose up -d

# 4. Open https://localhost in browser
# 5. Chat with your bot in Telegram
```

## 📂 **Project Structure**

```
tm_order/
├── docker-compose.yml      # Orchestration
├── .env                    # Secrets (DO NOT COMMIT)
├── api/                    # FastAPI backend
│   ├── Dockerfile
│   ├── main.py            # API routes
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # DB connection
│   └── requirements.txt
├── bot/                    # Telegram bot
│   ├── Dockerfile
│   ├── bot.py             # Bot logic + reminders
│   └── requirements.txt
├── web/                    # Quasar PWA
│   ├── Dockerfile
│   ├── index.html         # Main UI
│   └── nginx.conf
├── Caddyfile              # Reverse proxy config
├── SETUP.md               # Setup instructions
└── README.md              # This file
```

## 🔧 **Configuration**

Edit `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather | (required) |
| `SECRET_CALENDAR_TOKEN` | Calendar feed auth | `change_me` |
| `DB_NAME` | Postgres database | `tmorder` |
| `DB_USER` | Postgres user | `tmorder` |
| `DB_PASSWORD` | Postgres password | `tmorder_secret_123` |

## 📋 **Workflow**

### Create Order (Telegram)
1. Open bot chat → "+ New Order"
2. Fill: Customer, Topic, Deadline, Words
3. Save → appears in web UI instantly

### Manage Order (Web)
1. Open https://localhost
2. Click row → edit details
3. Upload files (source/target)
4. Mark as delivered

### Calendar Sync
1. Subscribe to `https://localhost/calendar/ics?token=SECRET`
2. All deadlines appear as all-day events
3. Auto-syncs on changes

### Deadline Reminder
- Bot checks every 15 min
- Sends Telegram push if deadline < 24h
- Type `/done` to mark delivered

## 🧪 **Development**

### View Logs
```bash
sudo docker-compose logs -f api
sudo docker-compose logs -f bot
```

### Restart Service
```bash
sudo docker-compose restart api
```

### Rebuild
```bash
sudo docker-compose up -d --build
```

### Database Access
```bash
sudo docker exec -it tm_order_db_1 psql -U tmorder -d tmorder
```

## 🐛 **Known Issues**

- #11: ✅ Fixed (iOS white screen)
- #14: ✅ Fixed (duplicate reminders)
- #17: 🔨 In progress (file upload returns 501)
- #19: 🔨 In progress (customer search not implemented)

## 📝 **Roadmap**

### Phase 1: Core Workflow ✅
- [x] Order CRUD (Telegram + Web)
- [x] Deadline reminders
- [x] Calendar feed
- [x] Docker deployment

### Phase 2: File Handling 🔨
- [ ] Fix file upload (#17)
- [ ] Customer autocomplete (#19)
- [ ] Add source/target language fields

### Phase 3: Invoicing
- [ ] Define invoice template
- [ ] Jinja2 + WeasyPrint generator
- [ ] "Generate Invoice" button

### Phase 4: Polish
- [ ] Dark mode toggle
- [ ] Export as CSV
- [ ] Backup/restore

## 🔒 **Security**

⚠️ **Current setup is for LOCAL DEVELOPMENT only.**

For production:
- Change all passwords in `.env`
- Use real domain + Let's Encrypt
- Enable firewall rules
- Regular database backups

## 📄 **License**

MIT (or your preferred license)

---

**Part of RAMA toolbench** | [Main Project](../README.md)

## Features

✅ **Order CRUD** via Telegram mini-app + web UI  
✅ **Deadline reminders** (24h before, via Telegram bot)  
✅ **Calendar feed** (iCal export for Thunderbird/Google Calendar)  
✅ **Docker-based** (5 containers: Caddy, Postgres, FastAPI, Bot, Web UI)

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Telegram account
- Telegram Bot Token (get from @BotFather)

### 2. Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set:
#   TELEGRAM_BOT_TOKEN=<your_token_from_botfather>
#   SECRET_CALENDAR_TOKEN=<random_string>

# Start all services
docker compose up -d

# Check health
docker compose ps
```

### 3. Access

- **Web UI**: https://localhost/app
- **API docs**: https://localhost/api/docs
- **Calendar feed**: https://localhost/calendar/ics?token=SECRET
- **Telegram bot**: Start chat with your bot → `/start`

### 4. Usage

1. **Create Order** (Telegram):
   - Open bot → tap "+ New Order"
   - Fill: customer, source lang, target lang, deadline
   - Save → appears instantly in web UI

2. **View Orders** (Web):
   - https://localhost/app
   - See all orders, sorted by deadline
   - Red text = deadline < 24h

3. **Calendar Integration**:
   - Copy calendar URL: `https://localhost/calendar/ics?token=SECRET`
   - Add to Thunderbird/Google Calendar as "internet calendar"
   - All deadlines sync automatically

4. **Deadline Reminders**:
   - Bot checks every 15 min
   - If deadline < 24h → sends Telegram message
   - Reply `/done` → marks order as delivered

## Architecture

```
┌─────────┐      ┌─────────┐      ┌──────────┐
│ Telegram│◄────►│  Bot    │◄────►│   API    │
│ Mini-App│      │ (Python)│      │ (FastAPI)│
└─────────┘      └─────────┘      └──────────┘
                                        │
┌─────────┐                            │
│ Web UI  │◄───────────────────────────┤
│ (HTML)  │                            │
└─────────┘                            ▼
                                  ┌──────────┐
┌─────────┐                       │ Postgres │
│  Caddy  │                       │    DB    │
│ (Proxy) │                       └──────────┘
└─────────┘
```

## API Endpoints

- `POST /api/orders` - Create order
- `GET /api/orders` - List all orders
- `GET /api/orders/{id}` - Get single order
- `PUT /api/orders/{id}` - Update order
- `GET /calendar/ics?token=SECRET` - iCal feed
- `GET /health` - Health check

## Database Schema

**orders** table:
- id, customer_name, source_lang, target_lang
- word_count, topic, deadline_at
- status (pending/in-progress/delivered)
- reminder_sent (boolean)
- created_at, updated_at

## Development

```bash
# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build

# Stop all services
docker compose down

# Reset database
docker compose down -v
docker compose up -d
```

## Roadmap

- [ ] File upload (source + target documents)
- [ ] Customer autocomplete
- [ ] Invoice PDF generation
- [ ] Production deployment config

## License

MIT - For personal freelance use
