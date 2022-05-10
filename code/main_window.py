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
from result_processing import ResultWidget, LoadingScreen, ExportWidget
from media_processing import MediaPlayerWidget, ProcessWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        menu_layout = QGridLayout()
        self.logo = SvgWidgetAspect('../assets/logo.svg', (1, 1), parent=self.menu)
        self.file_upload = ResponsiveIconButton('../assets/file_upload.svg', parent=self.menu)
        self.file_upload.setBorderColor('#3BACD9')
        self.file_upload.setCursor(QCursor(Qt.PointingHandCursor))
        self.file_upload.clicked.connect(self.render_file_upload)
        self.file_upload.clicked.connect(lambda: self.toggle_active(self.file_upload))
        self.video_record = ResponsiveIconButton('../assets/video_record.svg', parent=self.menu)
        self.video_record.setBorderColor('#A7171A')
        self.video_record.setCursor(QCursor(Qt.PointingHandCursor))
        self.video_record.clicked.connect(lambda: self.render_record('video'))
        self.video_record.clicked.connect(lambda: self.toggle_active(self.video_record))
        self.audio_record = ResponsiveIconButton('../assets/audio_record.svg', parent=self.menu)
        self.audio_record.setBorderColor('#DA70D6')
        self.audio_record.setCursor(QCursor(Qt.PointingHandCursor))
        self.audio_record.clicked.connect(lambda: self.render_record('audio'))
        self.audio_record.clicked.connect(lambda: self.toggle_active(self.audio_record))
        self.settings = ResponsiveIconButton('../assets/settings.svg', parent=self.menu)
        self.settings.setCursor(QCursor(Qt.PointingHandCursor))
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
        self.screen_widgets = {
            'file_upload_widget': None,
            'record_widget': None,
            'media_widget': None,
            'process_widget': None,
            'result_widget': None,
            'export_widget': None
        }
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
        self.reset_screen_widgets()
        screen_file_upload = FileUploadWidget(parent=self.screen)
        screen_file_upload.setGeometry(128, 256, 1024, 512)
        screen_file_upload.show()
        self.screen_widgets['file_upload_widget'] = screen_file_upload
        return screen_file_upload

    def render_record(self, record_type):
        clear_widget(self.screen)
        self.reset_screen_widgets()
        self.clear_thread()
        screen_record_video = RecordWidget(record_type, parent=self.screen)
        screen_record_video.render_default()
        screen_record_video.setGeometry(128, 256, 1024, 512)
        screen_record_video.show()
        self.screen_widgets['record_widget'] = screen_record_video
        return screen_record_video

    def render_media_process(self, output):
        clear_widget(self.screen)
        self.reset_screen_widgets()
        self.clear_thread()
        screen_media = MediaPlayerWidget(output, parent=self.screen)
        screen_media.setGeometry(128, 256, 1024, 512)
        screen_media.show()
        self.screen_widgets['media_widget'] = screen_media
        return screen_media

    def render_loading_screen(self):
        # clear_widget(self.screen)
        # self.clear_thread()
        loading_screen = LoadingScreen(parent=self.screen)
        loading_screen.setFixedSize(self.screen.width(), self.screen.height())
        loading_screen.show()
        return loading_screen

    def render_process_widget(self, files, file_process):
        # clear_widget(self.screen)
        # self.clear_thread()
        process = ProcessWidget(files, file_process, parent=self.screen)
        process.setGeometry(345, 820, 600, 150)
        process.show()
        self.screen_widgets['process_widget'] = process
        return process

    def render_result_process(self, files):
        clear_widget(self.screen)
        self.reset_screen_widgets()
        self.clear_thread()
        screen_result = ResultWidget(files, parent=self.screen)
        screen_result.setGeometry(128, 256, 1024, 512)
        screen_result.show()
        self.screen_widgets['result_widget'] = screen_result
        return screen_result

    def render_export_widget(self, files):
        # clear_widget(self.screen)
        # self.clear_thread()
        export = ExportWidget(files, parent=self.screen)
        export.setGeometry(345, 820, 600, 150)
        export.show()
        self.screen_widgets['export_widget'] = export
        return export

    def reset_screen_widgets(self):
        self.screen_widgets = {
            'file_upload_widget': None,
            'record_widget': None,
            'media_widget': None,
            'process_widget': None,
            'result_widget': None
        }

    def closeEvent(self, e):
        clear_widget(self)
