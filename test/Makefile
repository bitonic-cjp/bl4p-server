.PHONY: all test

all: test

test:
	python3-coverage run -p test_utils.py
	python3-coverage run -p test_bl4p_backend.py
	python3-coverage run -p test_bl4p_rpc.py
	python3-coverage run -p test_offerbook_backend.py
	python3-coverage run -p test_rpcserver.py
	python3-coverage run -p test_bl4p.py
	python3-coverage combine
	python3-coverage html
	python3-coverage report

