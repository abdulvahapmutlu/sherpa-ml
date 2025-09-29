.PHONY: setup lint type test build clean

setup:
	python -m pip install -U pip
	pip install -e .[dev]
	pre-commit install

lint:
	ruff check .
	black --check .

type:
	mypy src

test:
	pytest -q

build:
	python -m build

clean:
	rm -rf dist build *.egg-info .mypy_cache .pytest_cache
