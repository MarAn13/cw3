import time

from PyQt5.QtWidgets import QApplication, QWidget, \
    QGraphicsOpacityEffect, QVBoxLayout, QLabel, QPushButton, QStyleOption, QStyle, QFileDialog, QGridLayout, \
    QScrollArea, QMainWindow, QHBoxLayout, QCheckBox, QRadioButton
from PyQt5.QtCore import Qt, QSize, QUrl, QFile, QElapsedTimer, QTimer, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QLinearGradient, QColor, QBrush, QPalette, QPainter, QPainterPath, QPixmap, QIcon, QCursor, \
    QPen, QFont, QFontMetrics, QImage
from PyQt5.Qt import QSizePolicy, QCamera, QCameraViewfinder, QVideoEncoderSettings, QMediaRecorder, QMultimedia, \
    QCameraInfo
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from utils.utils import check_streams
import math
import cv2 as cv
import pyaudio
import wave


# class LogoWidget(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#         self.setStyleSheet('QLabel{color: #252525;}')
#         self.text = QLabel('AVSR', self)
#         # self.logo_text.setFont(QFont('Arial', 7))
#         self.text.setAlignment(Qt.AlignCenter)
#
#     def resizeEvent(self, e):
#         self.text.resize(self.geometry().width(), self.geometry().height())
#
#     def paintEvent(self, e):
#         logo_grad = QLinearGradient(self.geometry().width() / 2,
#                                     0,
#                                     self.geometry().width() / 2,
#                                     self.geometry().height()
#                                     )
#         logo_grad.setColorAt(0, QColor(18, 249, 255, 255))
#         logo_grad.setColorAt(1, QColor(224, 176, 255, 255))
#         logo_painter = QPainter()
#         logo_painter.setBrush(QBrush(logo_grad))
#         logo_path = QPainterPath()
#         logo_path.addRoundedRect(0, 0, self.geometry().width(), self.geometry().height(), 15, 15)
#         logo_painter.fillPath(logo_path, logo_grad)
def clear_widget(widget):
    for i in widget.children():
        i.deleteLater()


def clear_layout(layout, delete=False):
    for i in reversed(range(layout.count())):
        temp = layout.itemAt(i).widget()
        layout.removeWidget(temp)
        if delete:
            temp.deleteLater()
        else:
            temp.setVisible(False)


class QSvgWidgetAspect(QSvgWidget):
    def __init__(self, filepath, aspect_ratio, clickable=False, parent=None):
        super().__init__(parent=parent)
        self.aspect_ratio = aspect_ratio
        self.clickable = clickable
        self.click_event = None
        if self.clickable:
            self.setCursor(QCursor(Qt.PointingHandCursor))
        self.load(filepath)

    def resizeEvent(self, e):
        e_width = e.size().width()
        e_height = e.size().height()
        if e_width < e_height:
            e_point = e_width / self.aspect_ratio[0]
        else:
            e_point = e_height / self.aspect_ratio[1]
        self.setFixedSize(e_point * self.aspect_ratio[0], e_point * self.aspect_ratio[1])

    def connect(self, func):
        if self.clickable:
            self.click_event = func

    def mousePressEvent(self, e):
        if self.clickable and self.click_event:
            self.click_event()


class ResponsiveIconButton(QPushButton):
    def __init__(self, img_path, color=None, parent=None):
        super().__init__(parent=parent)
        self.pixmap = QPixmap(img_path)
        if color:
            mask = self.pixmap.createMaskFromColor(QColor('transparent'), Qt.MaskInColor)
            self.pixmap.fill((QColor(color)))
            self.pixmap.setMask(mask)
        self.setIcon(QIcon(self.pixmap))

    def resizeEvent(self, e):
        e_width = e.size().width()
        e_height = e.size().height()
        if e_width < e_height:
            e_point = e_width
        else:
            e_point = e_height
        self.setIconSize(QSize(e_point, e_point))


