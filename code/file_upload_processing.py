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
            '#test{background-color: red;}'
            '#test1{background-color: blue;}'
            '#file_upload{background-color: #292929;border: 3px dashed #FFFFFF;border-radius: 15px;}'
            'QWidget{color: #FFFFFF;}'
            '#browse_button{background: none;border: 3px solid #00FFFF;border-radius: 15px;}'
        )
        self.video_ext = ['mp3', 'mp4', 'webm', 'mkv']
        self.audio_ext = ['ogg', 'wav', 'flac']
        self.button_area = QLabel(parent=self)
        self.button_area.setGeometry(0, self.geometry().height() - 160, self.geometry().width(), 160)
        self.button_area.setObjectName('test1')
        self.layout_area = QLabel(parent=self)
        self.layout_area.setGeometry(0, 0, self.geometry().width(),
                                     self.geometry().height() - self.button_area.geometry().height())
        self.layout_area.setObjectName('test')
        self.scroll_widget = QWidget(parent=self.layout_area)
        self.scroll = QScrollArea(parent=self.layout_area)
        self.scroll.setBackgroundRole(QPalette.Dark)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setGeometry(0, 0, self.layout_area.width(), self.layout_area.height())
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scroll_widget)
        self.layout = QGridLayout()
        self.text = QLabel("Drag and Drop files here", parent=self)
        self.text.setAlignment(Qt.AlignCenter)
        # self.upload_icon = QSvgWidget('../assets/file_upload_upload.svg', parent=self)
        self.upload_icon = SvgWidgetAspect('../assets/file_upload_upload.svg', (176, 213), parent=self)

        # self.upload_icon.setPixmap()
        # self.upload_icon.setAlignment(Qt.AlignCenter)
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
            file_type = 'video'
            if file[-1] in self.audio_ext:
                file_type = 'audio'
            self.layout.addWidget(FileIcon(file, file_type, self), row, col, 1, 1)
            col += 1
            self.files = files
            if self.process is None:
                self.process = self.render_process()
            else:
                self.process.check_files(self.files)

    def render_process(self):
        process = ProcessWidget(self.files, True, parent=self.parent())
        process.show()
        return process

    def resizeEvent(self, e):
        self.button_area.setGeometry(0, self.geometry().height() - 160, self.geometry().width(), 160)
        self.layout_area.setGeometry(0, 0, self.geometry().width(),
                                     self.geometry().height() - self.button_area.geometry().height())
        self.browse_button.setGeometry(self.button_area.geometry().width() / 2 - 60,
                                       self.button_area.geometry().y() + self.button_area.geometry().height() / 2 - 30,
                                       120, 60)
        self.scroll.setGeometry(0, 0, self.layout_area.width(), self.layout_area.height())

    # def paintEvent(self, e):
    #     p = QPainter(self)
    #     pen = QPen(QColor('#FFFFFF'))
    #     p.setPen(pen)
    #     pen.setStyle(Qt.DashLine)
    #     p.setBrush(QBrush(QColor('#292929')))
    #     p.drawRoundedRect(0, 0, self.geometry().width(), self.geometry().height(), 15, 15)

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

    def dragLeaveEvent(self, e):
        print('drag_out')

    def dragMoveEvent(self, e):
        print('drag_move')


class FileIcon(QWidget):
    def __init__(self, text, file_type, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet('QWidget{background-color: black; color: #FFFFFF}'
                           '#icon{background-color: purple;}'
                           '#text{background-color: green;}')
        self.setMinimumSize(60, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.aspect_ratio = (8, 10)
        if file_type == 'video':
            self.icon = QSvgWidget('../assets/video_file_icon.svg', parent=self)
        else:
            self.icon = QSvgWidget('../assets/audio_file_icon.svg', parent=self)
        self.icon.setObjectName('icon')
        self.text = QLabel(parent=self)
        self.text.setText(text)
        self.text.setObjectName('text')
        self.text.setAlignment(Qt.AlignCenter)
        self.layout = QVBoxLayout()
        self.layout.setObjectName('layout')
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

#
# app = QApplication([])
# window = FileUploadWidget()
# window.setFixedSize(1200, 800)
# window.show()
# app.exec_()
