from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class ResponsiveIconButton(QPushButton):
    def __init__(self, svg_path, parent=None):
        super().__init__(parent=parent)
        self.filepath = svg_path
        self.border_color = 'transparent'
        self.border_state = True
        self.resize(self.width(), self.height())

    def setBorderColor(self, color):
        self.border_color = color

    def setBorderState(self, state):
        self.border_state = state
        self.update()

    def paintEvent(self, e):
        option = QStyleOptionButton()
        option.initFrom(self)
        if option.state & QStyle.State_MouseOver:
            brush_color = QColor('#323232')
        else:
            brush_color = QColor('#252525')
        painter = QPainter()
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.begin(self)
        # self.width() / 6 = 14 for initial size where 6 is desired border width
        pen = QPen(QColor(self.border_color), self.width() / 14, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(brush_color)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        painter.fillPath(path, painter.brush())
        if self.border_state:
            painter.drawPath(path)
        svg = QSvgRenderer(self.filepath)
        it = QGraphicsItem()
        # offset_x, offset_y, w, h
        # painter.rotate(45)
        # painter.translate(self.width(), 0)
        svg_size = QSize(self.width() / 2, self.height() / 2)
        svg.render(painter, QRectF(self.width() / 2 - svg_size.width() / 2, self.height() / 2 - svg_size.height() / 2,
                                   svg_size.width(), svg_size.height()))
        painter.end()

    def resizeEvent(self, e):
        e_width = e.size().width()
        e_height = e.size().height()
        if e_width < e_height:
            e_point = e_width
        else:
            e_point = e_height
        self.setFixedSize(e_point, e_point)


class Test(QWidget):
    def __init__(self):
        super().__init__()

    def paintEvent(self, e):
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(0, 0, self.width(), self.height(), QColor('black'))
        painter.fillRect(self.width() / 2 - 100, self.height() / 2 - 50, 200, 100, QColor('white'))
        # painter.translate(self.width() / 2, self.height() / 2)
        # painter.rotate(90)
        # painter.translate(self.height() - 200, 0)
        # painter.fillRect(0, 0, 200, 100, QColor('purple'))
        # painter.fillRect(0, 0, self.width(), self.height(), QColor('red'))
        painter.fillRect(self.width() / 2 - 100, self.height() / 2 - 50, 200, 100, QColor('blue'))
        painter.end()

    def resizeEvent(self, e):
        self.setFixedSize(e.size())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.area = QWidget(self)
        self.area_layout = QGridLayout()
        self.obj = ResponsiveIconButton('assets/audio_record.svg', self.area)
        # self.obj = Test()
        self.obj.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.obj)
        self.area.setLayout(self.area_layout)

    def resizeEvent(self, e):
        self.area.setFixedSize(e.size())


app = QApplication([])
window = MainWindow()
# window.setFixedSize(1200, 800)
window.setFixedSize(1000, 1000)
window.show()
app.exec_()
