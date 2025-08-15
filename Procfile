web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
worker: cd backend && python -m scraper.scheduler
release: cd backend && alembic upgrade head