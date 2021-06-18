.PHONY: all test test_minimal test_common

all: test

test_common:
	-rm -rf coverage-html
	-rm -rf .coverage
	python3-coverage erase
	python3-coverage run -p test_utils.py
	python3-coverage run -p test_offer.py
	python3-coverage run -p test_selfreport.py
	python3-coverage run -p test_bl4p_backend.py
	python3-coverage run -p test_bl4p_rpc.py
	python3-coverage run -p test_offerbook_backend.py
	python3-coverage run -p test_offerbook_rpc.py
	python3-coverage run -p test_rpcserver.py
	python3-coverage run -p test_bl4p.py
	python3-coverage combine

test_minimal: test_common
	python3-coverage report

test: test_common
	python3-coverage html
	python3-coverage report

