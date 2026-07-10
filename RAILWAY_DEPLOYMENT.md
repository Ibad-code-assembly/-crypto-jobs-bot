# Railway Deployment Guide

Complete guide to deploying the Crypto Jobs Bot to Railway (production).

## Prerequisites

- GitHub account with the repository pushed
- Railway account (free tier available at railway.app)
- GitHub token for authentication
- Telegram bot token and chat ID

## Step 1: Create Railway Project

### 1.1 Sign up / Log in to Railway

```bash
# Go to https://railway.app and sign up with GitHub
# Click "Deploy Now" or create a new project
```

### 1.2 Create Project

1. Click "New Project" button
2. Select "Deploy from GitHub repo"
3. Authorize Railway to access your GitHub account
4. Select the `crypto-jobs-bot` repository
5. Click "Deploy"

## Step 2: Configure Services

Railway will automatically detect and create services. You need to configure two services: **API** and **Web**.

### 2.1 API Service Configuration

**Settings Tab:**

```
Service Name: api
Root Directory: .
Dockerfile: ./Dockerfile
```

**Environment Variables:**

```
BOT_TOKEN=your_telegram_token
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./crypto_jobs_prod.db
ALLOWED_ORIGINS=https://your-domain.railway.app,https://your-web-domain.railway.app
TELEGRAM_CHAT_ID=your_chat_id
```

**Port:**
- Set to `8000`

**Deploy:**
- Click "Deploy" to start the API service

### 2.2 Web Service Configuration

**Settings Tab:**

```
Service Name: web
Root Directory: ./web
Dockerfile: ./web/Dockerfile
```

**Environment Variables:**

```
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://your-api-domain.railway.app/api
NEXT_TELEMETRY_DISABLED=1
```

**Port:**
- Set to `3000`

**Build Command:**
```bash
npm ci && npm run build
```

**Start Command:**
```bash
npm start
```

**Deploy:**
- Click "Deploy" to start the Web service

## Step 3: Get Your Railway URLs

After both services deploy successfully:

1. Go to your Railway project dashboard
2. Click on the `api` service
3. Copy the **public URL** (e.g., `https://crypto-jobs-api-prod.railway.app`)
4. Click on the `web` service
5. Copy the **public URL** (e.g., `https://crypto-jobs-web-prod.railway.app`)

### 3.1 Update Environment Variables

**Update Web Service:**

In the `web` service environment variables, update:

```
NEXT_PUBLIC_API_URL=https://crypto-jobs-api-prod.railway.app/api
```

(Replace with your actual API URL)

**Redeploy Web Service:**

The web service will automatically redeploy with the new environment variable.

## Step 4: Enable CI/CD with GitHub Actions

### 4.1 Set GitHub Secrets

Go to your GitHub repository settings:

1. Settings → Secrets and variables → Actions
2. Add new secrets:

