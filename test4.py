from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


# def resize_font(widget):
#     # font setting
#     font = widget.font()
#     check = True
#     real_bound = widget.contentsRect()
#     last_inc = {
#         'val': font.pointSize() / 2,
#         'dir': 'none'
#     }
#     step = 0
#     while True:
#         if step > 100:
#             break
#         font_size = font.pointSize()
#         test_font = QFont(font)
#         test_font.setPointSize(font.pointSize() + 1)
#         test_bound = QFontMetrics(test_font).boundingRect(widget.text())
#         bound = QFontMetrics(font).boundingRect(widget.text())
#         if bound.width() > real_bound.width() or bound.height() > real_bound.height():
#             if last_inc['dir'] == 'up' or last_inc['dir'] == 'tilt':
#                 font.setPointSize(font_size - last_inc['val'])
#                 last_inc['val'] /= 2
#                 last_inc['dir'] = 'tilt'
#             else:
#                 font.setPointSize(font_size - font_size / 2)
#                 last_inc['val'] = abs(font.pointSize() - font_size)
#                 last_inc['dir'] = 'down'
#         elif test_bound.width() < real_bound.width() and test_bound.height() < real_bound.height():
#             if last_inc['dir'] == 'down' or last_inc['dir'] == 'tilt':
#                 font.setPointSize(font_size + last_inc['val'])
#                 last_inc['val'] /= 2
#                 last_inc['dir'] = 'tilt'
#             else:
#                 font.setPointSize(font_size + font_size / 2)
#                 last_inc['val'] = abs(font.pointSize() - font_size)
#                 last_inc['dir'] = 'up'
#         else:
#             break
#         step += 1
#     return font, step


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


class ResultWidget(QWidget):
    def __init__(self, files, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #292929; border-radius: 15px;}'
            '#file_area, #result_area{background-color: #3A3A3A; border-radius: 15px; color: #FFFFFF;}'
            'QLabel{color: #FFFFFF;}'
        )
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.area_layout = QGridLayout()
        self.file_area = QWidget(parent=self.area)
        self.file_area.setObjectName('file_area')
        self.file_area_layout = QVBoxLayout()
        file_area_text = QLabel('Files', parent=self.file_area)
        self.file_area_layout.addWidget(file_area_text, alignment=Qt.AlignCenter)
        for i in files:
            self.file_area_layout.addWidget(ResultFileIcon(i, i))
        self.file_area.setLayout(self.file_area_layout)
        # self.scroll_widget = QWidget(parent=self.file_area)
        self.scroll = QScrollArea()  # parent=self.file_area)
        self.scroll.setBackgroundRole(QPalette.Dark)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.file_area)
        # self.scroll.resize(self.file_area.size())
        self.result_area = QTextEdit(parent=self.area)
        self.result_area.setObjectName('result_area')
        self.result_area.setReadOnly(True)
        self.file_area.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.result_area.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.file_area, 0, 0, 1, 2)
        self.area_layout.addWidget(self.result_area, 0, 3, 1, 5)
        for i in range(self.area_layout.columnCount()):
            self.area_layout.setColumnStretch(i, 1)
        self.area.setLayout(self.area_layout)

    def resizeEvent(self, e):
        self.area.setFixedSize(self.width(), self.height())


