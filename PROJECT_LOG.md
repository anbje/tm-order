#  11.  VM USER STANDARDIZATION (MANDATORY)
| Step | Command |
|---|---|
| Remove unused user dirs | `sudo bash /home/anton_bjerke/standardize_vm.sh` |
| Ensure all files owned by main user | Script sets ownership to `anton_bjerke` |
| All SSH, git, Docker, and file ops | Use only `anton_bjerke` user |
| Project location | `/home/anton_bjerke/tm_order` |

> The script `/home/anton_bjerke/standardize_vm.sh` automates cleanup and ownership. Run after any user confusion or migration.

```<!--  TM-ORDER  –  PRODUCTION-HANDOVER GUIDE  -->
<!--  Save as PROJECT_LOG.md in the root of your VS-Code workspace -->
<!--  Purpose: let GitHub Copilot / future-you know what is **LIVE**, what is **LOCAL**, and what must **NEVER** be touched.  -->

#  0.  GOLDEN RULES (read first, forget later)
| Rule | Why |
|---|---|
| 1. **VM = SINGLE SOURCE OF TRUTH** | DB lives there.  Web / bot traffic hits it.  Never overwrite VM with untested code. |
| 2. **LOCAL = SANDBOX ONLY** | Feel free to break anything; nothing leaves this folder until you **explicitly** push / upload. |
| 3. **NEVER COMMIT `.env` TOKENS** | `.env` is in `.gitignore`; tokens are **unique per machine**. |
| 4. **DOCKER-COMPOSE FILE MATRIX** | `docker-compose.yml` → local dev<br>`docker-compose.prod.yml` → VM only<br>Do **not** rename or merge them. |
| 5. **ONE COMMAND DEPLOY** | `docker compose down && docker compose up -d` (inside VM) is the **only** way to go live. |

---

#  1.  WHAT WE ALREADY FINISHED (✅ live in production)
| Step | Evidence | Command to verify |
|---|---|---|
| 1.1 | Google Cloud **Always-Free e2-micro** VM created | `gcloud compute instances list` → status `RUNNING` |
| 1.2 | **Static external IP** reserved & attached | `gcloud compute addresses list` → `tm-order-ip` |
| 1.3 | Firewall ports **80, 443, 8443** open | `gcloud compute firewall-rules list` → `allow-web` |
| 1.4 | Docker + Docker-Compose **installed on VM** | `docker --version` inside VM |
| 1.5 | Project folder **uploaded to VM** | `ls ~/tm_order` inside VM |
| 1.6 | **Containers running** (Caddy, Postgres, API, Bot) | `docker ps` → 4 rows |
| 1.7 | **HTTPS certificate** auto-issued by Caddy | Browse `https://<external-ip>` → padlock |
| 1.8 | **Telegram webhook** set | `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo` → URL points to VM |
| 1.9 | **Systemd service** enabled for reboot survival | `systemctl status tm-order` → active |
| 1.10 | **Calendar feed** reachable | `curl https://<external-ip>/calendar/ics?token=SECRET` → `.ics` file |

---

#  2.  DIRECTORY / FILE MAP
```
LOCAL  (VS-Code workspace)          REMOTE  (VM path)
├─ .env                              ├─ ~/tm_order/.env   (independent copy)
├─ docker-compose.yml               ├─ docker-compose.prod.yml
├─ bot/                             ├─ bot/
├─ web/                             ├─ web/
├─ api/                             ├─ api/
└─ db/                              └─ postgres-data  (docker volume)
```

---

#  3.  DAILY WORKFLOW (no code changes)
| Actor | Action |
|---|---|
| You | Use browser → `https://<external-ip>` → add / edit orders. |
| Bot | Sends 24 h deadline reminders automatically. |
| Caddy | Renews Lets-Encrypt cert forever. |
| You | **Nothing to do.** |

---

#  4.  NORMAL DEVELOPMENT CYCLE (changing code)
##  4.1  Local iteration
```
# 1. edit / debug in VS-Code
# 2. test locally
docker compose down
docker compose up -d
# 3. when happy → commit
git add .
git commit -m "feat: blah"
git push origin main        (or create PR)
```

##  4.2  Deploy to production
**Option A – GitHub (preferred)**
```
# inside VM (SSH window)
cd ~/tm_order
git pull origin main
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build   # rebuilds images
```

