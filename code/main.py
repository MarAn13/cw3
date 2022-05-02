"""
Launches application
"""

from PyQt5.QtWidgets import QApplication
from main_window import MainWindow


def main():
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable high dpi scaling
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use high dpi icons
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
