# Wheelhouse

Personal options wheel strategy tracker — covered calls, cash-secured puts, premium yield metrics.

## Stack

| Layer    | Tech                          | Hosting   |
|----------|-------------------------------|-----------|
| Frontend | React 19, Vite, TypeScript    | Vercel    |
| Backend  | FastAPI, SQLAlchemy, Alembic  | Fly.io    |
| Database | PostgreSQL                    | Supabase  |
| UI       | shadcn/ui, Tailwind CSS       |           |
| Auth     | Supabase Auth (JWT)           |           |

## Features

- Track covered calls and cash-secured puts
- Open positions dashboard with real-time prices
- Closed positions history
- Premium yield / annualized return metrics
- Real-time price alerts (client-side MVP)
- CSV export for taxes / recordkeeping
- Per-account portfolio tracking
- Column visibility toggles and settings

## Project Structure

```
wheelhouse/
├── frontend/              # React SPA (Vite + TypeScript)
│   ├── src/
│   │   ├── components/    # shadcn/ui + custom components
│   │   ├── contexts/      # AuthContext, SettingsContext
│   │   ├── hooks/         # Custom React hooks
│   │   ├── pages/         # Route pages
│   │   ├── types/         # TypeScript types
│   │   └── lib/           # Utilities
│   └── package.json
├── backend/               # FastAPI Python API
│   ├── app/
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── routers/       # API route handlers
│   │   ├── auth.py        # JWT middleware
│   │   ├── config.py      # Pydantic settings
│   │   └── database.py    # SQLAlchemy engine setup
│   ├── alembic/           # Database migrations
│   ├── tests/             # pytest tests
│   ├── requirements.txt
│   └── alembic.ini
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- A [Supabase](https://supabase.com) project (for PostgreSQL and auth)

## Getting Started

### 1. Clone the repo

```bash
git clone <repo-url>
cd wheelhouse
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Fill in your Supabase credentials (found in the Supabase dashboard under **Settings > API**):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
DATABASE_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head         # Run database migrations
uvicorn app.main:app --reload
```

The API will be running at **http://localhost:8000** (docs at `/docs`).

### 4. Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The app will be running at **http://localhost:5173**.

## Development

### Backend

```bash
cd backend && source .venv/bin/activate

uvicorn app.main:app --reload          # Dev server
pytest                                  # Run tests
alembic revision --autogenerate -m ""   # Create migration
alembic upgrade head                    # Apply migrations
```

### Frontend

```bash
cd frontend

npm run dev       # Dev server with HMR
npm run build     # Type-check + production build
npm run lint      # ESLint
npm run preview   # Preview production build
```
