"""
Display resulting output (after model prediction)
"""
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QScrollArea, QTextEdit, QGridLayout, QSizePolicy, QFileDialog, \
    QStyle, QStyleOptionButton, QGraphicsOpacityEffect, QLineEdit
from PyQt5.Qt import Qt
from PyQt5.QtGui import QCursor, QPainter, QPainterPath, QColor, QMovie, QRegExpValidator
from PyQt5.QtCore import QTimer, QSize, QRectF, QObject, pyqtSignal, QRegExp
from PyQt5.QtSvg import QSvgRenderer
from ui_utils import resize_font
from responsive_svg import ResponsiveIconButton
from utils import predict, process_convert, compute_wer, get_from_file, change_file
import pandas as pd
import openpyxl
import docx


class LoadingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.finish)
        self.opacity = 0.7
        self.area = QWidget(self)
        self.area_layout = QGridLayout()
        self.area_layout.setContentsMargins(0, 0, 0, 0)
        self.movie = QMovie('../assets/loading.gif')
        self.label = QLabel(self.area)
        self.label.setMovie(self.movie)
        self.movie.start()
        self.area_layout.addWidget(self.label, 0, 0, 1, 1, Qt.AlignCenter)
        self.area.setLayout(self.area_layout)

    def finish(self):
        self.timer.start(250)

    def eclipse(self):
        temp = QGraphicsOpacityEffect()
        self.opacity -= 0.1
        temp.setOpacity(self.opacity)
        self.setGraphicsEffect(temp)
        if self.opacity == 0:
            self.timer.stop()

    def resizeEvent(self, e):
        self.area.resize(self.width(), self.height())
        self.movie.setScaledSize(self.size())


class ResultProcess(QObject):
    finished = pyqtSignal(dict, str)

    def __init__(self, files, mode, SNR):
        super().__init__()
        self.files = files
        self.mode = mode
        self.SNR = SNR

    def process(self):
        # preprocess - dictionary {file: [filepath, filepath]}
        preprocess = process_convert(self.files, self.mode, self.SNR)
        result = predict(preprocess, self.mode)
        print(result)
        # return {file: result}
        self.finished.emit(result, self.mode)


class ResultWidget(QWidget):
    def __init__(self, result, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #292929; border-radius: 15px;}'
            '#file_area, #result_area, #scroll_widget{background-color: #3A3A3A; border-radius: 15px; color: #FFFFFF;}'
            'QLabel{color: #FFFFFF;}'
            'QScrollBar{background-color: #3A3A3A; width: 20px; border-radius: 15px; color:#FFFFFF;}'
            'QTextEdit, QLineEdit{background-color: #3A3A3A; border: 1px solid grey; color: #FFFFFF;}'
        )
        self.video_ext = ['mp3', 'mp4', 'webm', 'mkv', 'wmv', 'avi', 'mov', 'flv']  # should make a param in config file
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.file_area = QWidget(parent=self.area)
        self.file_area.setObjectName('file_area')
        self.file_area_widget = QWidget(parent=self.file_area)
        self.file_area_layout = QGridLayout()
        self.file_area_text = QLabel('Files', parent=self.file_area_widget)
        self.file_area_text.setAlignment(Qt.AlignCenter)
        self.file_area_layout.addWidget(self.file_area_text, 0, 0, 1, 1)
        self.file_area_obj = []
        for i, (file, res) in enumerate(result.items()):
            self.file_area_obj.append(FileIconResult(file, res[0], res[1], parent=self.file_area_widget))
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
        self.wer_input_area = QLineEdit(parent=self.result_area)
        self.wer_input_area.setPlaceholderText('Enter your original text')
        self.wer_input_area.setValidator(QRegExpValidator(QRegExp("[A-Za-z ']*")))
        self.wer_input_area.textChanged.connect(self.update_wer)
        self.wer_display_area = QTextEdit(parent=self.result_area)
        self.wer_display_area.setReadOnly(True)
        self.wer_display_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wer_display_area.viewport().setCursor(QCursor(Qt.ArrowCursor))
        self.wer_display_area.append('WER:')
        self.export_widget = self.parent().parent().render_export_widget(None)
        self.update_export()
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
        self.current_obj.setOriginal(self.wer_input_area.text().strip())
        original_text = self.current_obj.getOriginal()
        pred_text = self.current_obj.getResult()
        if len(original_text) > 0 and len(pred_text) > 0:
            wer = compute_wer(original_text, pred_text)
            data = get_from_file('data.txt', '')
            mode = self.current_obj.getFiletype()
            param_samples = mode[0].upper() + mode[1:] + ' samples'
            param_WER = mode[0].upper() + mode[1:] + ' WER'
            data[param_samples] = int(data[param_samples])
            data[param_WER] = float(data[param_WER])
            if self.current_obj.getWER() is not None:
                data[param_samples] -= 1
                data[param_WER] -= self.current_obj.getWER()
            data[param_samples] += 1
            data[param_WER] += wer
            for param, param_val in [[param_samples, data[param_samples]], [param_WER, data[param_WER]]]:
                change_file('data.txt', param, param_val)
            self.current_obj.setWER(wer)
            wer = "{:.2f}".format(wer)
        else:
            wer = '..'
        self.update_export()
        self.wer_display_area.setText(f'WER: {wer}%')

    def update_export(self):
        info = []
        for i in self.file_area_obj:
            info.append([i.getFile(), i.getOriginal(), i.getResult(), i.getWER()])
        self.export_widget.setData(info)

    def resizeEvent(self, e):
        self.area.resize(self.width(), self.height())
        self.file_area.setGeometry(self.area.width() * 0.05, self.area.height() * 0.1, self.area.width() * 0.3,
                                   self.area.height() * 0.80)
        self.file_area_text.setMaximumHeight(self.height() * 0.25)
        self.result_area.setGeometry(self.file_area.x() + self.file_area.width() + self.area.width() * 0.05,
                                     self.area.height() * 0.1, self.area.width() * 0.55, self.area.height() * 0.80)
        self.result_display.setGeometry(0, 0, self.result_area.width(), self.result_area.height() * 0.6)
        self.wer_input_area.setGeometry(0, self.result_display.height(), self.result_area.width(),
                                        self.result_area.height() * 0.3)
        self.wer_display_area.setGeometry(0, self.wer_input_area.y() + self.wer_input_area.height(),
                                          self.result_area.width(), self.result_area.height() * 0.1)
        self.file_area_widget.resize(self.file_area.size())
        self.scroll.resize(self.file_area_widget.size())
        # self.process_widget.setGeometry(self.area.x() + self.area.width() / 5, self.area.y() + self.area.height() + (
        #         self.parent().height() - (self.area.y() + self.area.height())) / 5, self.area.width() * 0.6,
        #                                 (self.parent().height() - (self.area.y() + self.area.height())) * 0.4)


