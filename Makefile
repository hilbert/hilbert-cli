## ---------------------------------------------- [ Makefile for Python Checks ]

# Simple Makefile used during development to check compliance with
# pep8 and to generate documentation

SRC=config/*.py tools/*.py
NAME=hilbert

.PHONY: usage pep8 apidocs clean pylint install build all_docs

usage: # Print Targets
	@grep '^[^#[:space:]].*:' Makefile

check: # Run the tests
	/bin/bash -c 'py.test-3 -vv -l --tb=auto --full-trace --color=auto tests/test_*.py'
#	/bin/bash -c 'py.test -vv -l --tb=auto --full-trace --color=auto tests/test_*.py'
	
tox: tox.ini setup.py # Run clean testing via tox
	tox
	
pep8: ${SRC} # Check for PEP8 compliance
	pep8 --first --show-source --show-pep8 --statistics --max-line-length=100 --format=pylint ${SRC} > docs/pep8.report.txt 2>&1 || echo $?

pylint: # Analyse Source 
	pylint --rcfile=rcfile.pylint -f html --comment=y --files-output=y ${SRC}  2>&1 || echo $? # --full-documentation
	mv pylint_*.html docs/

all_docs: apidocs epydoc pep8 pylint

apidocs: ${SRC} # Build API Documentation with doxygen
	doxygen Doxyfile 2>&1 || echo $?

epydoc: ${SRC} # Build API Documentation with epydoc
	epydoc --html -o docs/epydoc --inheritance=listed --show-imports --graph=all ${SRC}  2>&1 || echo $?

clean: # Clean Project
	rm -rf *~ docs/doxy docs/epydoc docs/pylint_*.html docs/pep8.report.txt

dist/hilbert: hilbert.spec
	pyinstaller hilbert.spec
