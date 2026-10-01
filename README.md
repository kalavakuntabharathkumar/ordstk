# Order and Inventory Management REST API

A runnable FastAPI starter for distributor product, stock, and order workflows.

## Features
- Product creation, listing, lookup, stock adjustment, and soft deactivation
- Order creation with inventory validation and stock decrement
- Role-gated routes and signed bearer tokens for local demo flows
- SQLAlchemy models, Alembic environment, Pydantic request/response schemas
- Pytest API coverage and Docker deployment

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs for Swagger UI.

## Test
```bash
pytest -q
```

## PostgreSQL
Set `DATABASE_URL`, for example:
`postgresql+psycopg://app:password@localhost:5432/orders`
Install a PostgreSQL driver such as `psycopg[binary]` when using PostgreSQL.

## Important security note
The compact HMAC token in `app/security.py` is intentionally a self-contained demo so the project runs with minimal dependencies. For production, replace it with a vetted JWT implementation, use proper password hashing and user persistence, move secrets to a secret manager, and enforce transaction/locking strategy for concurrent stock updates. `demo-login` is for local development only.