**Option B – ZIP (no git)**
```
# laptop:  zip the workspace folder
# CloudShell ⋮ → Upload zip
gcloud compute scp --zone=us-central1-a tm_order.zip tm-order-bot:~/
# inside VM
unzip -o tm_order.zip
cd tm_order
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

---

#  5.  ENVIRONMENT VARIABLE MATRIX
| Variable | Local value | VM value | Sync needed? |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | your local test bot | **SAME production bot** | YES – keep identical |
| `SECRET_CALENDAR_TOKEN` | `localtest` | strong random string | NO – different is OK |
| `POSTGRES_PASSWORD` | `devpass` | strong random string | NO – different is OK |

>  ⚠️  Never commit the real values; store them in VS-Code `.env` **and** in VM `.env` only.

---

#  6.  COMMANDS CHEAT-SHEET (copy-ready)
```
# --------------  LOCAL – VS-CODE TERMINAL  --------------
docker compose logs -f bot          # watch local logs
docker compose exec db psql -U postgres -d tmorder   # local SQL shell
pre-commit run --all-files          # if you installed pre-commit hooks

# --------------  REMOTE – SSH WINDOW  --------------
docker ps                           # quick health
docker logs -f bot                  # live bot log
docker compose exec db psql -U postgres -d tmorder   # prod SQL shell
docker system prune -af             # free disk after many rebuilds
sudo reboot                         # safe reboot (systemd auto-starts stack)
```

---

#  7.  WHAT **MUST** NEVER BE DONE
| Don’t | Reason |
|---|---|
| `docker compose up` locally **while pointing to VM Postgres** | Will mismatch schema / kill prod |
| Run **two e2-micro VMs** in same project | 744 h quota → billable |
| Commit `.env` with real tokens | Public repo = instant bot hijack |
| Manually edit files **inside VM** without Git/zip copy | No audit trail, easy to lose changes |
| Delete static IP **while VM is running** | Becomes unattached → $7.50/mo charge |
| Use **Balanced/SSD disk** > 30 GB | Leaves free tier → ~$4-10/mo |
| Enable **Cloud NAT, Load Balancer, GPU** | All billable |
| Change region to `europe-west1`, `asia-…` | e2-micro no longer free |

---

#  8.  DISASTER RECOVERY (if VM dies)
1. Create new e2-micro in `us-central1` (same steps as day-1).  
2. Restore last **git commit** or re-upload zip.  
3. Copy `.env` from local backup.  
4. `docker compose -f docker-compose.prod.yml up -d`.  
5. Re-set webhook:  
   ```
   curl -F "url=https://<new-ip>/bot" https://api.telegram.org/bot<TOKEN>/setWebhook
   ```

---

#  9.  OPTIONAL QUALITY-OF-LIFE (VS-Code)
| Extension | Purpose |
|---|---|
| Docker | GUI container control |
| Remote-SSH | Edit code directly on VM (no upload loop) |
| GitLens | clear history |
| Thunder Client / Postman | test API endpoints |

---

#  10.  SUMMARY FOR COPILOT SNIPPETS
```
// .vscode/copilot-instructions.md
// Paste the lines below into GitHub Copilot chat when you need context
Project: tm-order (Telegram mini-app workflow bot)
Production VM: tm-order-bot @ us-central1-a  (external IP static, free tier)
Deploy command (VM):  docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d --build
Local test command:   docker compose up -d
Never commit:         .env  (contains TELEGRAM_BOT_TOKEN)
Database volume:      postgres_data  (docker volume, lives only on VM)
HTTPS cert:           auto by Caddy, no action needed
--------------------------------------------------------------------------
``

---

#  11.  GIT LARGE FILE INCIDENT & PRODUCTION PIPELINE LESSONS (2025-10-17)
| Issue | Resolution | Key Lessons |
|---|---|---|
| Accidental commit of large binaries (Google Cloud SDK, >100MB) caused git push failures and repo bloat | Used BFG Repo-Cleaner to purge all large files from git history, updated .gitignore, and force-pushed to GitHub | Never commit SDKs or binaries; always check repo size before pushing; .gitignore must include all non-source assets |
| Production deployment failed to update web UI after code changes | Ensured VM pulled latest code, rebuilt Docker containers with --no-cache, and restarted services | Always verify commit hash on VM matches local; use --no-cache for Docker builds to avoid stale assets |
| Caddy/SSL issues (ERR_SSL_PROTOCOL_ERROR) after redeploy | Checked Caddy logs, confirmed certificate issuance, verified ports 80/443 open, cleared browser cache | Caddy logs are authoritative for SSL issues; browser cache and DNS can mask real status |
| Docker Compose errors (ContainerConfig) after image cleanup | Ran docker-compose down --volumes, pruned system, rebuilt all images | Full cleanup and rebuild may be required after major image or volume changes |

> Documented by Copilot: This section summarizes a critical production recovery, git hygiene, and deployment troubleshooting workflow. Review before future major upgrades or if similar symptoms recur.