class AudioProcess(QObject):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.mic = None
        self.mic_state = False

    def record(self):
        self.mic = pyaudio.PyAudio()
        chunk = 1024  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16  # 16 bits per sample
        channels = 1
        rate = 16000
        filename = "record_audio.wav"
        stream = self.mic.open(
            format=sample_format,
            channels=channels,
            rate=rate,
            frames_per_buffer=chunk,
            input=True
        )
        frames = []
        while self.mic_state:
            data = stream.read(chunk)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        self.mic.terminate()
        wf = wave.open(filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(self.mic.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        self.finished.emit()

    def toggle_record(self):
        print('toggle_record_audio')
        if self.mic_state:
            self.mic_state = False
        else:
            self.mic_state = True

    def destroy(self):
        print('destroy_audio')
        self.mic_state = False


class VideoProcess(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.cam = cv.VideoCapture(0)
        self.cam_state = True
        self.recorder = None
        self.recorder_state = False

    def run(self):
        while self.cam_state:
            ret, frame = self.cam.read()
            if ret:
                frame = cv.flip(frame, 1)
                frame_process = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                height, width, channel = frame_process.shape
                step = channel * width
                img = QImage(frame_process.data, width, height, step, QImage.Format_RGB888)
                self.progress.emit(img)
                if self.recorder_state:
                    self.recorder.write(frame)
        if self.recorder_state:
            self.recorder.release()
        self.cam.release()
        cv.destroyAllWindows()
        self.finished.emit()

    def toggle_record(self):
        print('toggle_record_video')
        if self.recorder is None:
            self.recorder = cv.VideoWriter('record_video.mp4', cv.VideoWriter_fourcc('m', 'p', '4', 'v'), 30,
                                           (int(self.cam.get(3)), int(self.cam.get(4))))
            self.recorder_state = True
        else:
            self.recorder.release()
            self.recorder = None
            self.recorder_state = False

    def destroy(self):
        print('destroy_video')
        self.cam_state = False


class VideoRecordWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #292929; border-radius: 15px}'
            'QLabel{color: #FFFFFF;}'
        )
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.area_layout = QGridLayout()
        self.viewfinder = QLabel(parent=self.area)
        self.record_toggle_button = QPushButton(parent=self.area)
        self.record_toggle_button.setVisible(False)
        self.record_timer = QElapsedTimer()
        self.record_repeater = QTimer(parent=self)
        self.record_repeater.timeout.connect(self.update_time)
        self.record_timer_text = QLabel(parent=self.area)
        self.record_timer_text.setVisible(False)
        self.worker_video = None
        self.worker_audio = None
        self.thread_video = None
        self.thread_audio = None
        self.render_default()

    def render_default(self):
        clear_layout(self.area_layout)
        cam = cv.VideoCapture(0, cv.CAP_DSHOW)
        if cam.isOpened():
            availability = True
        else:
            availability = False
        cam.release()
        cv.destroyAllWindows()
        text = QLabel(parent=self.area)
        if not availability:
            text.setText('Sorry this mode is not supported because you dont have a camera available to record')
            self.area_layout.addWidget(text, 0, 0, alignment=Qt.AlignCenter)
            text.setWordWrap(True)
        else:
            text.setText('Click to start recording')
            record_button = QSvgWidgetAspect('assets/video_record.svg', (16, 11), clickable=True, parent=self.area)
            record_button.setObjectName('record')
            record_button.connect(self.render_record)
            self.area_layout.addWidget(record_button, 0, 0, alignment=Qt.AlignCenter)
            self.area_layout.addWidget(text, 1, 0, alignment=Qt.AlignCenter)
        self.area.setLayout(self.area_layout)

    def render_record(self):
        clear_layout(self.area_layout, delete=True)
        self.record_timer_text.setText('00:00:00')
        self.record_timer_text.setVisible(True)
        self.record_toggle_button.setText('Record')
        self.record_toggle_button.clicked.connect(self.start_record)
        self.record_toggle_button.setVisible(True)
        self.record_toggle_button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.record_timer_text, 0, 0, 0, 1, Qt.AlignCenter)
        self.area_layout.addWidget(self.viewfinder, 0, 1, 0, 2, Qt.AlignCenter)
        self.area_layout.addWidget(self.record_toggle_button, 0, 4, 0, 1, Qt.AlignCenter)
        if self.worker_video is None:
            self.worker_video = VideoProcess(parent=self.thread_video)
            self.thread_video = QThread(parent=self)
            self.worker_video.moveToThread(self.thread_video)
            self.thread_video.started.connect(self.worker_video.run)
            self.worker_video.progress.connect(self.update_pixmap)
            self.worker_video.finished.connect(self.thread_video.quit)
            self.worker_video.finished.connect(self.worker_video.deleteLater)
            self.thread_video.finished.connect(self.thread_video.deleteLater)
        self.thread_video.start()
        # self.camera = QCamera(self.camera_info[0])
        # self.camera.setViewfinder(self.viewfinder)
        # self.recorder = QMediaRecorder(self.camera)
        # recorder_video_settings = self.recorder.videoSettings()
        # recorder_video_settings.setQuality(QMultimedia.VeryHighQuality)
        # recorder_video_settings.setFrameRate(30)
        # recorder_video_settings.setCodec('video/mp4')
        # self.recorder.setVideoSettings(recorder_video_settings)
        # self.recorder.setContainerFormat('mp4')
        # self.recorder.setOutputLocation(QUrl.fromLocalFile('test_record.mp4'))
        # self.camera.focus()
        # self.camera.start()

    def start_record(self):
        print('start_record')
        self.record_toggle_button.setText('Stop')
        self.record_toggle_button.disconnect()
        self.record_toggle_button.clicked.connect(self.stop_record)

        if self.worker_audio is None:
            self.worker_audio = AudioProcess(parent=self.thread_audio)
            self.thread_audio = QThread(parent=self)
            self.worker_audio.moveToThread(self.thread_audio)
            self.thread_audio.started.connect(self.worker_audio.record)
            self.worker_audio.finished.connect(self.thread_audio.quit)
            self.worker_audio.finished.connect(self.worker_audio.deleteLater)
            self.thread_audio.finished.connect(self.thread_audio.deleteLater)

        self.toggle_record_video()
        self.toggle_record_audio()
        self.record_toggle_button.setEnabled(False)
        self.record_timer.start()
        self.record_repeater.start(1000)

    def stop_record(self):
        print('stop_record')
        self.record_toggle_button.setText('Record')
        self.record_toggle_button.disconnect()
        self.record_toggle_button.clicked.connect(self.start_record)
        self.record_timer.restart()
        self.record_repeater.stop()
        self.toggle_record_video()
        self.toggle_record_audio()

    def toggle_record_audio(self):
        self.worker_audio.toggle_record()
        self.thread_audio.start()

    def toggle_record_video(self):
        self.worker_video.toggle_record()

    def update_pixmap(self, img):
        self.viewfinder.setPixmap(QPixmap.fromImage(img))

    def update_time(self):
        if not self.record_toggle_button.isEnabled():
            self.record_toggle_button.setEnabled(True)
        secs = int(self.record_timer.elapsed() / 1000)
        mins = int(secs / 60)
        secs -= mins * 60
        hours = int(mins / 60)
        mins -= hours * 60
        hours, mins, secs = ['0' + i if len(i) == 1 else i for i in [str(hours), str(mins), str(secs)]]
        self.record_timer_text.setText(f'{hours}:{mins}:{secs}')

    def destroy(self):
        if self.worker_video:
            self.worker_video.destroy()
            # self.worker_video.deleteLater()
        if self.thread_video:
            self.thread_video.exit()
        if self.worker_audio:
            self.worker_audio.destroy()
            self.worker_audio.deleteLater()

    def resizeEvent(self, e):
        self.area.setFixedSize(self.width(), self.height())


def resize_font(widget):
    # font setting
    font = widget.font()
    check = True
    real_bound = widget.contentsRect()
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
        test_bound = QFontMetrics(test_font).boundingRect(widget.text())
        bound = QFontMetrics(font).boundingRect(widget.text())
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


class ProcessWidget(QWidget):
    def __init__(self, files, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            '#area{background-color: #2D2D2D; border-radius: 15px;}'
            'QPushButton{color: #50C878;background-color: #303933;border: 1px solid #3E3E3E;border-radius: 15px;}'
            'QRadioButton{color: #FFFFFF; background-color: blue;}'
            'QRadioButton::indicator{width: 10px; height: 10px; background-color: #FFFFFF;}'
            'QRadioButton::indicator::checked{image: url(assets/radio_button_indicator.svg);}'
            'QRadioButton[cssClass~=disabled]{color: grey; background-color: yellow;}'
            'QRadioButton::indicator[cssClass~=disabled]{background-color: grey;}'
        )
        self.setGeometry(345, 820, 600, 150)
        self.area = QLabel(parent=self)
        self.area.setObjectName('area')
        self.radio_area = QLabel(parent=self.area)
        self.button_area = QLabel(parent=self.area)
        self.radio_area_layout = QVBoxLayout()
        self.radio_button_preferred = QRadioButton('preferred', parent=self.radio_area)
        self.radio_button_preferred.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.radio_button_preferred.setChecked(True)
        self.radio_button_audio_only = QRadioButton('audio-only', parent=self.radio_area)
        self.radio_button_audio_only.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.radio_button_video_only = QRadioButton('video-only', parent=self.radio_area)
        self.radio_button_video_only.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.radio_button_audio_video = QRadioButton('audio-video', parent=self.radio_area)
        self.radio_button_audio_video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.radio_area_layout.addWidget(self.radio_button_preferred)
        self.radio_area_layout.addWidget(self.radio_button_audio_only)
        self.radio_area_layout.addWidget(self.radio_button_video_only)
        self.radio_area_layout.addWidget(self.radio_button_audio_video)
        self.radio_area.setLayout(self.radio_area_layout)
        self.process_button = QPushButton('Process', parent=self.button_area)
        self.process_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.process_button.clicked.connect(self.process)
        self.audio_only = []
        self.video_only = []
        self.audio_video = []
        self.check_files(files)

    def check_files(self, files):
        self.audio_only = []
        self.video_only = []
        self.audio_video = []
        for i in [self.radio_button_preferred, self.radio_button_audio_only, self.radio_button_video_only,
                  self.radio_button_audio_video]:
            i.setCheckable(True)
            i.setProperty('cssClass', None)
            i.setCursor(QCursor(Qt.PointingHandCursor))
        for file in files:
            check_audio, check_video = check_streams(file)
            if check_video and check_audio:
                self.audio_video.append(file)
            elif check_video:
                self.video_only.append(file)
            elif check_audio:
                self.audio_only.append(file)
        sum_length = len(self.audio_video) + len(self.video_only) + len(self.audio_only)
        if len(self.audio_only) + len(self.audio_video) != sum_length:
            self.radio_button_audio_only.setCheckable(False)
            self.radio_button_audio_only.setProperty('cssClass', 'disabled')
            self.radio_button_audio_only.setCursor(QCursor(Qt.ForbiddenCursor))
        if len(self.video_only) + len(self.audio_video) != sum_length:
            self.radio_button_video_only.setCheckable(False)
            self.radio_button_video_only.setProperty('cssClass', 'disabled')
            self.radio_button_video_only.setCursor(QCursor(Qt.ForbiddenCursor))
        if len(self.audio_video) != sum_length:
            self.radio_button_audio_video.setCheckable(False)
            self.radio_button_audio_video.setProperty('cssClass', 'disabled')
            self.radio_button_audio_video.setCursor(QCursor(Qt.ForbiddenCursor))
        self.setStyleSheet(self.styleSheet())

    def process(self):
        print('process')

    def resizeEvent(self, e):
        self.area.setGeometry(0, 0, self.width(), self.height())
        self.radio_area.setGeometry(0, 0, self.area.width() / 2, self.area.height())
        self.button_area.setGeometry(self.area.width() / 2, 0, self.area.width() / 2, self.area.height())
        self.process_button.setGeometry(79, 37, 150, 75)
        min_font = self.radio_button_preferred.font()
        for i in [self.radio_button_preferred, self.radio_button_audio_only, self.radio_button_video_only,
                  self.radio_button_audio_video]:
            font, step = resize_font(i)
            if font.pointSize() < min_font.pointSize():
                min_font = font
        for i in [self.radio_button_preferred, self.radio_button_audio_only, self.radio_button_video_only,
                  self.radio_button_audio_video]:
            i.setFont(min_font)


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
            self.icon = QSvgWidget('assets/video_file_icon.svg', parent=self)
        else:
            self.icon = QSvgWidget('assets/audio_file_icon.svg', parent=self)
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
        # self.upload_icon = QSvgWidget('assets/file_upload_upload.svg', parent=self)
        self.upload_icon = QSvgWidgetAspect('assets/file_upload_upload.svg', (176, 213), parent=self)

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
        process = ProcessWidget(self.files, parent=self.parent())
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
        menu_layout = QVBoxLayout()
        self.logo = QLabel(parent=self.menu)
        self.logo.setObjectName('logo')
        self.logo.setGeometry(38, 38, 84, 84)
        logo_pixmap = QPixmap('assets/logo.svg')
        self.logo.setPixmap(logo_pixmap)
        self.file_upload = QPushButton(parent=self.menu)
        self.file_upload.setObjectName('file_upload')
        self.file_upload.setGeometry(38, 252, 84, 84)
        self.file_upload.setCursor(QCursor(Qt.PointingHandCursor))
        self.file_upload.setProperty('cssClass', 'active boy')
        file_upload_pixmap = QPixmap('assets/file_upload.svg')
        file_upload_icon = QIcon(file_upload_pixmap)
        self.file_upload.setIcon(file_upload_icon)
        self.file_upload.clicked.connect(self.render_file_upload)
        self.video_record = QPushButton(parent=self.menu)
        self.video_record.setObjectName('video_record')
        self.video_record.setGeometry(38, 427, 84, 84)
        self.video_record.setCursor(QCursor(Qt.PointingHandCursor))
        video_record_pixmap = QPixmap('assets/video_record.svg')
        video_record_icon = QIcon(video_record_pixmap)
        self.video_record.setIcon(video_record_icon)
        self.video_record.clicked.connect(self.render_video_record)
        self.audio_record = QPushButton(parent=self.menu)
        self.audio_record.setObjectName('audio_record')
        self.audio_record.setGeometry(38, 602, 84, 84)
        self.audio_record.setCursor(QCursor(Qt.PointingHandCursor))
        audio_record_pixmap = QPixmap('assets/audio_record.svg')
        audio_record_icon = QIcon(audio_record_pixmap)
        self.audio_record.setIcon(audio_record_icon)
        self.settings = QPushButton(parent=self.menu)
        self.settings.setObjectName('settings')
        self.settings.setGeometry(62.98, 952.5, 35, 35)
        self.settings.setCursor(QCursor(Qt.PointingHandCursor))
        settings_pixmap = QPixmap('assets/settings.svg')
        settings_icon = QIcon(settings_pixmap)
        self.settings.setIcon(settings_icon)
        self.menu.setLayout(menu_layout)
        self.screen = QWidget(parent=self)
        self.screen.setObjectName('screen')
        self.screen.setGeometry(160, 0, 1280, 1024)
        self.screen_file_upload = None
        self.screen_record_video = None
        self.render_file_upload()

    def render_file_upload(self):
        clear_widget(self.screen)
        self.screen_file_upload = FileUploadWidget(parent=self.screen)
        self.screen_file_upload.setGeometry(128, 256, 1024, 512)
        self.screen_file_upload.show()

    def render_video_record(self):
        if self.screen_record_video:
            self.screen_record_video.destroy()
        clear_widget(self.screen)
        self.screen_record_video = VideoRecordWidget(parent=self.screen)
        self.screen_record_video.setGeometry(128, 256, 1024, 512)
        self.screen_record_video.show()


def main():
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable high dpi scaling
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use high dpi icons
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
    print('Finished')


if __name__ == '__main__':
    main()
