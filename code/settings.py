from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QComboBox, QLineEdit, QGridLayout, QCheckBox, \
    QSizePolicy
from PyQt5.Qt import Qt
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QCursor
from PyQt5.QtCore import QRectF, QSizeF, pyqtSignal
from PyQt5.QtSvg import QSvgRenderer
from ui_utils import resize_font
from utils import change_file, get_from_file


class CustomComboBox(QComboBox):
    item_changed = pyqtSignal(str, str)

    def __init__(self, title, top_title=None, parent=None):
        super().__init__(parent=parent)
        self.setMinimumHeight(230)
        self.top_text = top_title
        self.text = title
        self.box_area = None
        self.items = []
        self.params = {
            'drop-down-menu': False,
            'current-item': None,
            'hover-item': None
        }
        self.setMouseTracking(True)

    def get_title(self):
        return self.text

    def contains(self, rect, e):
        if rect.x() <= e.x() <= rect.x() + rect.width() and rect.y() <= e.y() <= rect.y() + rect.height():
            return True
        return False

    def setCurrentIndex(self, index):
        self.params['current-item'] = index

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
                    self.item_changed.emit(self.text, self.itemText(i))
                self.params['current-item'] = i
                break
        self.update()

    def paintEvent(self, e):
        painter = QPainter()
        painter.begin(self)
        box_size = QSizeF(self.width(), self.height() / 3)
        if self.top_text is not None:
            top_text_geometry = QRectF(10, 0, self.width(), box_size.height() * 0.3)
            font, step = resize_font(top_text_geometry, painter.font(), self.top_text)
            font.setUnderline(True)
            painter.setFont(font)
            pen = painter.pen()
            pen.setColor(QColor('#FFFFFF'))
            painter.setPen(pen)
            painter.drawText(top_text_geometry, self.top_text)
            self.box_area = QRectF(0, top_text_geometry.height(), box_size.width(), box_size.height())
        else:
            self.box_area = QRectF(0, 0, box_size.width(), box_size.height())
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
        pen = painter.pen()
        pen.setColor(QColor('#FFFFFF'))
        painter.setPen(pen)
        painter.drawText(QRectF(10, self.box_area.y() + box_size.height() - text_size.height() - 15, text_size.width(),
                                text_size.height()),
                         self.text)
        if self.params['drop-down-menu'] and self.count():
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


class SettingsWidget(QWidget):
    config_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            # 'background-color:blue;'
            'QCheckBox{background-color: #292929; color: #FFFFFF; border-radius: 15px;}'
            'QCheckBox:hover{background-color: #363636;}'
            'QCheckBox::indicator{width: 10px; height: 10px; background-color: #FFFFFF;}'
            'QCheckBox::indicator::checked{image: url(../assets/radio_button_indicator.svg);}'
        )
        self.area_layout = QGridLayout()
        self.combo_res = CustomComboBox('Resolution', 'GUI', parent=self)
        self.combo_res.item_changed.connect(self.change_config)
        self.combo_res.addItem('1080 x 768')
        self.combo_res.addItem('1440 x 1024')
        self.combo_res.addItem('2160 x 1536')
        self.combo_dec = CustomComboBox('Decoder', 'Neural network', parent=self)
        self.combo_dec.item_changed.connect(self.change_config)
        self.combo_dec.addItem('greedy')
        self.combo_dec.addItem('search')
        self.combo_audio = CustomComboBox('Audio SNR', parent=self)
        self.combo_audio.item_changed.connect(self.change_config)
        self.combo_audio.addItem('0')
        self.combo_audio.addItem('100')
        self.combo_video = CustomComboBox('Video SNR', parent=self)
        self.combo_video.item_changed.connect(self.change_config)
        self.combo_video.addItem('0')
        self.combo_video.addItem('100')
        self.check_noise = QCheckBox('Use noise', parent=self)
        self.check_noise.stateChanged.connect(lambda state: self.change_config(self.check_noise.text(), bool(state)))
        self.check_noise.setCursor(QCursor(Qt.PointingHandCursor))
        self.check_lm = QCheckBox('Use LM', parent=self)
        self.check_lm.stateChanged.connect(lambda state: self.change_config(self.check_lm.text(), bool(state)))
        self.check_lm.setCursor(QCursor(Qt.PointingHandCursor))
        self.check_noise.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.check_lm.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.combo_res, 0, 0, 4, 1)
        self.area_layout.addWidget(self.combo_dec, 4, 0, 4, 1)
        self.area_layout.addWidget(self.check_noise, 4, 1, 2, 1)
        self.area_layout.addWidget(self.check_lm, 4, 2, 2, 1)
        self.area_layout.addWidget(self.combo_audio, 8, 1, 4, 1)
        self.area_layout.addWidget(self.combo_video, 12, 1, 4, 1)
        self.setLayout(self.area_layout)
        self.check_active()

    def check_active(self):
        config = get_from_file('config.txt', '')
        for i in [self.combo_res, self.combo_dec, self.combo_audio, self.combo_video]:
            i.setCurrentIndex(i.findText(config[i.get_title()]))

    def change_config(self, param, param_val):
        if change_file('config.txt', param, param_val):
            self.config_changed.emit()