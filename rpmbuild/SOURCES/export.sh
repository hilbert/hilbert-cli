#!/bin/bash

P="${PWD}"

## Generate current hilbert-cli.tar.gz

cd ../../ && git archive -9 --format tar.gz -o $P/hilbert-cli.tar.gz HEAD && cd -

##TODO/FIXME: get docker-compose.tar.gz from https://cloud.imaginary.org/index.php/s/n4YAGQXkvt1Whb3
##            get hilbert-compose-customizer.tar.gz from https://cloud.imaginary.org/index.php/s/ZNkWTSXhJ8ydMo8
