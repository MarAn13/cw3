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
from settings import SettingsWidget
from main_screen import MainWidget
from utils import get_from_file


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName('main_window')
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
        self.resolution = get_from_file('config.txt', 'Resolution')['Resolution'].split('x')
        self.resolution = list(map(lambda i: int(str(i).strip()), self.resolution))
        self.menu = None
        self.screen = None
        self.screen_widgets = {
            'main_widget': None,
            'file_upload_widget': None,
            'record_widget': None,
            'media_widget': None,
            'process_widget': None,
            'result_widget': None,
            'export_widget': None,
            'loading_widget': None,
            'settings_widget': None
        }
        self.threads = []

    def change_resolution(self):
        self.resolution = get_from_file('config.txt', 'Resolution')['Resolution'].split('x')
        self.resolution = list(map(lambda i: int(str(i).strip()), self.resolution))
        self.setFixedSize(self.resolution[0], self.resolution[1])

    def toggle_active(self, widget):
        for i in [self.file_upload, self.video_record, self.audio_record]:
            i.setBorderState(True)
        if widget in [self.file_upload, self.video_record, self.audio_record]:
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

    def render_menu(self):
        if self.menu is not None:
            self.menu.deleteLater()
        self.menu = QWidget(parent=self)
        self.menu.setObjectName('menu')
        self.menu.setGeometry(0, 0, self.width() / 9, self.height())
        menu_layout = QGridLayout()
        self.logo = SvgWidgetAspect('../assets/logo.svg', (1, 1), True, parent=self.menu)
        self.logo.setCursor(QCursor(Qt.PointingHandCursor))
        self.logo.connect(self.render_main_screen)
        self.logo.connect(lambda: self.toggle_active(self.logo))
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
        self.settings.clicked.connect(self.render_settings)
        self.settings.clicked.connect(lambda: self.toggle_active(self.settings))
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
        self.menu.show()

    def render_screen(self):
        if self.screen is not None:
            self.screen.deleteLater()
        self.screen = QWidget(parent=self)
        self.screen.setObjectName('screen')
        self.screen.setGeometry(self.menu.width(), 0, self.width() - self.menu.width(), self.height())
        self.screen.show()

    def render_main_screen(self):
        self.reset_screen_widgets()
        screen_main = MainWidget(parent=self.screen)
        screen_main.setGeometry(0, 0, self.screen.width(), self.screen.height())
        screen_main.show()
        self.screen_widgets['main_widget'] = screen_main
        return screen_main

    def render_file_upload(self):
        self.reset_screen_widgets()
        screen_file_upload = FileUploadWidget(parent=self.screen)
        screen_file_upload.setGeometry(int(self.screen.width() * 0.1), int(self.screen.height() * 0.25), int(self.screen.width() * 0.8), int(self.screen.height() * 0.5))
        screen_file_upload.show()
        self.screen_widgets['file_upload_widget'] = screen_file_upload
        return screen_file_upload

    def render_record(self, record_type):
        self.reset_screen_widgets()
        self.clear_thread()
        screen_record = RecordWidget(record_type, parent=self.screen)
        screen_record.render_default()
        screen_record.setGeometry(int(self.screen.width() * 0.1), int(self.screen.height() * 0.25), int(self.screen.width() * 0.8), int(self.screen.height() * 0.5))
        screen_record.show()
        self.screen_widgets['record_widget'] = screen_record
        return screen_record

    def render_settings(self):
        self.reset_screen_widgets()
        self.clear_thread()
        screen_settings = SettingsWidget(parent=self.screen)
        screen_settings.config_changed.connect(self.change_resolution)
        screen_settings.setGeometry(0, 0, self.screen.width(), self.screen.height())
        screen_settings.show()
        self.screen_widgets['settings_widget'] = screen_settings
        return screen_settings

    def render_media_process(self, output, file_type):
        self.reset_screen_widgets()
        self.clear_thread()
        screen_media = MediaPlayerWidget(output, file_type, parent=self.screen)
        screen_media.setGeometry(int(self.screen.width() * 0.1), int(self.screen.height() * 0.25), int(self.screen.width() * 0.8), int(self.screen.height() * 0.5))
        screen_media.show()
        self.screen_widgets['media_widget'] = screen_media
        return screen_media

    def render_loading_screen(self):
        loading_screen = LoadingScreen(parent=self.screen)
        loading_screen.setFixedSize(self.screen.width(), self.screen.height())
        loading_screen.show()
        self.screen_widgets['loading_widget'] = loading_screen
        return loading_screen

    def render_process_widget(self, files, file_process):
        process = ProcessWidget(files, file_process, parent=self.screen)
        process.setGeometry(int(self.screen.width() * 0.26953125), int(self.screen.height() * 0.80078125), int(self.screen.width() * 0.46875), int(self.screen.height() * 0.146484375))
        process.show()
        self.screen_widgets['process_widget'] = process
        return process

    def render_result_process(self, files):
        self.reset_screen_widgets()
        self.clear_thread()
        screen_result = ResultWidget(files, parent=self.screen)
        screen_result.setGeometry(int(self.screen.width() * 0.1), int(self.screen.height() * 0.25), int(self.screen.width() * 0.8), int(self.screen.height() * 0.5))
        screen_result.show()
        self.screen_widgets['result_widget'] = screen_result
        return screen_result

    def render_export_widget(self, files):
        export = ExportWidget(files, parent=self.screen)
        export.setGeometry(int(self.screen.width() * 0.26953125), int(self.screen.height() * 0.80078125), int(self.screen.width() * 0.46875), int(self.screen.height() * 0.146484375))
        export.show()
        self.screen_widgets['export_widget'] = export
        return export

    def reset_screen_widgets(self):
        for key, val in self.screen_widgets.items():
            if val is not None:
                val.deleteLater()
            self.screen_widgets[key] = None

    def resizeEvent(self, e):
        self.setFixedSize(self.resolution[0], self.resolution[1])
        self.render_menu()
        self.render_screen()
        self.reset_screen_widgets()
        self.render_main_screen()

    def closeEvent(self, e):
        self.reset_screen_widgets()
