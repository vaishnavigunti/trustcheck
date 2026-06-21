# TrustCheck

**Evidence-Based Internship & Job Offer Verification Platform**

A full-stack SaaS application that helps students and job seekers verify internship opportunities, recruiters, job offers, and company websites using objective and evidence-based checks.

## Architecture

- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python 3.12 + SQLAlchemy
- **Database**: PostgreSQL
- **Deployment**: Vercel (frontend) + Railway/Render (backend)

## Project Structure

```
trustcheck/
├── frontend/              # Next.js application
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── components/   # React components
│   │   ├── lib/         # Utilities
│   │   ├── hooks/       # Custom hooks
│   │   └── types/       # TypeScript types
│   └── package.json
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── services/    # Business logic
│   │   ├── repositories/# Data access
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── core/        # Config, security, logging
│   │   └── utils/       # Helpers
│   ├── alembic/         # Database migrations
│   └── main.py          # Entry point
├── uploads/             # File storage
└── docs/               # Documentation
```

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- PostgreSQL 15+

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
alembic upgrade head
python main.py
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with API URL
npm run dev
```

## Environment Variables

See `.env.example` files in both frontend and backend directories.

## License

MIT
