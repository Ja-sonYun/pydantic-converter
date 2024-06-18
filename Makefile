MAKEFLAGS += --always-make

check-all:
	# tox
	mypy .
	ruff check --diff
	ruff format --diff

format:
	ruff format
