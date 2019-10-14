#!/usr/bin/env bash

# Set CWD to this script's directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
cd "$DIR" || exit 1

COMPILED_EXAMPLES=${PWD}/Compiled_examples

echo
# if COMPILED_EXAMPLES doesn't exist, create it.
if [ ! -e "$COMPILED_EXAMPLES" ]; then
  mkdir "$COMPILED_EXAMPLES"
fi

function run_example() {
  echo "==================================================="
  python "$1" "$2"
  echo "==================================================="
}

for py in *.py; do
  run_example "$py" "$COMPILED_EXAMPLES"
done

run_example mazebox/mazebox.py "$COMPILED_EXAMPLES"

# revert to original dir
cd - || exit 1
