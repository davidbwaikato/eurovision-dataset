#!/bin/bash

echo "Updating PATH to include CWD for geckodriver"
export PATH=$PWD:$PATH

python3 ./audio.sh

