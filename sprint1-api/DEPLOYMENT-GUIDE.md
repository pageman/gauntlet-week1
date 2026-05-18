# Deployment Guide — Task Management REST API

## Current Public Render Deployment

```text
https://gauntlet-week1.onrender.com
```

Verified:

```bash
curl https://gauntlet-week1.onrender.com/health
curl https://gauntlet-week1.onrender.com/api/v1/tasks
curl https://gauntlet-week1.onrender.com/api/v1/tasks/stats
```

This is a Render Free deployment. It may cold-start after inactivity and uses
temporary SQLite storage.

## Quick Deploy to Render.com (Recommended)

### Prerequisites

- GitHub account with repository access
- Render.com account (free tier available)

### Step-by-Step

1. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/task-api.git
   git push -u origin main
   ```

2. **Connect Render.com**
   - Go to https://render.com/dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository
   - Set Root Directory to `sprint1-api`

3. **Configure Deployment**
   - Runtime: Python 3.11
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment: `DATABASE_PATH=/tmp/tasks.db`
   - Health Check Path: `/health`

4. **Deploy**
   - Click "Create Web Service"
   - Render builds and deploys automatically
   - Your API is live at `https://<service-name>.onrender.com`

5. **Test Deployment**
   ```bash
   curl https://<service-name>.onrender.com/health
   curl -X POST https://<service-name>.onrender.com/api/v1/tasks \
     -H "Content-Type: application/json" \
     -d '{"title": "Test task"}'
   ```

---

## Deploy to Railway.app

### Prerequisites

- Railway.com account
- GitHub repository

### Step-by-Step

1. **Create railway.toml**
   ```toml
   [build]
   builder = "dockerfile"

   [deploy]
   startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   healthcheckPath = "/health"
   healthcheckInterval = 30
   ```

2. **Connect Railway**
   - Go to https://railway.app/dashboard
   - Click "New Project"
   - Select "Deploy from GitHub"
   - Choose your repository

3. **Configure Environment**
   - Railway auto-detects Python
   - Sets `PORT` environment variable
   - Use a managed database or documented temporary SQLite storage

4. **Deploy**
   - Click "Deploy"
   - Railway builds and deploys
   - Your API is live at `https://<project>.railway.app`

---

## Deploy to Fly.io

### Prerequisites

- Fly.io account
- Fly CLI installed (`brew install flyctl`)

### Step-by-Step

1. **Create fly.toml**
   ```toml
   app = "task-api"
   primary_region = "sin"

   [build]
     image = "task-api:latest"

   [[services]]
     protocol = "tcp"
     internal_port = 8000
     processes = ["app"]

     [services.concurrency]
       type = "connections"
       hard_limit = 1000
       soft_limit = 800

   [[mounts]]
     source = "task_data"
     destination = "/data"
   ```

2. **Create Volume**
   ```bash
   flyctl volumes create task_data --size 1 --region sin
   ```

3. **Deploy**
   ```bash
   flyctl deploy
   ```

4. **Get URL**
   ```bash
   flyctl info
   ```

---

## Docker Local Deployment

### Build & Run

```bash
# Build image
docker build -t task-api:latest .

# Run container
docker run \
  -p 8000:8000 \
  -e DATABASE_PATH=/data/tasks.db \
  -v task-data:/data \
  task-api:latest

# Test
curl http://localhost:8000/health
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_PATH: /data/tasks.db
    volumes:
      - task-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

volumes:
  task-data:
```

