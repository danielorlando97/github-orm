test:
	poetry run pytest tests/ -v --cov=github_orm --cov-report=xml --cov-report=term-missing