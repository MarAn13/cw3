"""
Main window class
"""
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QSizePolicy
from PyQt5.Qt import Qt
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QCursor
from ui_utils import clear_widget
from responsive_svg import SvgWidgetAspect, ResponsiveIconButton
from file_upload_processing import FileUploadWidget
from record_processing import RecordWidget
from result_processing import ResultWidget
from media_processing import MediaPlayerWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.main_window = QWidget()
        self.setObjectName('main_window')
        self.setFixedWidth(1440)
        self.setFixedHeight(1024)
        self.setStyleSheet(
            '#main_window{background: #121212;}'
            '#menu{background: #252525;}'
            '#menu QPushButton{background-color: #252525;border: 3px solid;border-radius: 15px;}'
            '#menu QPushButton:hover{background-color: #323232;}'
            '#menu QPushButton[cssClass~=active]{background-color: #323232; border: 0;}'
            '#menu #file_upload{border-color: #3BACD9;}'
            '#menu #video_record{border-color: #A7171A;}'
            '#menu #audio_record{border-color: #DA70D6;}'
            '#screen{background: #1B1B1B;}'
        )
        self.menu = QWidget(parent=self)
        self.menu.setObjectName('menu')
        self.menu.setGeometry(0, 0, 160, 1024)
        # menu_layout = QVBoxLayout()
        menu_layout = QGridLayout()
        self.logo = SvgWidgetAspect('../assets/logo.svg', (1, 1), parent=self.menu)
        # self.logo.setGeometry(38, 38, 84, 84)
        # self.logo.setPixmap(QPixmap('../assets/logo.svg'))
        self.file_upload = ResponsiveIconButton('../assets/file_upload.svg', parent=self.menu)
        self.file_upload.setBorderColor('#3BACD9')
        # self.file_upload.setObjectName('file_upload')
        # self.file_upload.setGeometry(38, 252, 84, 84)
        self.file_upload.setCursor(QCursor(Qt.PointingHandCursor))
        # self.file_upload.setIcon(QIcon(QPixmap('../assets/file_upload.svg')))
        self.file_upload.clicked.connect(self.render_file_upload)
        self.file_upload.clicked.connect(lambda: self.toggle_active(self.file_upload))
        self.video_record = ResponsiveIconButton('../assets/video_record.svg', parent=self.menu)
        self.video_record.setBorderColor('#A7171A')
        # self.video_record.setObjectName('video_record')
        # self.video_record.setGeometry(38, 427, 84, 84)
        self.video_record.setCursor(QCursor(Qt.PointingHandCursor))
        # self.video_record.setIcon(QIcon(QPixmap('../assets/video_record.svg')))
        self.video_record.clicked.connect(lambda: self.render_record('video'))
        self.video_record.clicked.connect(lambda: self.toggle_active(self.video_record))
        self.audio_record = ResponsiveIconButton('../assets/audio_record.svg', parent=self.menu)
        self.audio_record.setBorderColor('#DA70D6')
        # self.audio_record.setObjectName('audio_record')
        # self.audio_record.setGeometry(38, 602, 84, 84)
        self.audio_record.setCursor(QCursor(Qt.PointingHandCursor))
        # self.audio_record.setIcon(QIcon(QPixmap('../assets/audio_record.svg')))
        self.audio_record.clicked.connect(lambda: self.render_record('audio'))
        self.audio_record.clicked.connect(lambda: self.toggle_active(self.audio_record))
        self.settings = ResponsiveIconButton('../assets/settings.svg', parent=self.menu)
        # self.settings.setObjectName('settings')
        # self.settings.setGeometry(62.98, 952.5, 35, 35)
        self.settings.setCursor(QCursor(Qt.PointingHandCursor))
        # self.settings.setIcon(QIcon(QPixmap('../assets/settings.svg')))
        self.logo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.file_upload.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.video_record.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.audio_record.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.settings.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        menu_layout.addWidget(self.logo, 0, 0, 1, 1)
        menu_layout.addWidget(self.file_upload, 2, 0, 1, 1)
        menu_layout.addWidget(self.video_record, 3, 0, 1, 1)
        menu_layout.addWidget(self.audio_record, 4, 0, 1, 1)
        menu_layout.addWidget(self.settings, 5, 0, 1, 1)
        self.menu.setLayout(menu_layout)
        self.screen = QWidget(parent=self)
        self.screen.setObjectName('screen')
        self.screen.setGeometry(160, 0, 1280, 1024)
        self.threads = []
        self.render_file_upload()

    def toggle_active(self, widget):
        for i in [self.file_upload, self.video_record, self.audio_record]:
            i.setBorderState(True)
        widget.setBorderState(False)

    def create_thread(self):
        self.threads.append(QThread())
        return self.threads[-1]

    def clear_thread(self):
        threads = []
        for thread in self.threads:
            if not thread.isFinished():
                threads.append(thread)
        self.threads = threads

    def render_file_upload(self):
        clear_widget(self.screen)
        screen_file_upload = FileUploadWidget(parent=self.screen)
        screen_file_upload.setGeometry(128, 256, 1024, 512)
        screen_file_upload.show()
        return screen_file_upload

    def render_record(self, record_type):
        clear_widget(self.screen)
        self.clear_thread()
        screen_record_video = RecordWidget(record_type, parent=self.screen)
        screen_record_video.render_default()
        screen_record_video.setGeometry(128, 256, 1024, 512)
        screen_record_video.show()
        return screen_record_video

    def render_media_process(self, output):
        clear_widget(self.screen)
        self.clear_thread()
        screen_record_audio = MediaPlayerWidget(output, parent=self.screen)
        screen_record_audio.setGeometry(128, 256, 1024, 512)
        screen_record_audio.show()
        return screen_record_audio

    def closeEvent(self, e):
        clear_widget(self)
