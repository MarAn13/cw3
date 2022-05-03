from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from PyQt5.QtGui import *

class Process(QObject):
    finished = pyqtSignal(dict, str)
    def __init__(self):
        super().__init__()

    def do_long_stuff(self):
        for i in range(10000):
            print(i, 'HELLO' * i)
        self.finished.emit({'test':'test'}, 'audio-only')

class LoadingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet('QWidget{background-color: black;}')
        self.area = QWidget(self)
        self.area_layout = QGridLayout()
        self.movie = QMovie('assets/Spinner-1s-200px.gif')
        self.label = QLabel(self.area)
        self.label.setMovie(self.movie)
        self.movie.start()
        self.area_layout.addWidget(self.label, 0, 0, 1, 1, Qt.AlignCenter)
        self.area.setLayout(self.area_layout)

    def resizeEvent(self, e):
        self.area.resize(self.width(), self.height())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load = LoadingScreen(self)

    def resizeEvent(self, e):
        print(self.width(), self.height())
        self.load.resize(self.width(), self.height())

    def do_stuff(self):
        thread = QThread(self)
        thread_1 = QThread(self)
        worker = Process()
        worker.moveToThread(thread)
        thread.started.connect(worker.do_long_stuff)
        worker.finished.connect(self.end)
        window = LoadingScreen()
        window.setFixedSize(1200, 800)
        window.show()
        thread.start()
        self.load = LoadingScreen(self)
        self.load.show()

    def end(self, var, var1):
        print('here', var, var1)
        self.load.hide()

app = QApplication([])
#app.processEvents()
#do_long_stuff()
window = MainWindow()
window.setFixedSize(1200, 800)
window.show()
window.do_stuff()
#splash.finish(window)
app.exec_()