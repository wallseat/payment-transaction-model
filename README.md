# Payment Transaction Model

## Quick Start
1. Create your .env file. U can use copy of .env.example
    2.1. Use `poetry` to install deps `poetry install`.
    2.2. Or use `python3 -m venv ./.venv && source ./.venv/bin/activate && pip install -r requirements.txt && pip install -e .`
3. Run `docker compose up -d postgres`
4. Run `POSTGRES_HOST=localhost alembic upgrade head`
5. Run `docker compose up -d`
6. API docs - `localhost:8000/docs`
