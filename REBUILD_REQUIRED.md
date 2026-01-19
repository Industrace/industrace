# 🔧 Rebuild Required After Code Changes

After modifying Python files in the backend, you **MUST rebuild the Docker images** for changes to take effect.

## Quick Rebuild

```bash
# Stop containers
make stop

# Rebuild only backend (faster)
docker-compose -f docker-compose.prod.yml build backend

# Start again
make prod
```

## Full Rebuild (if issues persist)

```bash
# Stop and clean
make stop

# Rebuild everything
docker-compose -f docker-compose.prod.yml build --no-cache

# Start again
make prod
```

## Why?

Docker containers run from **images**, not directly from your code. When you edit Python files:
1. The files on your computer change ✅
2. But the Docker image still has the old code ❌
3. You need to rebuild the image to include your changes

## Files that require rebuild:

- Any `.py` file in `backend/`
- `requirements.txt`
- `Dockerfile` or `Dockerfile.dev`
- Configuration files

## Files that DON'T require rebuild:

- Documentation (`.md` files)
- Frontend files (they use volume mounts in dev mode)
