# Development Scripts

Convenient scripts for managing the Path of Mirrors development environment.

## Available Scripts

### `dev.sh` - Start All Services

Starts the complete development stack with one command.

```bash
./scripts/dev.sh
```

**What it does:**
1. Starts Docker services (PostgreSQL, Redis, Backend API)
2. Waits for health checks to pass (database + cache)
3. Checks/installs frontend dependencies if needed
4. Starts Vite frontend dev server with HMR
5. Displays unified status and logs
6. Handles graceful shutdown on Ctrl+C

**Services started:**
- PostgreSQL 17 (port 5432)
- Redis 7 (port 6379)
- FastAPI Backend (port 8000)
- Vite Frontend (port 5173)

**Press Ctrl+C to stop all services cleanly**

---

### `stop.sh` - Stop All Services

Stops all running services (Docker + frontend).

```bash
./scripts/stop.sh
```

**What it does:**
1. Stops Docker Compose services
2. Kills any remaining frontend processes
3. Cleans up background processes

---

### `restart.sh` - Restart All Services

Convenience script to stop and restart everything.

```bash
./scripts/restart.sh
```

**What it does:**
1. Runs `stop.sh` to stop all services
2. Waits 2 seconds
3. Runs `dev.sh` to start everything fresh

---

## Usage Examples

### Daily Development

```bash
# Morning: start everything
./scripts/dev.sh

# Work on features...
# Frontend changes auto-reload via HMR
# Backend changes auto-reload via Docker watch

# Evening: stop everything
# Press Ctrl+C (or run ./scripts/stop.sh)
```

### Troubleshooting

```bash
# If something is stuck, restart everything
./scripts/restart.sh

# If you need to clear the database
docker compose down -v
./scripts/dev.sh
```

### Quick Testing

```bash
# Start everything
./scripts/dev.sh

# In another terminal: test the API
curl http://localhost:8000/health
curl http://localhost:8000/api/notes

# Open browser: http://localhost:5173/notes

# Stop when done
./scripts/stop.sh
```

---

## Architecture Notes

**Why frontend is separate from Docker:**

The frontend runs outside Docker Compose for optimal HMR performance:
- ✅ Sub-second hot reload
- ✅ No Docker volume overhead
- ✅ Direct file system access
- ✅ Simpler node_modules handling

Backend services run in Docker for:
- ✅ Consistent environment (PostgreSQL, Redis)
- ✅ Easy database management
- ✅ Production-like setup
- ✅ Isolated dependencies

This hybrid approach gives the best developer experience while maintaining environment consistency where it matters.

---

## Requirements

- Docker & Docker Compose
- Node.js 18+
- Bash shell
- Ports available: 5432, 6379, 8000, 5173

---

## Troubleshooting

**Script won't run:**
```bash
# Make sure it's executable
chmod +x scripts/*.sh
```

**Port conflicts:**
```bash
# Find what's using a port
lsof -i :8000
lsof -i :5173

# Kill the process or change port in config
```

**Frontend won't start:**
```bash
# Clean install dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
./scripts/dev.sh
```

**Database issues:**
```bash
# Reset database (WARNING: deletes all data)
./scripts/stop.sh
docker compose down -v
./scripts/dev.sh

# Run migrations
docker compose exec backend uv run alembic upgrade head
```
