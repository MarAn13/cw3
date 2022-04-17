from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            'QLabel{background-color: grey;}'

        )
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer(self, QMediaPlayer.VideoSurface)
        self.button = QPushButton('Play')
        self.button.clicked.connect(self.play)
        self.slider = QSlider(Qt.Horizontal)
        self.media_player.setVideoOutput(self.video_widget)
        self.area = QLabel(self)
        self.area_layout = QGridLayout()
        self.control_layout = QHBoxLayout()
        # self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile('record.mp4')))
        # self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        # self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # self.control_layout.addWidget(self.button)
        # self.control_layout.addWidget(self.slider)
        self.area_layout.addWidget(self.video_widget, 0, 0, 1, 4)
        self.area_layout.addWidget(self.button, 1, 0)
        self.area_layout.addWidget(self.slider, 1, 1)
        # self.area_layout.addLayout(self.control_layout, 1, 0)
        self.area.setLayout(self.area_layout)

    def play(self):
        print(self.media_player.state(), self.media_player.mediaStatus(), self.media_player.error())
        self.media_player.play()

    def resizeEvent(self, e):
        self.area.setGeometry(100, 100, self.width() / 2, self.height() / 2)


app = QApplication([])
window = MainWindow()
window.setFixedSize(1200, 800)
window.show()
app.exec_()
