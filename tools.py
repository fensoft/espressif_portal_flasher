import time
import esptool
from PySide6.QtSerialPort import QSerialPortInfo
import parameters
from littlefs import LittleFS
import json


def cmd(port, cmd):
    cmd = ["--port", port] + cmd
    before = [port.portName() for port in QSerialPortInfo.availablePorts()]
    try:
        esptool.main(cmd)
        return
    except:
        pass
    time.sleep(2)
    after = [port.portName() for port in QSerialPortInfo.availablePorts()]
    for i in before:
        after.remove(i)
    cmd[1] = after[0]
    esptool.main(cmd)


def download_fs(port, offset, size, out):
    cmd(
        port,
        [
            "read_flash",
            offset,
            size,
            out,
        ],
    )


def upload_fs(port, offset, out):
    cmd(
        port,
        [
            "write_flash",
            offset, out,
        ],
    )


def upload_firmware(port, files, tempdir, chip):
    for i in files.keys():
        fp = open(f"{tempdir}\\{i}.bin", "wb")
        fp.write(files[i])
        fp.close()
    if chip == 'esp8266':
        cmd(
            port,
            [
                "write_flash",
                "0x0", f"{tempdir}\\firmware.bin"
            ],
        )
    else:
        cmd(
            port,
            [
                "write_flash",
                "0x1000", f"{tempdir}\\bootloader.bin",
                "0x8000", f"{tempdir}\\partitions.bin",
                "0xe000", f"{tempdir}\\boot_app0.bin",
                "0x10000", f"{tempdir}\\firmware.bin"
            ],
        )


def patch_fs(file, content, forced_settings):
    fs = LittleFS(block_size=4096, block_count=parameters.littlefs["size"] / 4096)
    data = open(file, "rb").read()
    fs.context.buffer = bytearray(data)
    settings = {}
    try:
        fs.mount()
        print('old fs mounted')
        settings = json.loads(fs.open("settings.json").read())
        print('old settings loaded:', settings)
    except:
        pass
    settings.update(forced_settings)
    print(settings)
    fs.format()
    fs.mount()
    s = fs.open("/settings.json", "w")
    s.write(json.dumps(settings))
    s.close()
    for key, value in content.items():
        try:
            fs.mkdir(key.split("/")[0])
        except:
            pass
        f = fs.open(f"/{key}", "wb")
        f.write(value)
        f.close()

    for root, dirs, files in fs.walk("."):
        print(f"root {root} dirs {dirs} files {files}")

    with open(file, "wb") as f:
        f.write(fs.context.buffer)
    
