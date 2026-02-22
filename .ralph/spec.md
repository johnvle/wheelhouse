# Wheelhouse — Implementation Plan

## Context

Building a personal options wheel strategy tracker for 1-2 users. The app functions like an Excel dashboard: track covered calls and cash-secured puts, view open/closed positions, see premium yield metrics, get price alerts, and export to CSV.

## Decisions Finalized

| Decision | Choice |
|---|---|
| Auth | Supabase Auth (email/password, JWT) |
| Table UI | TanStack Table + shadcn/ui |
| Price API | Yahoo Finance (unofficial) |
| Roll workflow | Guided close+open (two-step modal) |
| Underlyings | String column on positions (no separate table) |
| State management | TanStack Query only + React useState/context |
| Mobile | Desktop only |

## Stack

| Layer | Tech | Deploy |
|---|---|---|
| Frontend | React + TypeScript + Vite, TanStack Table, TanStack Query, shadcn/ui, Tailwind | Vercel |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 | Fly.io |
| Database | PostgreSQL | Supabase |
| Auth | Supabase Auth | Supabase |

---

## Database Schema (Supabase PostgreSQL)

No `users` table needed — Supabase Auth manages that. All tables reference `auth.users.id`.

### `accounts`
- `id` uuid PK default gen_random_uuid()
- `user_id` uuid FK → auth.users.id NOT NULL
- `name` text NOT NULL (e.g., "Robinhood Taxable", "Merrill Roth")
- `broker` text NOT NULL (robinhood, merrill, other)
- `tax_treatment` text nullable (taxable, roth, traditional)
- `created_at`, `updated_at` timestamptz

### `positions`
- `id` uuid PK default gen_random_uuid()
- `user_id` uuid FK → auth.users.id NOT NULL
- `account_id` uuid FK → accounts.id NOT NULL
- `ticker` text NOT NULL (uppercase, e.g., "AAPL")
- `type` text NOT NULL CHECK (COVERED_CALL, CASH_SECURED_PUT)
- `status` text NOT NULL CHECK (OPEN, CLOSED) default OPEN
- `open_date` date NOT NULL
- `expiration_date` date NOT NULL
- `close_date` date nullable
- `strike_price` numeric NOT NULL
- `contracts` int NOT NULL
- `multiplier` int NOT NULL default 100
- `premium_per_share` numeric NOT NULL
- `open_fees` numeric default 0
- `close_fees` numeric default 0
- `close_price_per_share` numeric nullable
- `outcome` text nullable CHECK (EXPIRED, ASSIGNED, CLOSED_EARLY, ROLLED)
- `roll_group_id` uuid nullable
- `notes` text nullable
- `tags` text[] nullable (Postgres array — simpler than a join table)
- `created_at`, `updated_at` timestamptz

**Indexes:** `(user_id, status)`, `(user_id, ticker)`, `(user_id, expiration_date)`

---

## API Endpoints (FastAPI, `/api/v1`)

Auth: All endpoints except health require a valid Supabase JWT in `Authorization: Bearer <token>`. FastAPI middleware extracts `user_id` from the token.

### Accounts
- `GET /accounts` — list user's accounts
- `POST /accounts` — create account
- `PATCH /accounts/{id}` — update account

### Positions
- `GET /positions?status=OPEN&ticker=&type=&account_id=&expiration_start=&expiration_end=&sort=&order=` — list with filters
- `POST /positions` — create position
- `PATCH /positions/{id}` — update position fields
- `POST /positions/{id}/close` — close a position (sets status, outcome, close_date, close_price_per_share)
- `POST /positions/{id}/roll` — guided roll: closes old position + creates new linked position in one request. Body includes close fields for old + open fields for new. Both share a `roll_group_id`.

### Dashboard
- `GET /dashboard/summary?start=&end=` — totals: premium collected, open count, upcoming expirations
- `GET /dashboard/by-ticker?start=&end=` — per-ticker: premium, trade count, avg annualized ROC