```
RAILWAY_TOKEN=your_railway_api_token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

**How to get RAILWAY_TOKEN:**

1. Go to https://railway.app/account/tokens
2. Click "New Token"
3. Copy the token and add it to GitHub secrets

### 4.2 GitHub Actions Workflow

The `.github/workflows/deploy.yml` file will automatically:

1. Run tests on push to `main`
2. Build Docker images
3. Push to GitHub Container Registry
4. Deploy to Railway
5. Notify Telegram on completion

### 4.3 Deploy on Push

Simply push to `main` branch:

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

GitHub Actions will automatically test, build, and deploy!

## Step 5: Configure Domain (Optional)

### 5.1 Add Custom Domain

1. Go to your Railway project
2. Click on the `web` service
3. Go to "Settings" tab
4. Under "Domains", click "Add Domain"
5. Enter your custom domain (e.g., `jobs.yourdomain.com`)
6. Configure DNS records at your domain provider:

```
CNAME: railway-production.up.railway.app
```

### 5.2 SSL Certificate

Railway automatically provisions SSL certificates (Let's Encrypt). Certificate is renewed automatically.

## Step 6: Monitor & Logs

### 6.1 View Logs

In Railway dashboard:

1. Click on a service (api or web)
2. Go to "Logs" tab
3. See real-time application logs

### 6.2 Monitor Performance

1. Go to service → "Monitoring" tab
2. View:
   - Response time
   - Error rate
   - Request count
   - Memory usage
   - CPU usage

### 6.3 Health Checks

Both services have built-in health checks:

**API:**
```
GET /health
```

**Web:**
```
GET /
```

Railway automatically restarts services if health check fails.

## Step 7: Database Setup (Optional)

### 7.1 PostgreSQL Option

For production, consider PostgreSQL instead of SQLite:

1. In Railway dashboard, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Click "Create"
4. Copy connection string

### 7.2 Update Environment Variables

Update the API service:

```
DATABASE_URL=postgresql://user:password@host:port/crypto_jobs
```

This requires updating your FastAPI configuration to support PostgreSQL.

## Step 8: Scale & Performance

### 8.1 Scale Services

In Railway dashboard:

1. Click on service
2. Go to "Deploy" tab
3. Increase "Replica Count" (for horizontal scaling)
4. Adjust "Memory" and "CPU" limits

### 8.2 Recommended Production Settings

**API Service:**
- Memory: 512 MB
- CPU: 0.5
- Replicas: 2 (for redundancy)

**Web Service:**
- Memory: 256 MB
- CPU: 0.25
- Replicas: 1

## Step 9: Troubleshooting

### Issue: Build fails

**Solution:** Check build logs in Railway dashboard. Common issues:
- Missing environment variables
- Dockerfile syntax errors
- Dependencies not installing

### Issue: API unreachable from Web

**Solution:** Verify `NEXT_PUBLIC_API_URL` environment variable in web service.

### Issue: High memory usage

**Solution:** Increase memory limit in service settings, or optimize code.

### Issue: Slow response times

**Solution:**
1. Increase replica count for load balancing
2. Optimize API queries
3. Enable Redis caching
4. Use CDN for static assets

### Check Service Health

```bash
# Test API
curl https://your-api-url.railway.app/health

# Test Web
curl https://your-web-url.railway.app
```

## Step 10: Maintenance

### 10.1 Automatic Deployments

Every push to `main` automatically:
1. Runs tests
2. Builds Docker images
3. Deploys to Railway
4. Sends Telegram notification

### 10.2 Manual Deployments

To redeploy without code changes:

1. Go to Railway dashboard
2. Click service → "Deploy" tab
3. Click "Redeploy"

### 10.3 Rollback

If deployment fails:

1. Go to service → "Deployments" tab
2. Select previous successful deployment
3. Click "Rollback"

## Pricing & Costs

### Railway Free Tier

- $5 per month credit (free tier)
- Good for small projects
- Covers: small API + small web service

### Estimated Monthly Costs

| Component | Usage | Cost |
|-----------|-------|------|
| API (512 MB, 1 instance) | Always on | $5/month |
| Web (256 MB, 1 instance) | Always on | $3/month |
| Database (PostgreSQL) | 1 GB | $5/month |
| **Total** | | **$13/month** |

*Costs are approximate and may vary based on traffic.*

## Production Checklist

- ✅ Set all environment variables
- ✅ Enable GitHub Actions CI/CD
- ✅ Configure custom domain (optional)
- ✅ Set up monitoring and alerting
- ✅ Enable automatic backups
- ✅ Test health checks
- ✅ Configure rate limiting
- ✅ Set up error tracking (Sentry)
- ✅ Enable CORS properly
- ✅ Verify SSL certificate

## Monitoring Commands

```bash
# Check API status
curl https://your-api-url/health

# Check Web status
curl https://your-web-url

# View recent logs (via Railway CLI)
railway logs -s api --tail 100
railway logs -s web --tail 100

# Check service status
railway status
```

## Support & Help

- **Railway Docs:** https://docs.railway.app
- **Railway Community:** https://railway.app/community
- **GitHub Actions:** https://docs.github.com/en/actions
- **Telegram Bot API:** https://core.telegram.org/bots/api

## Next Steps

1. Deploy to Railway (this guide)
2. Monitor logs and performance
3. Gather user feedback
4. Optimize based on metrics
5. Scale as needed

Your Crypto Jobs Bot is now live in production! 🚀
