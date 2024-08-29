#!/bin/bash
set -e
set -x
if [ ! -e portalturret ]; then
  git clone https://github.com/joranderaaff/portalturret.git
fi
cd portalturret
git fetch --tags --force
git checkout $1
pio run
cd ..
python gen_firmwares.py
python -m nuitka flasher.py