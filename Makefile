.PHONY: install test bronze api frontend clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-api:
	cd api && pytest tests/ -v

bronze:
	python pipelines/bronze/ingest.py

api:
	cd api && uvicorn app.main:app --reload

frontend:
	cd frontend && ng serve

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
