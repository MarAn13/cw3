"""
Classes with responsive icons
"""
from PyQt5.QtWidgets import QComboBox, QPushButton, QStyle, QStyleOptionButton
from PyQt5.Qt import Qt
from PyQt5.QtCore import QRectF, QSize, QSizeF, pyqtSignal
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QLinearGradient, QCursor
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from ui_utils import resize_font


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
        self.brush_color = QColor('#252525')
        self.border_color = 'transparent'
        self.border_state = True

    def setSVG(self, filepath):
        self.filepath = filepath
        self.update()

    def setBrushColor(self, color):
        self.brush_color = QColor(color)
        self.update()

    def setBorderColor(self, color):
        self.border_color = color
        self.update()

    def setBorderState(self, state):
        self.border_state = state
        self.update()

    def paintEvent(self, e):
        option = QStyleOptionButton()
        option.initFrom(self)
        if option.state & QStyle.State_MouseOver or not self.border_state:
            brush_color = QColor('#323232')
        else:
            brush_color = self.brush_color
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
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


class CustomComboBox(QComboBox):
    changed_item = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimumHeight(230)
        self.top_text = 'GUI'
        self.text = 'HELLO'
        self.box_area = None
        self.items = []
        self.params = {
            'drop-down-menu': False,
            'current-item': None,
            'hover-item': None
        }
        self.setMouseTracking(True)

    def contains(self, rect, e):
        if rect.x() <= e.x() <= rect.x() + rect.width() and rect.y() <= e.y() <= rect.y() + rect.height():
            return True
        return False

    def mouseMoveEvent(self, e):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        if self.contains(self.box_area, e):
            self.params['hover-item'] = -1
        elif self.params['drop-down-menu']:
            for i, item in enumerate(self.items):
                if self.contains(item, e):
                    self.params['hover-item'] = i
                    break
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
            self.params['hover-item'] = None
        self.update()

    def mousePressEvent(self, e):
        if self.contains(self.box_area, e):
            if self.params['drop-down-menu']:
                self.params['drop-down-menu'] = False
            else:
                self.params['drop-down-menu'] = True
        for i, item in enumerate(self.items):
            if self.contains(item, e):
                if self.params['current-item'] != i:
                    self.changed_item.emit(self.itemText(i))
                self.params['current-item'] = i
                break
        self.update()

    def paintEvent(self, e):
        painter = QPainter()
        painter.begin(self)
        box_size = QSizeF(self.width(), self.height() / 3)
        top_text_geometry = QRectF(10, 0, self.width(), box_size.height() * 0.3)
        font, step = resize_font(top_text_geometry, painter.font(), self.top_text)
        font.setUnderline(True)
        painter.setFont(font)
        pen = painter.pen()
        pen.setColor(QColor('#FFFFFF'))
        painter.setPen(pen)
        painter.drawText(top_text_geometry, self.top_text)
        self.box_area = QRectF(0, top_text_geometry.height(), box_size.width(), box_size.height())
        path = QPainterPath()
        path.addRoundedRect(self.box_area, 15, 15)
        if self.params['hover-item'] == -1:
            color = QColor('#363636')
        else:
            color = QColor('#292929')
        painter.fillPath(path, color)
        svg = QSvgRenderer('../assets/combobox_arrow_down.svg')
        svg_size = QSizeF(box_size.height() / 2, box_size.height() / 2)
        svg_geometry = QRectF(box_size.width() - svg_size.width(),
                              self.box_area.y() + box_size.height() - svg_size.height() - 15,
                              svg_size.width(), svg_size.height())
        svg.render(painter, svg_geometry)
        text_size = QSizeF(box_size.width() - svg_size.width(), box_size.height() / 2)
        font, step = resize_font(text_size, painter.font(), self.text)
        font.setUnderline(False)
        painter.setFont(font)
        painter.drawText(QRectF(10, self.box_area.y() + box_size.height() - text_size.height() - 15, text_size.width(),
                                text_size.height()),
                         self.text)
        if self.params['drop-down-menu']:
            item_size = QSizeF(self.width(), (self.height() - box_size.height() - self.box_area.y()) / self.count())
            font = painter.font()
            font.setPointSize(font.pointSize() - 2)
            self.items = []
            for i in range(self.count()):
                rect = QRectF(0, self.box_area.y() + box_size.height() - 15 + item_size.height() * i, item_size.width(),
                              item_size.height())
                if self.params['current-item'] == i:
                    color = QColor('green')
                elif self.params['hover-item'] == i:
                    color = QColor('#363636')
                else:
                    color = QColor('#292929')
                painter.fillRect(rect, color)
                painter.drawRect(rect)
                self.items.append(rect)
                text = self.itemText(i)
                rect_text = rect
                rect_text.setX(rect_text.x() + 10)
                rect_text.setY(rect_text.y() + (item_size.height() - text_size.height()) / 2)
                painter.setFont(font)
                painter.drawText(rect, text)
        painter.end()

    def resizeEvent(self, e):
        print(e.size())
