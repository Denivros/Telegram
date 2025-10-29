# 🚀 Quick Reference Card

## One-Command Update

```bash
cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-monitor
./update-monitor.sh
```

## Essential Commands

```bash
# Check if running
ssh root@31.97.183.241 'docker ps | grep telegram'

# View live logs
ssh root@31.97.183.241 'docker logs telegram-monitor -f'

# Restart monitor
ssh root@31.97.183.241 'docker restart telegram-monitor'

# Stop monitor
ssh root@31.97.183.241 'docker stop telegram-monitor'
```

## VPS Info

- **IP:** 31.97.183.241
- **User:** root
- **Container:** telegram-monitor
- **Files:** ~/telegram-monitor/

## What to Update

- ✅ **Script changes:** `telegram_monitor.py`
- ✅ **Config changes:** `.env` file
- ✅ **New packages:** `requirements.txt`

## Files Included in Updates

- `telegram_monitor.py` (main script)
- `.env` (configuration)
- `requirements.txt` (dependencies)
- `telegram_monitor.session` (auth)
- `Dockerfile` (container config)
- `setup_session.py` (utility)
