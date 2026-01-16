dev:
	uv sync --extra dev

lint:
	ruff format .
	ruff check .
	mypy app/

run:
	python -m app.main
