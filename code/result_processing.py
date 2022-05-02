class ResultWidget(QWidget):
    def __init__(self, files, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area, #process_widget{background-color: #292929; border-radius: 15px;}'
            '#file_area, #result_area, #scroll_widget{background-color: #3A3A3A; border-radius: 15px; color: #FFFFFF;}'
            'QLabel{color: #FFFFFF; background-color: purple;}'
            'QScrollBar{background-color: #3A3A3A; width: 20px; border-radius: 15px; color:#FFFFFF;}'
        )
        # self.setFixedSize(1200, 800)
        self.process_widget = QWidget(parent=self.parent())
        self.process_widget.setObjectName('process_widget')
        self.process_widget_layout = QGridLayout()
        self.process_widget_button_excel = QPushButton('Excel', parent=self.process_widget)
        self.process_widget_button_word = QPushButton('Word', parent=self.process_widget)
        self.process_widget_button_text = QPushButton('Text', parent=self.process_widget)
        self.process_widget_layout.addWidget(self.process_widget_button_excel, 0, 0, 1, 1)
        self.process_widget_layout.addWidget(self.process_widget_button_word, 0, 1, 1, 1)
        self.process_widget_layout.addWidget(self.process_widget_button_text, 0, 2, 1, 1)
        self.process_widget.setLayout(self.process_widget_layout)
        self.process_widget.setAutoFillBackground(True)
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
        for i, file in enumerate(files):
            self.file_area_obj.append(FileIconResult(file, 'video', str(i), parent=self.file_area_widget))
            temp = self.file_area_obj[-1]
            temp.setCursor(QCursor(Qt.PointingHandCursor))
            temp.clicked.connect(lambda _, arg=temp: self.show_result(arg))
            self.file_area_layout.addWidget(temp, i + 1, 0, 1, 1)
        self.file_area_widget.setLayout(self.file_area_layout)
        self.file_area_widget.setObjectName('scroll_widget')
        self.scroll = QScrollArea(self.file_area)  # parent=self.file_area)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.file_area_widget)
        self.result_area = QTextEdit(parent=self.area)
        self.result_area.setObjectName('result_area')
        self.result_area.setReadOnly(True)
        self.result_area.append('Result')
        self.result_area.setAlignment(Qt.AlignCenter)

    def show_result(self, widget):
        self.result_area.clear()
        self.result_area.append('Result')
        self.result_area.setAlignment(Qt.AlignCenter)
        self.result_area.append('')
        self.result_area.append(widget.getResult())
        self.result_area.setAlignment(Qt.AlignLeft)

    def resizeEvent(self, e):
        self.area.resize(self.width(), self.height())
        self.file_area.setGeometry(self.area.width() * 0.05, self.area.height() * 0.1, self.area.width() * 0.3,
                                   self.area.height() * 0.80)
        self.result_area.setGeometry(self.file_area.x() + self.file_area.width() + self.area.width() * 0.05,
                                     self.area.height() * 0.1, self.area.width() * 0.55, self.area.height() * 0.80)
        self.file_area_widget.resize(self.file_area.size())
        self.scroll.resize(self.file_area_widget.size())
        # self.process_widget.setGeometry(345, 820, 600, 150)
        self.process_widget.setGeometry(self.x() + self.width() / 5, self.y() + self.height() + (
                    self.parent().height() - (self.y() + self.height())) * 0.2, self.width() * 0.6,
                                        (self.parent().height() - (self.y() + self.height())) * 0.6)


    def showEvent(self, e):
        self.show()
        self.process_widget.show()

class FileIconResult(QPushButton):
    def __init__(self, text, filetype, result, parent=None):
        super().__init__(parent=parent)
        # self.setMinimumSize(675, 135)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.aspect = (5, 1)  # width / height
        self.text = text
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