### Market Prices
- `GET /prices?tickers=AAPL,TSLA` — batch fetch current prices via Yahoo Finance. Backend proxies + caches briefly (60s) to avoid hammering.

### Export
- `GET /export/positions.csv?start=&end=&status=&ticker=` — CSV download respecting filters

### Health
- `GET /health` — no auth required

---

## Frontend Pages & Components

### Pages
1. **Login** — Supabase Auth UI (email/password)
2. **Open Positions** (default route `/`) — main table
3. **History** (`/history`) — closed positions table
4. **Dashboard** (`/dashboard`) — metrics widgets
5. **Settings** (`/settings`) — alert thresholds, display prefs

### Core Components
- **PositionsTable** — TanStack Table with sorting, filtering, column visibility toggle, sticky header
- **AddPositionModal** — form to create a new position
- **ClosePositionModal** — set outcome, close date, close price
- **RollPositionModal** — two-step: close old (step 1) → open new prefilled (step 2)
- **DashboardSummary** — total premium, open count, upcoming expirations
- **TickerSummary** — grouped by-ticker stats
- **AlertBanner** — in-app alert notifications
- **CSVExportButton** — triggers filtered download

### Price Polling
- On Open Positions page load, collect distinct tickers from open positions
- Fetch `GET /prices?tickers=...` every 60 seconds
- Display current price + change % in table column
- Stale indicator if last update > 5 minutes

### Client-Side Alerts (evaluated on price refresh)
1. **Expiration soon** — position expires within N days (configurable, default 7)
2. **Price near strike** — CC: price >= strike * (1 - threshold); CSP: price <= strike * (1 + threshold)
3. **Stale price** — no update in N minutes

---

## Calculations (computed on backend, returned in API responses)

Per position:
- `premium_total = premium_per_share × multiplier × contracts`
- `premium_net = premium_total - open_fees - close_fees`
- `collateral = strike_price × multiplier × contracts`
- `roc_period = premium_total / collateral`
- `dte = expiration_date - open_date` (days)
- `annualized_roc = roc_period × (365 / dte)`

Dashboard aggregates:
- Total premium (lifetime / date range)
- Premium MTD
- By-ticker: total premium, trade count, avg annualized ROC

---

## Build Order

### Phase 1: Foundation
1. Set up Supabase project (database + auth)
2. Create Alembic migrations for `accounts` and `positions` tables
3. FastAPI auth middleware (verify Supabase JWT)
4. CRUD endpoints: accounts, positions (create, list, update)
5. Frontend: install Tailwind, shadcn/ui, TanStack Table, TanStack Query
6. Frontend: Supabase Auth login page
7. Frontend: basic Open Positions table (read-only, no prices)

### Phase 2: Core Workflows
8. Close position endpoint + modal
9. Roll position endpoint + two-step modal
10. History page (closed positions table with filters)
11. Add Position modal with form validation

### Phase 3: Dashboard & Metrics
12. Backend: dashboard summary + by-ticker endpoints (with calculations)
13. Frontend: Dashboard page with widgets

### Phase 4: Prices & Alerts
14. Backend: Yahoo Finance proxy endpoint with caching
15. Frontend: price column in Open Positions table + polling
16. Frontend: client-side alert evaluation + alert banner

### Phase 5: Export & Polish
17. CSV export endpoint + button
18. Settings page (alert thresholds)
19. Column visibility toggles, sorting/filter UX polish

---

## Verification

- **Backend:** Run `uvicorn app.main:app --reload` locally, test all endpoints with curl/httpie
- **Frontend:** Run `npm run dev`, verify login → positions table → add/close/roll → dashboard → export flow
- **Auth:** Confirm unauthenticated requests are rejected, tokens refresh correctly
- **Prices:** Verify batch price fetch returns data for valid tickers, handles invalid tickers gracefully
- **Alerts:** Open a position near expiration or with price near strike, confirm alert banner appears
- **CSV:** Export with filters, open in Excel/Sheets, verify columns and data
- **Deploy:** Push frontend to Vercel, backend to Fly.io, DB on Supabase — verify end-to-end in production