Run with:
```bash
docker-compose up
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `tasks.db` | Path to SQLite database |
| `PORT` | `8000` | Server port |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS allowed origins |

### Production Recommendations

```bash
# Render Free environment variables
DATABASE_PATH=/tmp/tasks.db
ALLOWED_ORIGINS=*
```

---

## Health Checks

All deployment platforms use the health check endpoint:

```bash
GET /health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2026-05-18T01:30:00Z"
}
```

---

## Monitoring

### Logs

**Render.com:**
- Dashboard → Logs tab
- Real-time streaming logs

**Railway.app:**
- Dashboard → Logs tab
- Searchable log history

**Fly.io:**
```bash
flyctl logs
```

### Health Checks

All platforms monitor `/health` endpoint:
- Interval: 30 seconds
- Timeout: 10 seconds
- Failure threshold: 3 consecutive failures

---

## Scaling

### Horizontal Scaling

**Render.com:**
- Paid plans support multiple instances
- Auto-scaling available

**Railway.app:**
- Replica management in dashboard
- Manual scaling

**Fly.io:**
```bash
flyctl scale count=3
```

### Vertical Scaling

**Render.com:**
- Upgrade plan tier

**Railway.app:**
- Increase memory/CPU allocation

**Fly.io:**
```bash
flyctl scale vm=performance-2x
```

---

## Database Persistence

### SQLite Persistence

All platforms use persistent volumes:

**Render.com:**
- Disk: `task-data` mounted at `/data`
- Size: 1 GB
- Auto-backed up

**Railway.app:**
- Persistent volume auto-created
- Data survives restarts

**Fly.io:**
- Volume: `task_data` mounted at `/data`
- Survives deployments

---

## Troubleshooting

### API Not Responding

1. **Check health endpoint:**
   ```bash
   curl https://<your-api>/health
   ```

2. **Check logs:**
   - Render: Dashboard → Logs
   - Railway: Dashboard → Logs
   - Fly: `flyctl logs`

3. **Restart service:**
   - Render: Manual restart in dashboard
   - Railway: Redeploy from dashboard
   - Fly: `flyctl restart`

### Database Issues

1. **Check volume:**
   - Render: Disk settings in dashboard
   - Railway: Volume status
   - Fly: `flyctl volumes list`

2. **Check permissions:**
   - Ensure `/data` directory is writable
   - Check file permissions in logs

3. **Reset database:**
   ```bash
   # Delete and recreate volume
   # WARNING: This deletes all data!
   ```

### High Memory Usage

1. **Check active connections:**
   - Monitor dashboard
   - Check concurrent requests in logs

2. **Optimize queries:**
   - Add database indexes
   - Implement caching

3. **Scale vertically:**
   - Increase memory allocation

---

## Backup Strategy

### Manual Backup

```bash
# Download database from Render
# Via dashboard or SFTP

# Backup to local file
cp /data/tasks.db tasks.db.backup
```

### Automated Backup

**Recommendation:** Implement daily backups to S3

```python
# Future: Backup script
import boto3
import shutil

def backup_database():
    shutil.copy('/data/tasks.db', 'tasks.db.backup')
    s3 = boto3.client('s3')
    s3.upload_file('tasks.db.backup', 'my-bucket', f'backups/tasks-{date}.db')
```

---

## Security Checklist

- [ ] HTTPS enabled (automatic on all platforms)
- [ ] Database encrypted at rest (check platform settings)
- [ ] Environment variables not exposed in logs
- [ ] Health check endpoint accessible
- [ ] CORS properly configured
- [ ] No sensitive data in error messages
- [ ] Rate limiting configured (future sprint)
- [ ] Authentication enabled (future sprint)

---

## Performance Optimization

### Current Optimizations

- ✅ Async/await for non-blocking I/O
- ✅ Database indexes on filter columns
- ✅ Pagination to limit response size
- ✅ Connection pooling via aiosqlite

### Future Optimizations

- ⏳ Redis caching for frequently accessed data
- ⏳ Query result caching
- ⏳ Gzip compression for responses
- ⏳ CDN for static assets

---

## Cost Estimation

### Render.com

- **Free tier:** 0.5 GB RAM, 0.5 CPU, 1 GB disk
- **Starter:** $7/month (1 GB RAM, 0.5 CPU, 10 GB disk)
- **Standard:** $12/month (2 GB RAM, 1 CPU, 50 GB disk)

### Railway.app

- **Pay as you go:** ~$5/month for small API
- **Includes:** 5 GB storage, 100 GB bandwidth

### Fly.io

- **Shared CPU:** $0.0000011/second (~$3/month)
- **Dedicated CPU:** $0.0000037/second (~$10/month)

---

## Next Steps

1. **Deploy to Render.com** (recommended for MVP)
2. **Monitor health checks** and logs
3. **Test all endpoints** in production
4. **Set up backup strategy** (future sprint)
5. **Plan for scaling** as usage grows

---

## Support

For deployment issues:
- Render: https://render.com/docs
- Railway: https://railway.app/docs
- Fly: https://fly.io/docs

For API issues:
- See README.md for usage examples
- See SPEC.md for endpoint documentation
- See PEER-REVIEW-NOTES.md for architecture details
