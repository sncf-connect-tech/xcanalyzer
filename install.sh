#!/usr/bin/env bash

mkdir build

python3 -m venv venv
./venv/bin/pip install --upgrade pip

# We indicate the graphviz lib path
./venv/bin/pip install --install-option="--include-path=/usr/local/include/graphviz" --install-option="--library-path=/usr/local/lib" pygraphviz

./venv/bin/pip install -r requirements.txt