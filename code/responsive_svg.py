"""
Classes with responsive icons
"""
from PyQt5.QtWidgets import QPushButton, QStyle, QStyleOptionButton
from PyQt5.Qt import Qt
from PyQt5.QtCore import QRectF, QSize
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QLinearGradient
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer


class SvgWidgetAspect(QSvgWidget):
    def __init__(self, filepath, aspect_ratio, clickable=False, parent=None):
        super().__init__(parent=parent)
        self.aspect_ratio = aspect_ratio
        self.clickable = clickable
        self.click_event = None
        self.load(filepath)

    def resizeEvent(self, e):
        e_width = e.size().width()
        e_height = e.size().height()
        if e_width < e_height:
            e_point = e_width / self.aspect_ratio[0]
        else:
            e_point = e_height / self.aspect_ratio[1]
        self.setFixedSize(e_point * self.aspect_ratio[0], e_point * self.aspect_ratio[1])

    def setClickable(self, state):
        self.clickable = state

    def connect(self, func):
        if self.clickable:
            self.click_event = func

    def mousePressEvent(self, e):
        if self.clickable and self.click_event:
            self.click_event()


class CustomAudioSvgWidget(SvgWidgetAspect):
    filepath = '../assets/audio_record_diamond.svg'
    aspect_ratio = (1, 1)

    def __init__(self, parent=None):
        super().__init__(self.filepath, self.aspect_ratio, True, parent)
        self.max_background_offset = 0
        self.background_offset = self.max_background_offset

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
        if self.width() < self.height():
            e_point = self.width()
        else:
            e_point = self.height()
        self.max_background_offset = e_point * 0.15
        # bound rect
        # painter.setBrush(QColor('blue'))
        # painter.drawRect(self.width() / 2 - e_point / 2, self.height() / 2 - e_point / 2, e_point, e_point)
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
        # offset_x, offset_y, w, h
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
