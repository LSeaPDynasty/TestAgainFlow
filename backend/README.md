# TestFlow Backend

FastAPI backend for TestFlow automation testing platform.

## Setup

1. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Initialize database:
```bash
# Create database tables
alembic upgrade head
```

## Run

Development server:
```bash
python -m app.main
```

Or with uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response models
├── routers/         # API route handlers
├── repositories/    # Data access layer
├── utils/           # Utility functions
├── database.py      # Database connection
├── config.py        # Configuration
└── main.py          # Application entry
```
