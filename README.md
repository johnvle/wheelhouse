# Wheelhouse

Personal options wheel strategy tracker. Log covered calls and cash-secured puts, track premium income across brokerage accounts, and monitor yield metrics like return on collateral and annualized ROC.

## What it does

- **Open positions dashboard** — view all active covered calls and cash-secured puts with real-time prices, DTE countdown, and strike distance
- **Closed positions history** — track outcomes (expired, assigned, closed early, rolled) with P&L
- **Premium yield metrics** — auto-calculated return on collateral, annualized ROC, and net premium after fees
- **Multi-account support** — organize positions by brokerage account with broker and tax treatment metadata
- **Roll tracking** — link rolled positions together via roll groups
- **CSV export** — export position data for taxes and recordkeeping
- **Price alerts** — client-side alerts when underlying price approaches strike

## Tech stack

| Layer    | Tech                         |
| -------- | ---------------------------- |
| Frontend | React 19, Vite, TypeScript   |
| Backend  | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL (Supabase)        |
| Auth     | Supabase Auth (JWT)          |
| UI       | shadcn/ui, Tailwind CSS      |

## Project structure

```
wheelhouse/
├── frontend/              # React SPA
│   ├── src/
│   │   ├── components/    # shadcn/ui + custom components
│   │   ├── contexts/      # AuthContext, SettingsContext
│   │   ├── hooks/         # Custom React hooks
│   │   ├── pages/         # Route pages
│   │   ├── types/         # TypeScript interfaces
│   │   └── lib/           # Utilities, API client
│   └── package.json
├── backend/               # FastAPI API
│   ├── app/
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── routers/       # API route handlers
│   │   ├── auth.py        # JWT middleware
│   │   ├── config.py      # Pydantic settings
│   │   └── database.py    # SQLAlchemy engine setup
│   ├── alembic/           # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── alembic.ini
└── .env.example
```

## Local setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier works)

### Quick start

```bash
git clone https://github.com/johnvle/wheelhouse.git
cd wheelhouse
cp .env.example .env
# Fill in .env with your Supabase credentials (see below)
./dev.sh
```

This sets up the Python venv, installs dependencies, runs database migrations, and starts both servers. Press `Ctrl+C` to stop.

- Frontend: **http://localhost:5173**
- Backend: **http://localhost:8000**
- API docs: **http://localhost:8000/docs**

### Manual setup

#### 1. Clone and configure environment

```bash
git clone https://github.com/johnvle/wheelhouse.git
cd wheelhouse
cp .env.example .env
```

Fill in `.env` with your Supabase credentials (found under **Settings > API** in the Supabase dashboard):

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

#### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head         # run database migrations
uvicorn app.main:app --reload
```

API runs at **http://localhost:8000** — interactive docs at [localhost:8000/docs](http://localhost:8000/docs).

#### 3. Start the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

App runs at **http://localhost:5173**.

## Development

### Backend

```bash
cd backend && source .venv/bin/activate

uvicorn app.main:app --reload          # dev server
pytest                                  # run tests
alembic revision --autogenerate -m ""   # create migration
alembic upgrade head                    # apply migrations
```

### Frontend

```bash
cd frontend

npm run dev       # dev server with HMR
npm run build     # type-check + production build
npm run lint      # ESLint
```
