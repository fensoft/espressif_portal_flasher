#!/bin/bash
set -e
set -x
if [ ! -e portalturret ]; then
  git clone https://github.com/joranderaaff/portalturret.git
fi
cd portalturret
git fetch --tags --force
git checkout $1
if [ "$OS" = "Windows_NT" ]; then
  $HOME/.platformio/penv/Scripts/pio.exe run
else
  pio run
fi
cd ..
pip install -r requirements.txt
python gen_firmwares.py
echo "VERSION = '$1'" > version.py
python -m nuitka flasher.py --product-version=$1
if [ "$OS" = "Windows_NT" ]; then
  SP=`python -m site | grep site-packages | grep -v USER_SITE | sed "s#^[ ]*'##g" | sed "s#',\\$##" | sed "s#\\\\\#/#g" | sed "s#//#/#g" | sed "s#:##"`
  mkdir -p flasher.dist/esptool/targets/stub_flasher
  cp /$SP/esptool/targets/stub_flasher/* flasher.dist/esptool/targets/stub_flasher
  cp icon.png flasher.dist
  rm -rf flasher-$1
  cp -rf flasher.dist flasher-$1
else
  SP=`python -m site | grep site-packages | grep -v USER_SITE | sed "s#^[ ]*'##g" | sed "s#',\\$##"`
  ls $SP/esptool/targets/stub_flasher
  mkdir -p flasher.app/Contents/MacOS/esptool/targets/stub_flasher
  cp $SP/esptool/targets/stub_flasher/* flasher.app/Contents/MacOS/esptool/targets/stub_flasher
  cp icon.png flasher.app/Contents/MacOS/
  rm -rf flasher-$1-$MACHTYPE.app
  cp -rf flasher.app flasher-$1-$MACHTYPE.app
fi
