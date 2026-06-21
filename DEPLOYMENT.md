# TrustCheck Deployment Guide

## Architecture

- **Frontend**: Next.js 15 deployed to Vercel
- **Backend**: FastAPI deployed to Railway or Render
- **Database**: Neon PostgreSQL (serverless)

## Prerequisites

- Vercel account
- Railway or Render account
- Neon PostgreSQL account

## Environment Variables

### Frontend (Vercel)
```
NEXT_PUBLIC_API_URL=https://your-api.railway.app
```

### Backend (Railway/Render)
```
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
DATABASE_URL_SYNC=postgresql://user:pass@host/db

# Security — generate a strong, unique key (the app refuses to start in
# production with a weak/placeholder SECRET_KEY):
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=<output-of-the-command-above>

# CORS — comma-separated list of your real frontend origins (required in prod)
CORS_ORIGINS=https://your-app.vercel.app

# Environment
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
```

## Deployment Steps

### 1. Database Setup (Neon)

1. Create new project in Neon
2. Create database
3. Copy connection string
4. Add to backend environment variables

### 2. Backend Deployment (Railway)

```bash
cd backend
railway login
railway init
railway up
```

Or connect GitHub repo to Railway for auto-deploy.

### 3. Frontend Deployment (Vercel)

```bash
cd frontend
vercel login
vercel --prod
```

Or connect GitHub repo to Vercel.

### 4. Database Migration

After backend is deployed:

```bash
railway run alembic upgrade head
```

## Health Check

- Backend: `https://your-api.railway.app/health`
- Frontend: `https://your-app.vercel.app`

## Post-Deployment Verification

1. Test registration/login
2. Create a verification
3. Download a report
4. Check all API endpoints

## Troubleshooting

### CORS Issues
Update `allowed_origins` in backend config with your Vercel domain.

### Database Connection
Verify `DATABASE_URL` includes correct async driver (`postgresql+asyncpg`).

### File Uploads
Ensure `uploads/` directory is writable or configure external storage.

## Monitoring

- Railway dashboard: CPU, memory, logs
- Vercel analytics: Web vitals, errors
- Neon dashboard: Database metrics

The backend emits structured JSON logs in production (`APP_ENV=production`).
Watch for:
- `Failed login` warnings (brute-force / credential stuffing)
- `Rate limit exceeded` / `blocking for 5 minutes` (abuse)
- `Blocked SSRF attempt` (attempts to reach internal hosts)
- `Unhandled exception` (server errors — these never leak details to clients)

## Production Security Checklist

Before going live, confirm:

- [ ] `APP_ENV=production` and `DEBUG=false` are set on the backend.
- [ ] `SECRET_KEY` is a unique 48+ char random value (app refuses weak keys in prod).
- [ ] `CORS_ORIGINS` lists only your real frontend domain(s) — no wildcards.
- [ ] HTTPS is enforced end-to-end (Vercel and Railway both serve TLS by
      default; HSTS is sent automatically in production).
- [ ] Database is **not** publicly reachable — restrict access to the backend
      host / use the provider's private networking, and require SSL.
- [ ] `alembic upgrade head` has been run against the production database.
- [ ] `.env`, `*.db`, and `uploads/` are git-ignored and were never committed
      (see `.gitignore`). Rotate `SECRET_KEY` if a real one ever leaked.
- [ ] API docs are disabled in production (they are — `/docs` and `/redoc`
      return 404 when `APP_ENV=production`).

### Not yet implemented (require an email provider)

Two authentication features need an outbound email service (SendGrid / AWS SES /
Postmark) plus SMTP credentials before they can function:

- **Email verification** — the `users.email_verified` column exists but no
  verification email is sent yet.
- **Password reset** — only authenticated password *change* exists today; a
  "forgot password" flow needs tokenized reset emails (store only the token
  hash, expire after ~1 hour).

Wire these up once an email provider is chosen; the data model already
accommodates them.
