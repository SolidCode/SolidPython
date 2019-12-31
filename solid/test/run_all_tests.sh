#!/usr/bin/env bash

# Set CWD to this script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd $DIR

# Let unittest discover all the tests
python -m unittest discover .

# revert to original dir
cd -