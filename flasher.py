import sys
import yaml
import tempfile
import requests
import os
import zipfile
import io

from types import MethodType
from extract import extract

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QLineEdit,
    QCheckBox,
)

import parameters
from version import VERSION
from tools import download_fs, patch_fs, upload_fs, upload_firmware

# --onefile
# nuitka-project: --standalone
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --windows-icon-from-ico=icon.ico
# nuitka-project: --windows-console-mode=disable
# nuitka-project: --company-name=fensoft
# nuitka-project: --product-name=PortalTurret
# nuitka-project: --copyright=fensoft@gmail.com
# nuitka-project: --macos-create-app-bundle
# nuitka-project: --macos-app-icon=icon.png
# nuitka-project: --include-module=littlefs.context

global app

class MainWindow(QMainWindow):
    def group_port(self):
        groupBox = QGroupBox("Serial port")
        self.port = QComboBox()
        buttonlayout = QGridLayout()
        buttonlayout.setColumnMinimumWidth(0, 100)
        buttonlayout.setColumnMinimumWidth(1, 700)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        buttonlayout.addWidget(QLabel("Port"), 0, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.port, 0, 1)
        buttonlayout.addWidget(refresh, 1, 1)
        groupBox.setLayout(buttonlayout)
        return groupBox

    def group_firmware(self):
        groupBox = QGroupBox("Firmware")
        buttonlayout = QGridLayout()
        buttonlayout.setColumnMinimumWidth(0, 100)
        buttonlayout.setColumnMinimumWidth(1, 700)

        self.firmware = QComboBox()
        self.firmware.setCurrentIndex(
            self.firmware.findText(self.settings.value("firmware", ""))
        )
        buttonlayout.addWidget(QLabel("Version"), 0, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.firmware, 0, 1)
        for name in parameters.firmwares.keys():
            self.firmware.addItem(name)
        flash = QPushButton("Flash")
        flash.clicked.connect(self.flash)
        buttonlayout.addWidget(flash, 2, 1)
        groupBox.setLayout(buttonlayout)
        return groupBox

    def slot_show_password(self):
        self.password.setEchoMode(
            QLineEdit.EchoMode.Normal
            if self.show_password.isChecked()
            else QLineEdit.EchoMode.Password
        )

    def slot_load_from(self, index):
        if index == 0:
            self.source.setText(
                "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Portal 2"
            )
        else:
            self.source.setText("https://joranderaaff.nl/portal-sentry/audio/")

    def update(self):
        print('downloading old fs')
        download_fs(
            self.port.currentData().replace("\\\\.\\", ""),
            str(parameters.littlefs["offset"]),
            str(parameters.littlefs["size"]),
            f"{self.temp}/fs.bin",
        )
        if self.load_from.currentData() == "game":
            if not os.path.exists(f"{self.temp}/ffmpeg.exe"):
                print('downloading ffmpeg')
                content = requests.get(self.ffmpeg.text())
                zip = zipfile.ZipFile(io.BytesIO(content.content))
                for i in zip.filelist:
                    if 'ffmpeg.exe' in i.filename:
                        print(f'using {i.filename}')
                        open(f"{self.temp}/ffmpeg.exe", "wb").write(zip.read(i.filename))
            print('converting audio files')
            content = extract(
                self.source.text(),
                self.language.currentText(),
                parameters.sounds,
                self.temp
            )
        else:
            print('downloading audio files')
            prefix = self.source.text()
            language = self.language.currentText()
            content = {}
            for key, val in parameters.sounds.items():
                for i in range(1, len(val) + 1):
                    result = requests.get(f"{prefix}/{language}/{key}/{i:03}.mp3")
                    content[f"{key}/{i:03}.mp3"] = result.content
        print('patching fs')
        patch_fs(f"{self.temp}/fs.bin", content, {"wifiSSID": self.ssid.text(), "wifiPassword": self.password.text()})
        print('uploading fs')
        upload_fs(
            self.port.currentData().replace("\\\\.\\", ""),
            str(parameters.littlefs["offset"]),
            f"{self.temp}/fs.bin",
        )

    def group_fs(self):
        groupBox = QGroupBox("Filesystem")
        buttonlayout = QGridLayout()
        buttonlayout.setColumnMinimumWidth(0, 100)
        buttonlayout.setColumnMinimumWidth(1, 700)

        self.language = QComboBox()
        buttonlayout.addWidget(QLabel("Audio language"), 0, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.language, 0, 1)
        for lang in ["english", "german", "french", "spanish", "russian"]:
            self.language.addItem(lang, lang)

        self.load_from = QComboBox()
        self.load_from.addItem("Load audio from game path (*.vpk)", "game")
        self.load_from.addItem("Load audio from URL", "url")
        self.source = QLineEdit()
        buttonlayout.addWidget(self.load_from, 1, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.source, 1, 1)
        self.load_from.currentIndexChanged.connect(self.slot_load_from)
        self.slot_load_from(0)

        self.ffmpeg = QLineEdit()
        self.ffmpeg.setText("https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip")
        buttonlayout.addWidget(QLabel("URL zip containing ffmpeg.exe"), 2, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.ffmpeg, 2, 1)

        self.ssid = QLineEdit()
        buttonlayout.addWidget(QLabel("WiFi SSID"), 3, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.ssid, 3, 1)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        buttonlayout.addWidget(QLabel("WiFi password"), 4, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.password, 4, 1)

        self.show_password = QCheckBox()
        buttonlayout.addWidget(QLabel("Show password"), 5, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.show_password, 5, 1)
        self.show_password.clicked.connect(self.slot_show_password)

        update = QPushButton("Update Filesystem")
        update.clicked.connect(self.update)
        buttonlayout.addWidget(update, 6, 1)

        groupBox.setLayout(buttonlayout)
        return groupBox

    def __init__(self, temp):
        super().__init__()
        self.temp = temp
        self.setWindowTitle("PortalTurret flasher" + " v" + VERSION)
        self.settings = QSettings("fensoft", "PortalTurret")
        self.setWindowIcon(QIcon("icon.png"))
        self.setMinimumWidth(800)
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.group_port())
        mainlayout.addWidget(self.group_firmware())
        mainlayout.addWidget(self.group_fs())
        self.refresh()

        log = self.log = QTextEdit()
        mainlayout.addWidget(self.log)

        widget = QWidget()
        widget.setLayout(mainlayout)
        self.setCentralWidget(widget)

        def new_write(self, data):
            global window
            log.moveCursor(QTextCursor.End)
            log.insertPlainText(str(data))
            app.processEvents()

        sys.stdout.write = MethodType(new_write, sys.stdout)
        sys.stderr.write = MethodType(new_write, sys.stdout)
        print(f'using temp dir {self.temp}')

    def flash(self):
        try:
            upload_firmware(
                self.port.currentData().replace("\\\\.\\", ""),
                parameters.firmwares[self.firmware.currentText()],
                self.temp,
                'esp8266' if 'esp8266' in self.firmware.currentText() else 'esp32'
            )
            QMessageBox.information(self, "Success", "Success")
        except Exception as e:
            QMessageBox.critical(self, "Error", "Error")

    def save(self):
        self.settings.setValue("port", self.port.currentData())
        self.settings.setValue("language", self.language.currentData())
        self.settings.setValue("load_from", self.load_from.currentIndex())
        self.settings.setValue("source", self.source.text())
        self.settings.setValue("ssid", self.ssid.text())
        self.settings.setValue("password", self.password.text())

    def refresh(self):
        self.port.clear()
        for port in QSerialPortInfo.availablePorts():
            text = port.portName()
            text += " / " + port.description() if port.description() != "" else ""
            text += " / " + port.manufacturer() if port.manufacturer() != "" else ""
            self.port.addItem(text, port.systemLocation())
        self.port.setCurrentIndex(self.port.findData(self.settings.value("port", "")))
        self.language.setCurrentIndex(
            self.language.findData(self.settings.value("language", ""))
        )
        self.load_from.setCurrentIndex(self.settings.value("load_from", ""))
        self.source.setText(self.settings.value("source", ""))
        self.ssid.setText(self.settings.value("ssid", ""))
        self.password.setText(self.settings.value("password", ""))

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.save()
            self.close()

with tempfile.TemporaryDirectory() as temp:
    app = QApplication(sys.argv)
    window = MainWindow(temp)
    window.show()
    app.exec()
    window.save()
