import os, yaml
from os import walk
from extract import extract
import csv
import sys

params = open("parameters.py", "w")

path = "portalturret/.pio/build"
out = {}
for file in os.listdir(path):
    if file in ["project.checksum"]:
        continue
    out[file] = {"boot_app0": open(sys.argv[1], "rb").read()}
    for i in ["bootloader", "partitions", "firmware"]:
        if os.path.exists(f"{path}/{file}/{i}.bin"):
            out[file][i] = open(f"{path}/{file}/{i}.bin", "rb").read()
params.write("firmwares = " + str(out) + "\n")
for i in out.keys():
    print(out[i].keys())

params.write(
    "sounds = " + str(yaml.safe_load(open("portalturret/audio/sounds.yml"))) + "\n"
)

params.write("firmwares = " + str(out) + "\n")

reader = csv.reader(open("portalturret/partitions.csv"), delimiter=",")
first = True
for name, _, _, offset, size, _ in reader:
    if first:
        first = False
        continue
    offset = int(offset, 16)
    size = int(size, 16)
    if name == "spiffs":
        params.write(f"littlefs = " + str({"offset": offset, "size": size}) + "\n")
