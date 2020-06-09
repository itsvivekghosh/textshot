import io
import sys

import pyperclip
import pytesseract
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

try:
    from pynotifier import Notification
except ImportError:
    pass


class Snipper(QtWidgets.QWidget):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)

        self.setWindowTitle("TextShot")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
        )

        self.setWindowState(self.windowState() | Qt.WindowFullScreen)
        self.screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos()).grabWindow(0)

        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.screen))
        self.setPalette(palette)

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.start, self.end = QtCore.QPoint(), QtCore.QPoint()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QtWidgets.QApplication.quit()

        return super().keyPressEvent(event)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 100))
        painter.drawRect(0, 0, self.width(), self.height())

        if self.start == self.end:
            return super().paintEvent(event)

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
        painter.setBrush(painter.background())
        painter.drawRect(QtCore.QRect(self.start, self.end))

        return super().paintEvent(event)

    def mousePressEvent(self, event):
        self.start = self.end = event.pos()
        self.update()

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.start == self.end:
            return super().mouseReleaseEvent(event)

        self.hide()
        QtWidgets.QApplication.processEvents()
        shot = self.screen.copy(QtCore.QRect(self.start, self.end))
        processImage(shot)
        QtWidgets.QApplication.quit()


def processImage(img):
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QBuffer.ReadWrite)
    img.save(buffer, "PNG")

    pil_img = Image.open(io.BytesIO(buffer.data()))
    buffer.close()

    try:
        result = pytesseract.image_to_string(
            pil_img, timeout=2, lang=(sys.argv[1] if len(sys.argv) > 1 else None)
        )

    except RuntimeError as error:
        print(f"An Error occured while processing the Image: {error}")
        notify(f"An Error occured while processing the Image: {error}")
        return

    if result:
        pyperclip.copy(result)
        print(f"INFO: Copied Result to the clipboard")
        notify(f"Copied Result to the Clipboard")
    else:
        print(f"INFO: Unable to read the text from the Image")
        notify(f"Unable to read the text from the Image, did not copied")


def notify(msg):
    try:
        Notification(title="TextShot", description=msg).send()
    except (SystemError, NameError):
        trayicon = QtWidgets.QSystemTrayIcon(
            QtGui.QIcon(
                QtGui.QPixmap.fromImage(QtGui.QImage(1, 1, QtGui.QImage.Format_Mono))
            )
        )

        trayicon.show()
        trayicon.showMessage("TextShot", msg, QtWidgets.QSystemTrayIcon.NoIcon)
        trayicon.hide()


if __name__ == "__main__":

    try:
        pytesseract.get_tesseract_version()
    except EnvironmentError as error:
        notify(
            "Teseeract-OCR is not installed or cannot be reached\n"
            "Install it and then try again!"
        )

        print(
            f"ERROR: Tesseract-OCR Not Installed or cannot be reached {error}\n"
        )
        sys.exit()

    QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    snipper = Snipper(window)
    snipper.show()
    sys.exit(app.exec_())
