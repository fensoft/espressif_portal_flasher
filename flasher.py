import sys
import tempfile
from types import MethodType

import esptool
from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from firmwares import firmwares

# nuitka-project: --product-version=1.0.0
VERSION = "1.0.0"

# --onefile
# nuitka-project: --standalone
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --windows-icon-from-ico=icon.ico
# nuitka-project: --company-name=fensoft
# nuitka-project: --product-name=PortalTurret
# nuitka-project: --copyright=fensoft@gmail.com
# nuitka-project: --macos-create-app-bundle
# nuitka-project: --macos-app-icon=icon.png

global window, app

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PortalTurret flasher" + " v" + VERSION)
        self.settings = QSettings("fensoft", "PortalTurret")
        self.setWindowIcon(QIcon("icon.png"))
        self.setMinimumWidth(800)
        mainlayout = QVBoxLayout()

        buttonlayout = QGridLayout()
        buttonlayout.setColumnMinimumWidth(0, 100)
        buttonlayout.setColumnMinimumWidth(1, 700)

        self.firmware = QComboBox()
        self.firmware.setCurrentIndex(self.firmware.findText(self.settings.value("firmware", "")))
        buttonlayout.addWidget(QLabel("Firmware"), 0, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.firmware, 0, 1)
        for name in firmwares.keys():
            self.firmware.addItem(name)

        self.port = QComboBox()
        self.refresh()
        buttonlayout.addWidget(QLabel("Serial port"), 1, 0, Qt.AlignRight)
        buttonlayout.addWidget(self.port, 1, 1)

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        flash = QPushButton("Flash")
        flash.clicked.connect(self.flash)
        buttonlayout.addWidget(refresh, 2, 0, Qt.AlignRight)
        buttonlayout.addWidget(flash, 2, 1)

        mainlayout.addLayout(buttonlayout)

        self.log = QTextEdit()
        mainlayout.addWidget(self.log)
        def new_write(self, data):
            global window
            window.log.moveCursor(QTextCursor.End)
            window.log.insertPlainText(data)
            app.processEvents()

        sys.stdout.write = MethodType(new_write, sys.stdout)

        widget = QWidget()
        widget.setLayout(mainlayout)
        self.setCentralWidget(widget)
    
    def flash(self):
        try:
            with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
                fp.write(firmwares[self.firmware.currentText()])
                fp.close()
                cmd = [
                    '--port', self.port.currentData(),
                    '--baud','115200',
                    '--after', 'no_reset', 'write_flash',
                    '--flash_mode', 'dout', '0x00000', fp.name,
                    '--erase-all'
                ]
                esptool.main(cmd)
                QMessageBox.information(self, "Success", "Success")
        except Exception as e:
            QMessageBox.critical(self, "Error", "Error")
        

    def save(self):
        self.settings.setValue("port", self.port.currentData())

    def refresh(self):
        self.port.clear()
        for port in QSerialPortInfo.availablePorts():
            text = port.portName()
            text += " / " + port.description() if port.description() != "" else ""
            text += " / " + port.manufacturer() if port.manufacturer() != "" else ""
            self.port.addItem(text, port.systemLocation())
        self.port.setCurrentIndex(self.port.findData(self.settings.value("port", "")))
    
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
window.save()