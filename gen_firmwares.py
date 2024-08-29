import os
from os import walk

path = "portalturret/.pio/build"
out = {}
for file in os.listdir(path):
    if file in ['project.checksum']:
        continue
    out[file] = open(f"{path}/{file}/firmware.bin", 'rb').read()

open("firmwares.py", "w").write("firmwares = " + (str(out)))
