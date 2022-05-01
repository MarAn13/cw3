import pandas
from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pandas as pd
import docx


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
    def __init__(self, result, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #292929; border-radius: 15px;}'
            '#file_area, #result_area, #scroll_widget{background-color: #3A3A3A; border-radius: 15px; color: #FFFFFF;}'
            'QLabel{color: #FFFFFF; background-color: purple;}'
            'QScrollBar{background-color: #3A3A3A; width: 20px; border-radius: 15px; color:#FFFFFF;}'
            'QTextEdit{background-color: #3A3A3A; border: 1px solid grey; color: #FFFFFF;}'
        )
        self.setFixedSize(1200, 800)
        self.video_ext = ['mp3', 'mp4', 'webm', 'mkv']  # should make a param in config file
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.file_area = QWidget(parent=self.area)
        self.file_area.setObjectName('file_area')
        self.file_area_widget = QWidget(parent=self.file_area)
        self.file_area_layout = QGridLayout()
        file_area_text = QLabel('Files', parent=self.file_area_widget)
        file_area_text.setMaximumHeight(self.height() / 4)
        file_area_text.setAlignment(Qt.AlignCenter)
        self.file_area_layout.addWidget(file_area_text, 0, 0, 1, 1)
        self.file_area_obj = []
        for i, (file, res) in enumerate(result.items()):
            if file.split('.')[-1] in self.video_ext:
                file_type = 'video'
            else:
                file_type = 'audio'
            self.file_area_obj.append(FileIconResult(file, file_type, res, parent=self.file_area_widget))
            temp = self.file_area_obj[-1]
            temp.setCursor(QCursor(Qt.PointingHandCursor))
            temp.clicked.connect(lambda _, arg=temp: self.show_result(arg))
            self.file_area_layout.addWidget(temp, i + 1, 0, 1, 1)
        self.current_obj = self.file_area_obj[0]
        self.file_area_widget.setLayout(self.file_area_layout)
        self.file_area_widget.setObjectName('scroll_widget')
        self.scroll = QScrollArea(self.file_area)  # parent=self.file_area)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.file_area_widget)
        self.result_area = QWidget(parent=self.area)
        self.result_area.setObjectName('result_area')
        self.result_display = QTextEdit(parent=self.result_area)
        self.result_display.setReadOnly(True)
        self.result_display.viewport().setCursor(QCursor(Qt.ArrowCursor))
        self.result_display.append('Result')
        self.result_display.setAlignment(Qt.AlignCenter)
        self.wer_input_area = QTextEdit(parent=self.result_area)
        self.wer_input_area.setPlaceholderText('Enter your original text')
        self.wer_input_area.textChanged.connect(self.update_wer)
        self.wer_display_area = QTextEdit(parent=self.result_area)
        self.wer_display_area.setReadOnly(True)
        self.wer_display_area.viewport().setCursor(QCursor(Qt.ArrowCursor))
        self.wer_display_area.append('WER:')
        self.process_widget = QWidget(parent=self.parent())
        self.process_widget.setObjectName('process_widget')
        self.current_obj.click()

    def show_result(self, widget):
        self.current_obj = widget
        self.result_display.clear()
        self.result_display.append('Result')
        self.result_display.setAlignment(Qt.AlignCenter)
        self.result_display.append('')
        self.result_display.append(self.current_obj.getResult())
        self.result_display.setAlignment(Qt.AlignLeft)
        self.wer_input_area.setText(self.current_obj.getWER())

    def update_wer(self):
        self.current_obj.setWER(self.wer_input_area.toPlainText())
        original_text = self.current_obj.getWER()
        pred_text = self.current_obj.getResult()
        print(original_text, pred_text)
        wer = '50'
        self.wer_display_area.setText(f'WER: {wer}%')

    def resizeEvent(self, e):
        self.area.resize(self.width(), self.height())
        self.file_area.setGeometry(self.area.width() * 0.05, self.area.height() * 0.1, self.area.width() * 0.3,
                                   self.area.height() * 0.80)
        self.result_area.setGeometry(self.file_area.x() + self.file_area.width() + self.area.width() * 0.05,
                                     self.area.height() * 0.1, self.area.width() * 0.55, self.area.height() * 0.80)
        self.result_display.setGeometry(0, 0, self.result_area.width(), self.result_area.height() * 0.6)
        self.wer_input_area.setGeometry(0, self.result_display.height(), self.result_area.width(), self.result_area.height() * 0.3)
        self.wer_display_area.setGeometry(0, self.wer_input_area.y() + self.wer_input_area.height(), self.result_area.width(), self.result_area.height() * 0.1)
        self.file_area_widget.resize(self.file_area.size())
        self.scroll.resize(self.file_area_widget.size())
        self.process_widget.setGeometry(self.area.x() + self.area.width() / 5, self.area.y() + self.area.height() + (
                self.parent().height() - (self.area.y() + self.area.height())) / 5, self.area.width() * 0.6,
                                        (self.parent().height() - (self.area.y() + self.area.height())) * 0.4)


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
    def __init__(self, text, filetype, result, parent=None):
        super().__init__(parent=parent)
        # self.setMinimumSize(675, 135)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.aspect = (5, 1)  # width / height
        self.text = text
        self.wer_text = None
        self.text_font = None
        self.filetype = filetype
        self.result = result
        # self.word_limit = 12
        self.word_limit = len(text)
        self.current_pos = 0
        # self.animation = True
        self.animation = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

    def getResult(self):
        return self.result

    def getWER(self):
        return self.wer_text

    def setWER(self, wer_text):
        self.wer_text = wer_text

    def setFont(self, font):
        self.text_font = font
        self.update()

    def resizeEvent(self, e):
        e_width = e.size().width()
        e_height = e.size().height()
        e_width_test = e_height / self.aspect[1] * self.aspect[0]
        if e_width_test > e_width:
            e_height = e_width / self.aspect[0] * self.aspect[1]
        else:
            e_width = e_width_test
        self.setFixedSize(e_width, e_height)
        # self.text_font = None
        # self.animation = True

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
            # if font.pointSize() > 8:
            #     self.animation = False
            if font.pointSize() < 10:
                self.animation = True
            while font.pointSize() < 10:
                self.word_limit -= 1
                font, step = resize_font(text_rect, painter.font(), text[:self.word_limit] + '..')
            font = painter.font()
            font.setPointSize(10)
            self.text_font = font
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


class ExportWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #252525; border-radius: 15px;}'
        )
        self.setObjectName('area')
        self.data = data
        self.pd_data = None
        self.area_layout = QGridLayout()
        self.button_excel = ResponsiveIconButton('assets/export_excel.svg', parent=self)
        self.button_excel.setCursor(QCursor(Qt.PointingHandCursor))
        self.button_excel.clicked.connect(lambda: self.export('excel'))
        self.button_word = ResponsiveIconButton('assets/export_word.svg', parent=self)
        self.button_word.setCursor(QCursor(Qt.PointingHandCursor))
        self.button_word.clicked.connect(lambda: self.export('word'))
        self.button_text = ResponsiveIconButton('assets/export_text.svg', parent=self)
        self.button_text.setCursor(QCursor(Qt.PointingHandCursor))
        self.button_text.clicked.connect(lambda: self.export('text'))
        self.button_excel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.button_word.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.button_text.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.button_excel, 0, 0, 1, 1)
        self.area_layout.addWidget(self.button_word, 0, 2, 1, 1)
        self.area_layout.addWidget(self.button_text, 0, 4, 1, 1)
        self.setLayout(self.area_layout)
        for i in range(self.area_layout.columnCount()):
            self.area_layout.setColumnStretch(i, 1)

    def export(self, mode):
        ext = {
            'excel': ['xlsx', 'csv'],
            'word': ['docx'],
            'text': ['txt']
        }
        file = QFileDialog.getSaveFileName(self, 'Save file', '',
                                           f'{mode[0].upper() + mode[1:]} ({" ".join("*." + i for i in ext[mode])})')
        if file == ('', ''):
            return
        else:
            file = file[0]
        if self.pd_data is None:
            self.pd_data = pd.DataFrame(self.data.items(), columns=['file', 'result'])
        if mode == 'excel':
            if file.split('.')[-1] == 'xlsx':
                self.pd_data.to_excel(file)
            else:
                self.pd_data.to_csv(file)
        elif mode == 'word':
            doc = docx.Document()
            table = doc.add_table(self.pd_data.shape[0], self.pd_data.shape[1])
            table_cells = table._cells
            for i in range(self.pd_data.shape[0]):
                for j in range(self.pd_data.shape[1]):
                    table_cells[j + i * self.pd_data.shape[1]].text = str(self.pd_data.values[i][j])
            doc.save(file)
        elif mode == 'text':
            with open(file, 'w') as f:
                max_width = max(len(key) for key in self.data.keys())
                for key, val in self.data.items():
                    f.write(f'{key.ljust(max_width + 1) + val}\n')


#
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.obj = ExportWidget(self)
#         self.obj.export.connect(self.test)
#         self.setCentralWidget(self.obj)


app = QApplication([])
# window = MainWindow()
# window = ExportWidget({'test': 'test', 'test11111111111111111111111111111': 'test1111111111111111',
#                        'test2': 'test222222222', 'test333333333': 'test333333'})
window = ResultWidget({'test.mp4': 'ereweve', 'test1.wav': 'refvbefwfvwefevwefv'})
# window = MainWindow()
# window = FileIconResult('file_icon_result_testing.mp4', 'video')  # testing_file_icon_result.mp4', 'video')
window.setFixedSize(1200, 800)
# obj.setGeometry(0, 0, 600, 400)
# window.setFixedSize(60, 150)
window.show()
app.exec_()
