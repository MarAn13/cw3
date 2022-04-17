from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            'QLabel{background-color: grey;}'
            '#test1, #test2{background-color: red;}'
            'QSlider{margin: 0px;}'
            'QSlider::groove:horizontal{border-radius: 5px; height: 18px; margin: 20px 0px 20px 0px; background-color: yellow;}'
            'QSlider::handle:horizontal{border: none; height: 20px; width: 20px; margin: -14px 0; border-radius: 5px; background-color: blue;}'
            'QSlider::sub-page:horizontal{border-radius: 5px; margin: 20px 0px 20px 0px; background: purple;}'
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
        self.media_elapsed_time = QLabel('Elapsed', self.area)
        self.media_elapsed_time.setObjectName('test1')
        self.media_remained_time = QLabel('Remained', self.area)
        self.media_remained_time.setObjectName('test2')
        self.media_elapsed_time.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.media_remained_time.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.video_widget, 0, 0, 8, 10)
        self.area_layout.addWidget(self.media_elapsed_time, 8, 0, 1, 1)
        self.area_layout.addWidget(self.slider, 8, 1, 1, 8)
        self.area_layout.addWidget(self.media_remained_time, 8, 9)
        self.area_layout.addWidget(self.button, 9, 0, 1, 1)
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
