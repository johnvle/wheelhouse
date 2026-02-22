# Wheelhouse

Personal options wheel strategy tracker — covered calls, cash-secured puts, premium yield metrics.

## Stack

| Layer    | Tech       | Hosting   |
|----------|------------|-----------|
| Frontend | React      | Vercel    |
| Backend  | FastAPI    | Fly.io    |
| Database | PostgreSQL | Supabase  |

## Project Structure

```
wheelhouse/
├── frontend/          # React app (Vite + TypeScript)
├── backend/           # FastAPI Python API
│   └── app/
│       ├── models/    # SQLAlchemy / DB models
│       ├── schemas/   # Pydantic request/response schemas
│       ├── routers/   # API route handlers
│       └── services/  # Business logic
└── README.md
```

## Features

- Track covered calls and cash-secured puts
- Open positions dashboard
- Closed positions history
- Premium yield / annualized return metrics
- Real-time price alerts (client-side MVP)
- CSV export for taxes / recordkeeping