def resize_font(el, font=None, text=None):
    # font setting
    if font is None:
        font = el.font()
        real_bound = el.contentsRect()
        text = el.text()
    else:
        real_bound = el
    check = True
    last_inc = {
        'val': font.pointSize() / 2,
        'dir': 'none'
    }
    step = 0
    while True:
        if step > 100:
            break
        font_size = font.pointSize()
        test_font = QFont(font)
        test_font.setPointSize(font.pointSize() + 1)
        test_bound = QFontMetrics(test_font).boundingRect(text)
        bound = QFontMetrics(font).boundingRect(text)
        if bound.width() > real_bound.width() or bound.height() > real_bound.height():
            if last_inc['dir'] == 'up' or last_inc['dir'] == 'tilt':
                font.setPointSize(font_size - last_inc['val'])
                last_inc['val'] /= 2
                last_inc['dir'] = 'tilt'
            else:
                font.setPointSize(font_size - font_size / 2)
                last_inc['val'] = abs(font.pointSize() - font_size)
                last_inc['dir'] = 'down'
        elif test_bound.width() < real_bound.width() and test_bound.height() < real_bound.height():
            if last_inc['dir'] == 'down' or last_inc['dir'] == 'tilt':
                font.setPointSize(font_size + last_inc['val'])
                last_inc['val'] /= 2
                last_inc['dir'] = 'tilt'
            else:
                font.setPointSize(font_size + font_size / 2)
                last_inc['val'] = abs(font.pointSize() - font_size)
                last_inc['dir'] = 'up'
        else:
            break
        step += 1
    return font, step


class FileIconResult(QPushButton):
    def __init__(self, text, filetype, parent=None):
        super().__init__(parent=parent)
        self.aspect = (4, 1)  # width / height
        self.text = text
        self.text_font = None
        self.filetype = filetype
        self.word_limit = 12
        self.current_pos = 0
        self.animation = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

    def resizeEvent(self, e):
        e_width = e.size().width()
        e_height = e.size().height()
        e_width_test = e_height / self.aspect[1] * self.aspect[0]
        if e_width_test > e_width:
            e_height = e_width / self.aspect[0] * self.aspect[1]
        else:
            e_width = e_width_test
        self.setFixedSize(e_width, e_height)
        self.text_font = None
        self.animation = True

    def paintEvent(self, e):
        painter = QPainter()
        painter.begin(self)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        painter.fillPath(path, QColor('#454545'))
        if self.filetype == 'video':
            svg = QSvgRenderer('assets/video_file_icon.svg')
        else:
            svg = QSvgRenderer('assets/audio_file_icon.svg')
        painter.fillRect(QRectF(0, 0, self.height(), self.height()), QColor('red'))
        svg_size = QSize(self.height() / 1.5, self.height() / 1.5)
        svg.render(painter, QRectF(self.height() / 2 - svg_size.width() / 2, self.height() / 2 - svg_size.height() / 2,
                                   svg_size.width(), svg_size.height()))
        text_rect = QRectF(self.height(), 0, self.width() - self.height(), self.height())
        text = self.text
        option = QStyleOptionButton()
        option.initFrom(self)
        if self.text_font is None:
            font, step = resize_font(text_rect, painter.font(), text)
            if font.pointSize() > 15:
                self.animation = False
        if option.state & QStyle.State_MouseOver and self.animation:
            text = self.text[self.current_pos:self.current_pos + self.word_limit]
            if len(text) < self.word_limit:
                word_diff = self.word_limit - len(text)
                spacer = min(word_diff, 2)
                text += ' ' * spacer
                word_diff -= spacer
                text += self.text[0:word_diff]
            self.current_pos += 1
            if self.current_pos > len(self.text):
                self.current_pos = 0
            if not self.timer.isActive():
                self.timer.start(250)
        else:
            if self.timer.isActive():
                self.timer.stop()
            if self.animation:
                text = self.text[:self.word_limit] + '..'
            self.current_pos = 0
        if self.text_font is None:
            font, step = resize_font(text_rect, painter.font(), text)
            self.text_font = font
        painter.setFont(self.text_font)
        painter.setPen(QColor('#FFFFFF'))
        painter.fillRect(text_rect, QColor('blue'))
        painter.drawText(text_rect, Qt.AlignCenter, text)
        painter.end()


app = QApplication([])
# window = ResultWidget(['assets/audio_file_icon.svg'])
# window = MainWindow()
window = FileIconResult('file_icon_result_testing.mp4', 'video')  # testing_file_icon_result.mp4', 'video')
window.setFixedSize(675, 150)
window.show()
app.exec_()
