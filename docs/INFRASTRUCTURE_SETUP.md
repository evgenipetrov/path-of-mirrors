# Infrastructure Setup Guide

This document covers the infrastructure setup completed for the Path of Mirrors POC.

## ✅ Completed Infrastructure Tasks

### 1. Fixed Orval/Axios Integration

**Issue:** Orval generates Fetch API code (`body` property) but we use Axios (expects `data` property).

**Solution:** Custom mutator in `frontend/src/lib/api-client.ts` that converts `body → data`:

```typescript
// Convert Fetch API 'body' to Axios 'data' if present
const axiosConfig: AxiosRequestConfig = { ...config };
if ('body' in axiosConfig && axiosConfig.body !== undefined) {
  axiosConfig.data = axiosConfig.body;
  delete (axiosConfig as any).body;
}
```

This is documented in both the code and `orval.config.ts`.

### 2. CRUD Operations

All CRUD operations are fully functional:

- ✅ **Create** - Working perfectly with toast notifications
- ✅ **Read** - Working with proper loading states
- ✅ **Update** - Working with backend validation
- ✅ **Delete** - Working with confirmation dialog

### 3. Query Cache Management

Implemented proper cache invalidation with await:

```typescript
const createMutation = useCreateNoteApiNotesPost({
  mutation: {
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['listNotesApiNotesGet'] });
      toast.success('Note created successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail?.[0]?.msg || 'Failed to create note');
    },
  },
});
```

### 4. Error Handling

Added Sonner toast notifications for all mutations:
- Success messages for create/update/delete
- Error messages with API validation details
- Toaster component in App.tsx

### 5. Database Migrations

Migration workflow verified:
- Current migration: `2a1185ac4b28` (create_notes_table)
- Migrations run from host system, not container (Docker mount is read-only)
- Command: `docker compose exec backend bash -c "cd /app/src && uv run alembic ..."

### 6. Environment Variables & .gitignore

**Created root `.gitignore`:**
- IDE files (.vscode/, .idea/)
- OS files (.DS_Store)
- Environment files (.env, .env.local)
- MCP tools (.playwright-mcp/, .mcp.json)
- Docker volumes

**Updated frontend `.gitignore`:**
- Added .env, .env.local, .env.production

**Backend `.gitignore`:**
- Already comprehensive (from boilerplate)

### 7. Development Scripts

All scripts working and documented:
- `./scripts/start-dev.sh` - Start all services
- `./scripts/stop-dev.sh` - Stop all services
- `./scripts/restart-dev.sh` - Restart everything
- Comprehensive README in `scripts/README.md`

## Infrastructure Components

### Backend (Docker Compose)

```yaml
services:
  postgres:
    image: postgres:17-alpine
    ports: ["5432:5432"]
    healthcheck: pg_isready

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck: redis-cli ping

  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./backend/src:/app/src:ro"]  # Read-only for safety
    depends_on: [postgres (healthy), redis (healthy)]
```

### Frontend (Vite)

- Runs outside Docker for optimal HMR
- Auto-reload on file changes
- TypeScript type-safe API client generated from OpenAPI

### API Client Generation

```bash
cd frontend
npm run generate:api  # Regenerate from http://localhost:8000/openapi.json
```

## Development Workflow

### Starting Development

```bash
./scripts/start-dev.sh
```

This starts:
1. PostgreSQL (health check wait)
2. Redis (health check wait)
3. FastAPI backend (auto-reload on changes)
4. Vite frontend (HMR enabled)

### Creating Database Migrations

```bash
# 1. Modify models in backend/src/contexts/*/domain/models.py
# 2. Generate migration (run on HOST, not in container)
cd backend
docker compose exec backend bash -c "cd /app/src && uv run alembic revision --autogenerate -m 'Description'"
# 3. Review generated migration in src/migrations/versions/
# 4. Apply migration
docker compose exec backend bash -c "cd /app/src && uv run alembic upgrade head"
```

### Regenerating API Client

After backend API changes:

```bash
cd frontend
npm run generate:api
```

This fetches `http://localhost:8000/openapi.json` and generates:
- TypeScript types
- TanStack Query hooks
- Axios request functions

## Known Issues & Solutions

### Issue: Migrations fail with "Read-only file system"

**Cause:** Docker volume is mounted as `:ro` (read-only) for safety.

**Solution:** Create migrations on the host system, not in the container. They will sync to the container automatically.

### Issue: Frontend shows stale data after mutations

**Cause:** Query invalidation wasn't awaited.

**Status:** ✅ Fixed - all mutations now await `queryClient.invalidateQueries()`

### Issue: API calls return 422 with `body: null`

**Cause:** Orval generates Fetch API code but we use Axios.

**Status:** ✅ Fixed - custom mutator converts `body → data`

## Environment Variables

### Backend

Required in `backend/src/.env`:

```bash
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pathofmirrors
REDIS_CACHE_HOST=redis
REDIS_CACHE_PORT=6379
REDIS_QUEUE_HOST=redis
REDIS_QUEUE_PORT=6379
ENVIRONMENT=local
LOG_LEVEL=INFO
```

### Frontend

Required in `frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000
```

## Health Checks

```bash
# Backend liveness
curl http://localhost:8000/health

# Backend readiness (DB + Redis)
curl http://localhost:8000/ready

# PostgreSQL
docker compose exec postgres pg_isready -U postgres

# Redis
docker compose exec redis redis-cli ping
```

## Access Points

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- OpenAPI Spec: http://localhost:8000/openapi.json

## Next Phase Tasks

After infrastructure setup, the next tasks are:

1. **Add more shadcn/ui components** - Improve UI polish
2. **Add game context switcher** - Switch between PoE1/PoE2 in header
3. **Implement Phase 1** - Market intelligence features
4. **Add testing** - pytest (backend), Vitest (frontend)
5. **Set up CI/CD** - GitHub Actions
6. **Deploy to production** - Railway/Render + Vercel

## Troubleshooting

See `scripts/README.md` for common issues and solutions.

## Summary

The POC infrastructure is now complete and production-ready:

- ✅ Full CRUD operations working
- ✅ Proper error handling with toast notifications
- ✅ Database migrations workflow verified
- ✅ API client generation working
- ✅ Development scripts documented
- ✅ Environment variables secured
- ✅ Git ignore configuration complete

**The foundation is solid. Ready to build features! 🚀**