class FileIconResult(QPushButton):
    def __init__(self, file, filetype, result, parent=None):
        super().__init__(parent=parent)
        # self.setMinimumSize(675, 135)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.aspect = (5, 1)  # width / height
        self.file = file
        self.filename = ''.join(file.split('\\')[-1])
        self.wer = None
        self.text_font = None
        self.filetype = filetype
        self.original = ''
        self.result = result
        # self.word_limit = 12
        self.word_limit = len(self.filename)
        self.current_pos = 0
        # self.animation = True
        self.animation = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

    def getFile(self):
        return self.file

    def getFilename(self):
        return self.filename

    def getFiletype(self):
        return self.filetype

    def getOriginal(self):
        return self.original

    def setOriginal(self, original):
        self.original = original

    def getResult(self):
        return self.result

    def getWER(self):
        return self.wer

    def setWER(self, wer):
        self.wer = wer

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
        if self.filetype != 'audio-only':
            svg = QSvgRenderer('../assets/video_file_icon.svg')
        else:
            svg = QSvgRenderer('../assets/audio_file_icon.svg')
        svg_size = QSize(self.height() / 1.5, self.height() / 1.5)
        svg.render(painter, QRectF(self.height() / 2 - svg_size.width() / 2, self.height() / 2 - svg_size.height() / 2,
                                   svg_size.width(), svg_size.height()))
        text_rect = QRectF(self.height(), 0, self.width() - self.height(), self.height())
        text = self.filename
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
            text = self.filename[self.current_pos:self.current_pos + self.word_limit]
            if len(text) < self.word_limit:
                word_diff = self.word_limit - len(text)
                spacer = min(word_diff, 2)
                text += ' ' * spacer
                word_diff -= spacer
                text += self.filename[0:word_diff]
            self.current_pos += 1
            if self.current_pos > len(self.filename):
                self.current_pos = 0
            if not self.timer.isActive():
                self.timer.start(250)
        else:
            if self.timer.isActive():
                self.timer.stop()
            if self.animation:
                text = self.filename[:self.word_limit] + '..'
            self.current_pos = 0
        if self.text_font is None:
            font, step = resize_font(text_rect, painter.font(), text)
            self.text_font = font
        painter.setFont(self.text_font)
        painter.setPen(QColor('#FFFFFF'))
        painter.drawText(text_rect, Qt.AlignCenter, text)
        painter.end()


class ExportWidget(QWidget):
    def __init__(self, data=None, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #252525; border-radius: 15px;}'
        )
        self.data = data
        self.pd_data = None
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.area_layout = QGridLayout()
        self.button_excel = ResponsiveIconButton('../assets/export_excel.svg', parent=self.area)
        self.button_excel.setCursor(QCursor(Qt.PointingHandCursor))
        self.button_excel.clicked.connect(lambda: self.export('excel'))
        self.button_word = ResponsiveIconButton('../assets/export_word.svg', parent=self.area)
        self.button_word.setCursor(QCursor(Qt.PointingHandCursor))
        self.button_word.clicked.connect(lambda: self.export('word'))
        self.button_text = ResponsiveIconButton('../assets/export_text.svg', parent=self.area)
        self.button_text.setCursor(QCursor(Qt.PointingHandCursor))
        self.button_text.clicked.connect(lambda: self.export('text'))
        self.button_excel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.button_word.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.button_text.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.button_excel, 0, 0, 1, 1)
        self.area_layout.addWidget(self.button_word, 0, 2, 1, 1)
        self.area_layout.addWidget(self.button_text, 0, 4, 1, 1)
        self.area.setLayout(self.area_layout)
        for i in range(self.area_layout.columnCount()):
            self.area_layout.setColumnStretch(i, 1)

    def setData(self, data):
        self.data = data

    def export(self, mode):
        ext = {
            'excel': ['xlsx', 'csv'],
            'word': ['docx'],
            'text': ['txt']
        }
        file = QFileDialog.getSaveFileName(
            self,
            'Save file',
            '',
            f'{mode[0].upper() + mode[1:]} ({" ".join("*." + i for i in ext[mode])})'
        )
        if file == ('', ''):
            return
        else:
            file = file[0]
        self.pd_data = pd.DataFrame(self.data, columns=['file', 'original', 'pred', 'wer'])
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
                max_width = max(len(file[0]) for file in self.data)
                for file, original, pred, wer in self.data:
                    if wer is None:
                        wer = ''
                    f.write(f'{file.ljust(max_width + 1) + " | " + original + " | " + pred + " | " + wer}\n')

    def resizeEvent(self, e):
        self.area.resize(self.width(), self.height())
