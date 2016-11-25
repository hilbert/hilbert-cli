## ---------------------------------------------- [ Makefile for Python Checks ]

# Simple Makefile used during development to check compliance with
# pep8 and to generate documentation

SRC=config/*.py tools/*.py
NAME=hilbert

.PHONY: usage pep8 apidocs clean pylint install build

usage: # Print Targets
	@grep '^[^#[:space:]].*:' Makefile

check: # Run the tests
	/bin/bash -c 'cd tests/ && py.test -v test_*.py'
	/bin/bash -c 'cd tests/ && py.test-3 -v test_*.py'

pep8: ${SRC} # Check for PEP8 compliance
	pep8 --first --show-source --show-pep8 ${SRC}

pylint: # Analyse Source
	pylint -f html --files-output=y ${SRC}

apidocs: ${SRC} # Build API Documentation with doxygen
	doxygen Doxyfile

epydoc: ${SRC} # Build API Documentation with epydoc
	epydoc --html --inheritance=listed --graph=all ${SRC}

clean: # Clean Project
	rm -rf doxydoc *~
#	python3 distribute_setup.py clean
