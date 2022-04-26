from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class CustomAudioSvgWidget(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filepath = 'assets/audio_record_diamond.svg'
        self.aspect_ratio = (1, 1)
        self.max_background_offset = 0
        self.background_offset = self.max_background_offset
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def set_background_offset(self, offset):
        if offset < 0:
            offset = 0
        elif offset > self.max_background_offset:
            offset = self.max_background_offset
        self.background_offset = offset

    def get_background_offset(self):
        return self.background_offset

    def get_max_background_offset(self):
        return self.max_background_offset

    def paintEvent(self, e):
        painter = QPainter()
        painter.begin(self)
        painter.setPen(QColor('transparent'))
        e_point = 0
        if self.width() < self.height():
            e_point = self.width()
        else:
            e_point = self.height()
        self.max_background_offset = e_point * 0.15
        # bound rect
        painter.setBrush(QColor('blue'))
        painter.drawRect(self.width() / 2 - e_point / 2, self.height() / 2 - e_point / 2, e_point, e_point)
        grad = QLinearGradient()
        grad.setColorAt(0, QColor('#DA70D6'))
        grad.setColorAt(1, QColor('#7F00FF'))
        grad.setStart(self.width() / 2, self.height() / 2 - e_point / 4)
        grad.setFinalStop(self.width() / 2, self.height() / 2 + e_point / 4)
        painter.setBrush(grad)
        # offset_x, offset_y, w, h
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.drawEllipse(self.width() / 2 - (e_point - self.background_offset) / 2,
                            self.height() / 2 - (e_point - self.background_offset) / 2,
                            e_point - self.background_offset, e_point - self.background_offset)
        svg = QSvgRenderer(self.filepath)
        # offset_x, offset_y, w, h
        svg.render(painter,
                   QRectF(self.width() / 2 - e_point / 2, self.height() / 2 - e_point / 2, e_point, e_point))
        painter.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            '#area{background: grey;}'
        )
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.area_layout = QGridLayout()
        self.widget = CustomAudioSvgWidget(parent=self)
        self.widget.clicked.connect(self.test)
        self.widget.setCursor(QCursor(Qt.PointingHandCursor))
        self.widget_inc = -1
        self.area_layout.addWidget(self.widget)
        self.area.setLayout(self.area_layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_circle)
        self.timer.start(10)
        # self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        # self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # self.control_layout.addWidget(self.button)
        # self.control_layout.addWidget(self.slider)

    def test(self):
        print('yeap')

    def update_circle(self):
        current_offset = self.widget.get_background_offset()
        max_offset = self.widget.get_max_background_offset()
        if current_offset == 0:
            self.widget_inc = max_offset / 100
        elif current_offset == max_offset:
            self.widget_inc = -max_offset / 100
        self.widget.set_background_offset(current_offset + self.widget_inc)
        self.widget.update()

    def resizeEvent(self, e):
        self.area.setFixedSize(self.width(), self.height())


app = QApplication([])
window = MainWindow()
# window.setFixedSize(1200, 800)
window.setFixedSize(2000, 2000)
window.show()
app.exec_()
