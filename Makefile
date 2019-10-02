clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + > /dev/null 2>&1
	find . -type f -name "*.pyc" -exec rm -rf {} + > /dev/null 2>&1

isort:
	isort -rc .

test:
	flake8 --show-source metaform
	isort --check-only -rc metaform --diff
	coverage run --source='metaform' -m unittest
	coverage report

install:
	pip install -r requirements.txt
	pre-commit install
