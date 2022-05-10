"""
Processing file uploads
"""
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QScrollArea, QGridLayout, QVBoxLayout, QFileDialog, \
    QSizePolicy
from PyQt5.Qt import Qt
from PyQt5.QtGui import QPalette, QCursor
from PyQt5.QtSvg import QSvgWidget
import math
from ui_utils import clear_layout, resize_font
from responsive_svg import SvgWidgetAspect
from media_processing import ProcessWidget
from PyQt5.QtWidgets import QApplication


class FileUploadWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('file_upload')
        self.setStyleSheet(
            '#file_upload{border: 3px dashed #FFFFFF;border-radius: 15px;}'
            'QWidget{color: #FFFFFF;}'
            '#browse_button{background: none;border: 3px solid #00FFFF;border-radius: 15px;}'
            '#scroll_widget{background: #1B1B1B;}'
            'QScrollBar{background-color: #3A3A3A; width: 20px; border-radius: 15px; color:#FFFFFF;}'
        )
        self.video_ext = ['mp3', 'mp4', 'webm', 'mkv', 'wmv', 'avi', 'mov', 'flv']
        self.audio_ext = ['m4a', 'mp3', 'mp4', 'ogg', 'wav', 'flac', 'wma']
        self.button_area = QLabel(parent=self)
        self.button_area.setGeometry(0, self.geometry().height() - 160, self.geometry().width(), 160)
        self.layout_area = QLabel(parent=self)
        self.layout_area.setGeometry(0, 0, self.geometry().width(),
                                     self.geometry().height() - self.button_area.geometry().height())
        self.scroll_widget = QWidget(parent=self.layout_area)
        self.scroll_widget.setObjectName('scroll_widget')
        self.scroll_widget.setAutoFillBackground(True)
        self.scroll = QScrollArea(parent=self.layout_area)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setGeometry(2, 2, self.layout_area.width() - 4, self.layout_area.height() - 4)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scroll_widget)
        self.layout = QGridLayout()
        self.text = QLabel("Drag and Drop files here", parent=self)
        self.text.setAlignment(Qt.AlignCenter)
        self.upload_icon = SvgWidgetAspect('../assets/file_upload_upload.svg', (176, 213), parent=self)
        self.browse_button = QPushButton('Browse', parent=self)
        self.browse_button.setObjectName('browse_button')
        self.browse_button.setGeometry(self.button_area.geometry().width() / 2 - 60,
                                       self.button_area.geometry().y() + self.button_area.geometry().height() / 2 - 30,
                                       120, 60)
        self.browse_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.browse_button.clicked.connect(self.browse)
        self.layout.addWidget(self.text, 0, 0, Qt.AlignCenter)
        self.layout.addWidget(self.upload_icon, 1, 0, Qt.AlignCenter)
        self.scroll_widget.setLayout(self.layout)
        self.files = []
        self.process = None
        self.setAcceptDrops(True)

    def browse(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter(f'Media ({" ".join(["*." + i for i in (self.video_ext + self.audio_ext)])})')
        dialog.setViewMode(QFileDialog.Detail)
        if dialog.exec_():
            files = dialog.selectedFiles()
            self.render_uploaded(files)

    def render_uploaded(self, files):
        file_names = []
        for file in files:
            file_names.append(file.split('/')[-1])
        if self.text is not None:
            self.text.deleteLater()
            self.text = None
            self.upload_icon.deleteLater()
            self.upload_icon = None
        clear_layout(self.layout, delete=True)
        items_in_row = math.ceil(math.sqrt(len(files)))
        row, col = 0, 0
        if len(file_names) == 1:
            stretch = 0
        else:
            stretch = 1
        self.layout.setRowStretch(row, stretch)
        for file in file_names:
            if col == items_in_row:
                col = 0
                row += 1
                self.layout.setRowStretch(row, stretch)
            self.layout.setColumnStretch(col, stretch)
            if file.split('.')[-1] in self.video_ext:
                file_type = 'video'
            else:
                file_type = 'audio'
            self.layout.addWidget(FileIcon(file, file_type, self), row, col, 1, 1)
            col += 1
        self.files = files
        if self.process is None:
            self.process = self.render_process()
        else:
            self.process.check_files(self.files)

    def render_process(self):
        process = self.parent().parent().render_process_widget(self.files, True)
        return process

    def resizeEvent(self, e):
        self.button_area.setGeometry(0, self.geometry().height() - 160, self.geometry().width(), 160)
        self.layout_area.setGeometry(0, 0, self.geometry().width(),
                                     self.geometry().height() - self.button_area.geometry().height())
        self.browse_button.setGeometry(self.button_area.geometry().width() / 2 - 60,
                                       self.button_area.geometry().y() + self.button_area.geometry().height() / 2 - 30,
                                       120, 60)
        self.scroll.setGeometry(2, 2, self.layout_area.width() - 4, self.layout_area.height() - 4)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            files = [file.toLocalFile() for file in e.mimeData().urls()]
            check_pass = False
            for file in files:
                if file.split('.')[-1] in (self.video_ext + self.audio_ext):
                    check_pass = True
                    break
            if check_pass:
                e.accept()
            else:
                e.ignore()
        else:
            e.ignore()

    def dropEvent(self, e):
        files = [file.toLocalFile() for file in e.mimeData().urls()]
        res_files = []
        for file in files:
            if file.split('.') in (self.video_ext + self.audio_ext):
                res_files.append(file)
        self.render_uploaded(res_files)


class FileIcon(QWidget):
    def __init__(self, text, file_type, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet('QWidget{background-color: none; color: #FFFFFF}')
        self.setMinimumSize(60, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.aspect_ratio = (8, 10)
        if file_type == 'video':
            self.icon = QSvgWidget('../assets/video_file_icon.svg', parent=self)
        else:
            self.icon = QSvgWidget('../assets/audio_file_icon.svg', parent=self)
        self.text = QLabel(parent=self)
        self.text.setText(text)
        self.text.setAlignment(Qt.AlignCenter)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.icon)
        self.layout.addWidget(self.text)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def resizeEvent(self, e):
        e_width = e.size().width()
        e_height = e.size().height()
        if e_width < e_height:
            e_point = e_width / self.aspect_ratio[0]
        else:
            e_point = e_height / self.aspect_ratio[1]
        real_width = e_point * self.aspect_ratio[0]
        real_height = e_point * self.aspect_ratio[1]
        self.setFixedSize(real_width, real_height)
        self.icon.setFixedSize(real_width, real_height * 0.75)
        self.text.setFixedSize(real_width, real_height * 0.25)
        font, step = resize_font(self.text)
        self.text.setFont(font)