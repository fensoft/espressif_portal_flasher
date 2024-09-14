#!/bin/bash
set -e
set -x
if [ "$1" = "" ]; then
  echo "$0 <version>"
  exit 1
fi
if [ ! -e portalturret ]; then
  git clone https://github.com/joranderaaff/portalturret.git
fi
cd portalturret
git fetch --tags --force
git pull origin $1
git checkout $1
if [ "$OS" = "Windows_NT" ]; then
  $HOME/.platformio/penv/Scripts/pio.exe run
else
  pio run
fi
cd ..
pip install -r requirements.txt
if [ ! -e ffmpeg ]; then
  curl -L https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip -o ffmpeg.zip
  unzip ffmpeg.zip
  mv ffmpeg-* ffmpeg
  rm ffmpeg.zip
fi
python gen_parameters.py "$HOME/.platformio/packages/framework-arduinoespressif32@3.20006.221224/tools/partitions/boot_app0.bin"
echo "VERSION = '$1'" > version.py
python -m nuitka flasher.py --product-version=$1 --output-dir=temp
if [ "$OS" = "Windows_NT" ]; then
  SP=`python -m site | grep site-packages | grep -v USER_SITE | sed "s#^[ ]*'##g" | sed "s#',\\$##" | sed "s#\\\\\#/#g" | sed "s#//#/#g" | sed "s#:##"`
  mkdir -p flasher.dist/esptool/targets/stub_flasher
  cp /$SP/esptool/targets/stub_flasher/* flasher.dist/esptool/targets/stub_flasher
  rm -rf flasher-$1
  cp -rf flasher.dist flasher-$1
  cp icon.png flasher-$1
  cp -rf temp/flasher.dist/* flasher-$1
else
  SP=`python -m site | grep site-packages | grep -v USER_SITE | sed "s#^[ ]*'##g" | sed "s#',\\$##"`
  ls $SP/esptool/targets/stub_flasher
  mkdir -p flasher.app/Contents/MacOS/esptool/targets/stub_flasher
  cp $SP/esptool/targets/stub_flasher/* flasher.app/Contents/MacOS/esptool/targets/stub_flasher
  cp icon.png flasher.app/Contents/MacOS/
  rm -rf flasher-$1-$MACHTYPE.app
  cp -rf flasher.app flasher-$1-$MACHTYPE.app
fi
