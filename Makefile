.DEFAULT_GOAL := help

ifeq ($(WITH_COVERAGE), TRUE)
	TEST_COMMAND = COVERAGE_FILE=.coverage coverage run --rcfile .coveragerc setup.py nosetests
else
	TEST_COMMAND = nosetests
endif

help:
	@echo 'Use "make test" to run all the unit tests and docstring tests.'
	@echo 'Use "make pep8" to validate PEP8 compliance.'
	@echo 'Use "make html" to create html documentation with sphinx'
	@echo 'Use "make all" to run all the targets listed above.'
test:
	$(TEST_COMMAND)
pep8:
	flake8 spongeworld setup.py
html:
	make -C doc clean html

all: test pep8
