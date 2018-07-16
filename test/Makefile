.PHONY: all test

all: test

test:
	python3-coverage run -p test_storage.py
	python3-coverage combine
	python3-coverage html
	python3-coverage report

