#!/bin/bash

P="${PWD}"

cd ../../ && git archive -9 --format tar.gz -o $P/hilbert-cli.tar.gz HEAD && cd -

