#!/usr/bin/env bash

# Set CWD to this script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd $DIR

export PYTHONPATH="../../":$PYTHONPATH
# Run all tests. Note that unittest's built-in discovery doesn't run the dynamic 
# testcase generation they contain
for i in test_*.py;
do 
    echo $i;
    python3 $i;
    echo
done


# revert to original dir
cd -
