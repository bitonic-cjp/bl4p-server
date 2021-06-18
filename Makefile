.PHONY: proto test

proto:
	make -C bl4p_server proto

test:
	make -C test

test_minimal:
	make -C test test_minimal

