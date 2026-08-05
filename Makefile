.PHONY: install test run clean lint

install:
	pip install -e .

test:
	pytest tests/ -v

run:
	python -m armonic.run --config config.example.yaml

clean:
	rm -rf results/ __pycache__ .pytest_cache *.egg-info build dist
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

lint:
	python -m py_compile armonic/run.py
	python -m py_compile src/**/*.py
