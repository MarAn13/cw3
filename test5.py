from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.widget = QWidget(self)
        self.widget_layout = QVBoxLayout()
        for i in range(0, 20):
            temp = QLabel('TextLabel')
            # temp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.widget_layout.addWidget(temp)#, i, 0, 1, 1)
        self.widget.setLayout(self.widget_layout)
        # self.scroll_widget = QWidget(parent=self.file_area)
        self.scroll = QScrollArea(self)  # parent=self.file_area)
        # self.scroll.setBackgroundRole(QPalette.Dark)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

    def resizeEvent(self, e):
        self.widget.resize(self.width(), self.height())
        self.scroll.resize(self.width(), self.height())
        # self.widget.setFixedSize(self.width(), self.height())
        #self.scroll.resize(self.width(), self.height())


app = QApplication([])
window = MainWindow()
window.setFixedSize(1200, 800)
window.show()
app.exec_()
