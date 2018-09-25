#!/usr/bin/env bash

# Set CWD to this script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd $DIR

for i in test_*.py;
do 
echo $i;
python $i;
echo
done

# revert to original dir
cd -