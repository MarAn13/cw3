from PyQt5.QtWidgets import QApplication, QWidget, \
    QGraphicsOpacityEffect, QVBoxLayout, QLabel, QPushButton, QStyleOption, QStyle, QFileDialog, QGridLayout, \
    QScrollArea, QMainWindow, QHBoxLayout, QCheckBox, QRadioButton, QSpacerItem, QStackedWidget
from PyQt5.QtCore import Qt, QSize, QUrl, QFile, QElapsedTimer, QTimer, QThread, QObject, pyqtSignal, QRectF
from PyQt5.QtGui import QLinearGradient, QColor, QBrush, QPalette, QPainter, QPainterPath, QPixmap, QIcon, QCursor, \
    QPen, QFont, QFontMetrics, QImage
from PyQt5.Qt import QSizePolicy, QCamera, QCameraViewfinder, QVideoEncoderSettings, QMediaRecorder, QMultimedia, \
    QCameraInfo, QMediaPlayer, QSlider, QVideoWidget, QMediaContent
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from utils.utils import check_streams, merge
import math
import cv2 as cv
import pyaudio
import wave


def ms_to_time(milliseconds):
    secs = int(milliseconds / 1000)
    mins = int(secs / 60)
    secs -= mins * 60
    hours = int(mins / 60)
    mins -= hours * 60
    hours, mins, secs = ['0' + i if len(i) == 1 else i for i in [str(hours), str(mins), str(secs)]]
    return f'{hours}:{mins}:{secs}'


def clear_widget(widget):
    for i in widget.children():
        if i.children():
            clear_widget(i)
        check_func = getattr(i, "destroy", None)
        if callable(check_func):
            i.destroy()
        i.deleteLater()


def clear_layout(layout, delete=False):
    for i in reversed(range(layout.count())):
        temp = layout.itemAt(i).widget()
        layout.removeWidget(temp)
        if delete:
            temp.deleteLater()
        else:
            temp.setVisible(False)


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


class CustomAudioSvgWidget(SvgWidgetAspect):
    filepath = 'assets/audio_record_diamond.svg'
    aspect_ratio = (1, 1)

    def __init__(self, parent=None):
        super().__init__(self.filepath, self.aspect_ratio, True, parent)
        self.max_background_offset = 0
        self.background_offset = self.max_background_offset

    def set_background_offset(self, offset):
        if offset < 0:
            offset = 0
        elif offset > self.max_background_offset:
            offset = self.max_background_offset
        self.background_offset = offset

    def get_background_offset(self):
        return self.background_offset

    def get_max_background_offset(self):
        return self.max_background_offset

    def paintEvent(self, e):
        painter = QPainter()
        painter.begin(self)
        painter.setPen(QColor('transparent'))
        e_point = 0
        if self.width() < self.height():
            e_point = self.width()
        else:
            e_point = self.height()
        self.max_background_offset = e_point * 0.15
        # bound rect
        # painter.setBrush(QColor('blue'))
        # painter.drawRect(self.width() / 2 - e_point / 2, self.height() / 2 - e_point / 2, e_point, e_point)
        grad = QLinearGradient()
        grad.setColorAt(0, QColor('#DA70D6'))
        grad.setColorAt(1, QColor('#7F00FF'))
        grad.setStart(self.width() / 2, self.height() / 2 - e_point / 4)
        grad.setFinalStop(self.width() / 2, self.height() / 2 + e_point / 4)
        painter.setBrush(grad)
        # offset_x, offset_y, w, h
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.drawEllipse(self.width() / 2 - (e_point - self.background_offset) / 2,
                            self.height() / 2 - (e_point - self.background_offset) / 2,
                            e_point - self.background_offset, e_point - self.background_offset)
        svg = QSvgRenderer(self.filepath)
        # offset_x, offset_y, w, h
        svg.render(painter,
                   QRectF(self.width() / 2 - e_point / 2, self.height() / 2 - e_point / 2, e_point, e_point))
        painter.end()


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

    def __init__(self, output):
        super().__init__()
        self.mic = None
        self.mic_state = False
        self.output = output

    def record(self):
        self.mic = pyaudio.PyAudio()
        chunk = 1024  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16  # 16 bits per sample
        channels = 1
        rate = 16000
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
        with wave.open(self.output, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(self.mic.get_sample_size(sample_format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
        self.finished.emit()

    def toggle_record(self):
        print('toggle_record_audio')
        if self.mic_state:
            self.mic_state = False
        else:
            self.mic_state = True

    def get_output(self):
        return self.output

    def destroy(self):
        print('destroy_audio')
        self.mic_state = False


class MediaSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent=parent)
        self.last_pressed_button = None
        self.timer = QElapsedTimer()

    def mousePressEvent(self, e):
        self.last_pressed_button = e.button()
        if e.button() == Qt.LeftButton:
            if self.orientation() == Qt.Horizontal:
                pos = e.localPos().x()
                move_pos = pos / self.width()
                move_pos = self.maximum() * move_pos
            else:
                pos = self.height() - e.localPos().y()
                move_pos = pos / self.height()
                move_pos = self.maximum() * move_pos
            self.setValue(move_pos)
            self.timer.restart()
            self.timer.start()

    def mouseMoveEvent(self, e):
        if self.last_pressed_button == Qt.LeftButton and self.timer.elapsed() > 20:
            if self.orientation() == Qt.Horizontal:
                pos = self.mapFromGlobal(QCursor.pos()).x()
                move_pos = pos / self.width()
                move_pos = self.maximum() * move_pos
            else:
                pos = self.height() - self.mapFromGlobal(QCursor.pos()).y()
                move_pos = pos / self.height()
                move_pos = self.maximum() * move_pos
            self.setValue(move_pos)
            self.timer.restart()
            self.timer.start()


class MediaPlayerWidget(QWidget):
    def __init__(self, file, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #292929; border-radius: 15px}'
            'QLabel{color: #FFFFFF; background-color: red;}'
            'QPushButton{background: yellow;}'
            '#media_seek{margin: 0px; background: purple;}'
            '#media_seek::groove:horizontal{border-radius: 5px; height: 18px; margin: 20px 0px 20px 0px; background-color: silver;}'
            '#media_seek::handle:horizontal{border: 3px solid black; height: 20px; width: 20px; margin: -14px 0; border-radius: 5px; background-color: green;}'
            '#media_seek::sub-page:horizontal{border-radius: 5px; margin: 20px 0px 20px 0px; background-color: green;}'
            '#media_volume{margin: 0px;}'
            '#media_volume::groove:vertical{width: 18px; background: qlineargradient(x1:0.5, y1:0, x2:0.5, y2:0.25, x3:0.5, y3:1 stop:0 red, stop:0.25 yellow, stop:1 green);}'
            '#media_volume::handle:vertical{height: 10px; background: black}'
            '#media_volume::sub-page:vertical{background: silver;}'
        )
        self.setFocus()
        self.setFocusPolicy(Qt.StrongFocus)
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.area_layout = QGridLayout()
        self.process_widget = ProcessWidget(file, False, parent=self.parent())
        self.media_player = QMediaPlayer(flags=QMediaPlayer.VideoSurface, parent=self)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file)))
        self.value_change_loop_control = True
        self.media_player_widget = QVideoWidget(parent=self.area)
        self.control_button_play = QPushButton(parent=self.area)
        self.control_button_play.setFocusPolicy(Qt.NoFocus)
        self.control_button_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.control_button_play.setCursor(QCursor(Qt.PointingHandCursor))
        self.control_button_play.clicked.connect(self.toggle_play)
        self.control_button_stop = QPushButton(parent=self.area)
        self.control_button_stop.setFocusPolicy(Qt.NoFocus)
        self.control_button_stop.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.control_button_stop.setCursor(QCursor(Qt.PointingHandCursor))
        self.control_button_stop.clicked.connect(self.stop)
        self.control_button_mute = QPushButton(parent=self.area)
        self.control_button_mute.setFocusPolicy(Qt.NoFocus)
        self.control_button_mute.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.control_button_mute.setCursor(QCursor(Qt.PointingHandCursor))
        self.control_button_mute.clicked.connect(self.toggle_volume)
        self.media_slider = MediaSlider(Qt.Horizontal, parent=self.area)
        self.media_slider.setObjectName('media_seek')
        self.media_slider.setFocusPolicy(Qt.NoFocus)
        self.media_slider.setCursor(QCursor(Qt.PointingHandCursor))
        self.media_slider.valueChanged.connect(self.media_slider_value_changed)
        self.media_volume = MediaSlider(Qt.Vertical, parent=self.area)
        self.media_volume.setObjectName('media_volume')
        self.media_volume.setFocusPolicy(Qt.NoFocus)
        self.media_volume.setCursor(QCursor(Qt.PointingHandCursor))
        self.media_volume.setRange(0, 100)
        self.media_volume.setValue(self.media_player.volume())
        self.media_volume.valueChanged.connect(self.media_volume_value_changed)
        self.media_elapsed_time = QLabel('Elapsed', parent=self.area)
        self.media_elapsed_time.setAlignment(Qt.AlignCenter)
        self.media_remained_time = QLabel('Remained', parent=self.area)
        self.media_remained_time.setAlignment(Qt.AlignCenter)
        self.media_player.setVideoOutput(self.media_player_widget)
        self.media_player.stateChanged.connect(self.media_player_state_changed)
        self.media_player.positionChanged.connect(self.media_player_position_changed)
        self.media_player.durationChanged.connect(self.media_player_duration_changed)
        self.media_elapsed_time.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.media_remained_time.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.media_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.control_button_play.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.control_button_stop.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.control_button_mute.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.media_volume.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.media_player_widget, 0, 0, 8, 40)
        self.area_layout.addWidget(self.media_volume, 0, 40, 8, 1)
        self.area_layout.addWidget(self.media_elapsed_time, 8, 0, 1, 4)
        self.area_layout.addWidget(self.control_button_play, 8, 4, 1, 4)
        self.area_layout.addWidget(self.media_slider, 8, 8, 1, 24)
        self.area_layout.addWidget(self.control_button_stop, 8, 32, 1, 4)
        self.area_layout.addWidget(self.media_remained_time, 8, 36, 1, 4)
        self.area_layout.addWidget(self.control_button_mute, 8, 40, 1, 1)
        self.area.setLayout(self.area_layout)

    def toggle_play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def toggle_volume(self):
        if not self.media_player.isMuted():
            self.media_player.setMuted(True)
            self.control_button_mute.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
            temp = QGraphicsOpacityEffect()
            temp.setOpacity(0.25)
            self.media_volume.setGraphicsEffect(temp)
        else:
            self.media_player.setMuted(False)
            self.control_button_mute.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
            self.media_volume.setGraphicsEffect(None)

    def stop(self):
        self.media_player.stop()

    def media_player_state_changed(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.control_button_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.control_button_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def media_player_position_changed(self, position):
        self.value_change_loop_control = False
        self.media_slider.setValue(position)

    def media_player_duration_changed(self, duration):
        self.media_slider.setRange(0, duration)
        self.media_elapsed_time.setText('00:00:00')
        self.media_remained_time.setText(ms_to_time(duration))
        font, step = resize_font(self.media_remained_time)
        self.media_elapsed_time.setFont(font)
        self.media_remained_time.setFont(font)

    def media_slider_value_changed(self, val):
        if self.value_change_loop_control:
            self.media_player.setPosition(val)
        self.media_elapsed_time.setText(ms_to_time(val))
        self.value_change_loop_control = True

    def media_volume_value_changed(self, val):
        self.media_player.setVolume(val)

    def keyPressEvent(self, e):
        seek_inc, volume_inc = None, None
        key = e.key()
        if key == Qt.Key_Left:
            seek_inc = -10
        elif key == Qt.Key_Right:
            seek_inc = 10
        elif key == Qt.Key_Up:
            volume_inc = 5
        elif key == Qt.Key_Down:
            volume_inc = -5
        elif key == Qt.Key_Space:
            self.toggle_play()
            return
        else:
            return
        if seek_inc is not None:
            val = self.media_slider.value() + seek_inc * 1000
            if self.media_slider.minimum() <= val <= self.media_slider.maximum():
                self.media_slider.setValue(self.media_slider.value() + seek_inc * 1000)
            else:
                if val < self.media_slider.minimum():
                    self.media_slider.setValue(self.media_slider.minimum())
                else:
                    self.media_slider.setValue(self.media_slider.maximum())
        else:
            val = self.media_volume.value() + volume_inc
            if self.media_volume.minimum() <= val <= self.media_volume.maximum():
                self.media_volume.setValue(self.media_volume.value() + volume_inc)
            else:
                if val < self.media_volume.minimum():
                    self.media_volume.setValue(self.media_volume.minimum())
                else:
                    self.media_volume.setValue(self.media_volume.maximum())

    def resizeEvent(self, e):
        self.area.setFixedSize(self.width(), self.height())

    def showEvent(self, e):
        self.show()
        self.process_widget.show()


class VideoProcess(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(QImage)

    def __init__(self, output):
        super().__init__()
        self.cam = cv.VideoCapture(0)
        self.cam_state = True
        self.recorder = None
        self.recorder_state = False
        self.output = output

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
        self.cam.release()
        # cv.destroyAllWindows()
        self.finished.emit()
        print('video thread done')

    def toggle_record(self):
        print('toggle_record_video')
        if self.recorder is None:
            self.recorder = cv.VideoWriter(self.output, cv.VideoWriter_fourcc('m', 'p', '4', 'v'), 30,
                                           (int(self.cam.get(3)), int(self.cam.get(4))))
            self.recorder_state = True
        else:
            self.recorder.release()
            self.recorder = None
            self.recorder_state = False
            self.cam_state = False

    def get_output(self):
        return self.output

    def destroy(self):
        print('destroy_video')
        self.cam_state = False
        self.recorder_state = False
        self.cam.release()
        cv.destroyAllWindows()


class RecordWidget(QWidget):
    def __init__(self, record_type, parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #292929; border-radius: 15px}'
            '#area[cssClass~=disabled]{background: none;}'
            'QLabel{color: #FFFFFF;}'
            'QPushButton{background: transparent; border-color: none;}'
        )
        self.record_type = record_type
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.area_layout = QGridLayout()
        self.viewfinder = QLabel(parent=self.area)
        self.record_toggle_button = None
        self.record_timer = QElapsedTimer()
        self.record_repeater = QTimer(parent=self)
        self.record_repeater.timeout.connect(self.update_time)
        self.record_timer_text = QLabel(parent=self.area)
        self.record_timer_text.setText('00:00:00')
        self.record_timer_text.setVisible(False)
        self.worker_video = None
        self.worker_audio = None
        self.thread_video = None
        self.thread_audio = None
        self.timer_audio = QTimer()

    def render_default(self):
        clear_layout(self.area_layout)
        args = dict()
        if self.record_type == 'video':
            args['text'] = 'camera'
            args['svg'] = 'assets/video_record_red.svg'
            args['svg_aspect'] = (1, 1)
            args['button'] = 'record_video'
            args['button_connect'] = self.render_record_video
            cam = cv.VideoCapture(0, cv.CAP_DSHOW)
            if cam.isOpened():
                availability = True
            else:
                availability = False
            cam.release()
            cv.destroyAllWindows()
        else:
            args['text'] = 'microphone'
            args['svg'] = 'assets/audio_record_linear.svg'
            args['svg_aspect'] = (1, 1)
            args['button'] = 'record_audio'
            args['button_connect'] = self.render_record_audio
            mic = pyaudio.PyAudio()
            if mic.get_device_count() > 0:
                availability = True
            else:
                availability = False
            mic.terminate()
        text = QLabel(parent=self.area)
        if not availability:
            text.setText(f'Sorry this mode is not supported because you dont have a {args["text"]} available to record')
            self.area_layout.addWidget(text, 0, 0, alignment=Qt.AlignCenter)
            text.setWordWrap(True)
        else:
            self.area.setProperty('cssClass', 'disabled')
            self.area.setStyleSheet(self.styleSheet())
            text.setText('Click to start recording')
            record_button = SvgWidgetAspect(args['svg'], args['svg_aspect'], clickable=True, parent=self.area)
            record_button.setObjectName(args['button'])
            record_button.setCursor(QCursor(Qt.PointingHandCursor))
            record_button.connect(args['button_connect'])
            self.area_layout.addWidget(record_button, 0, 0, 1, 1, alignment=Qt.AlignCenter)
            self.area_layout.addWidget(text, 1, 0, 1, 1, alignment=Qt.AlignCenter)
        self.area.setLayout(self.area_layout)

    def render_record_video(self):
        clear_layout(self.area_layout, delete=True)
        self.record_timer_text.setVisible(True)
        self.record_toggle_button = QPushButton(parent=self.area)
        self.record_toggle_button.setIcon(QIcon(QPixmap('assets/video_record_red.svg')))
        self.record_toggle_button.clicked.connect(self.start_record)
        self.record_toggle_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.record_toggle_button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.record_timer_text, 0, 0, 0, 1, Qt.AlignCenter)
        self.area_layout.addWidget(self.viewfinder, 0, 1, 0, 2, Qt.AlignCenter)
        self.area_layout.addWidget(self.record_toggle_button, 0, 3, 0, 1, Qt.AlignCenter)
        self.area.setLayout(self.area_layout)
        if self.worker_video is None:
            self.worker_video = VideoProcess('record_video.mp4')
            self.thread_video = self.parent().parent().create_thread()
            self.worker_video.moveToThread(self.thread_video)
            self.thread_video.started.connect(self.worker_video.run)
            self.worker_video.progress.connect(self.update_pixmap)
            self.worker_video.finished.connect(self.thread_video.quit)  # is not working properly
        self.thread_video.start()

    def render_record_audio(self):
        clear_layout(self.area_layout, delete=True)
        self.record_timer_text.setVisible(True)
        self.record_toggle_button = CustomAudioSvgWidget(parent=self.area)
        self.record_toggle_button.setCursor(QCursor(Qt.PointingHandCursor))
        # self.record_toggle_button.setStyleSheet('background: qlineargradient(x1:0.5, y1:0, x2:0.5, y2:1 stop:0 #DA70D6, stop:1 #7F00FF); border-radius: 100%;')
        # self.record_toggle_button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.record_toggle_button, 0, 0, 1, 1, Qt.AlignCenter)
        self.area_layout.addWidget(self.record_timer_text, 1, 0, 1, 1, Qt.AlignCenter)
        self.area.setLayout(self.area_layout)
        self.timer_audio.timeout.connect(self.update_svg_circle)
        self.timer_audio.start(10)
        self.start_record()

    def start_record(self):
        print('start_record')
        if self.record_type == 'video':
            self.record_toggle_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            self.record_toggle_button.disconnect()
        else:
            self.record_toggle_button.connect(None)
        if self.record_type == 'video':
            self.record_toggle_button.clicked.connect(self.stop_record)
        else:
            self.record_toggle_button.connect(self.stop_record)
        if self.worker_audio is None:
            self.worker_audio = AudioProcess('record_audio.wav')
            self.thread_audio = self.parent().parent().create_thread()
            self.worker_audio.moveToThread(self.thread_audio)
            self.thread_audio.started.connect(self.worker_audio.record)
            self.worker_audio.finished.connect(self.thread_audio.quit)  # is not working properly
            self.worker_audio.finished.connect(self.worker_audio.deleteLater)  # is not working properly
        if self.record_type == 'video':
            self.toggle_record_video()
        self.toggle_record_audio()
        if self.record_type == 'video':
            self.record_toggle_button.setEnabled(False)
        else:
            self.record_toggle_button.setClickable(False)
        self.record_timer.start()
        self.record_repeater.start(100)

    def stop_record(self):
        print('stop_record')
        self.record_timer.restart()
        self.record_repeater.stop()
        if self.record_type == 'audio':
            self.timer_audio.stop()
        if self.record_type == 'video':
            self.toggle_record_video()
        self.toggle_record_audio()
        if self.thread_video:
            self.thread_video.quit()
            self.thread_video.wait()
        if self.thread_audio:
            self.thread_audio.quit()
            self.thread_audio.wait()
        if self.record_type == 'video':
            video = self.worker_video.get_output()
        audio = self.worker_audio.get_output()
        parent = self.parent()
        self.record_toggle_button.setCursor(QCursor(Qt.ArrowCursor))
        if self.record_type == 'video':
            merge(video, audio, 'record.mp4')
            output = 'record.mp4'
        else:
            output = 'record_audio.wav'
        clear_widget(self.parent())
        player = MediaPlayerWidget(output, parent=parent)
        player.setGeometry(128, 256, 1024, 512)
        player.show()

    def toggle_record_audio(self):
        self.worker_audio.toggle_record()
        if not self.thread_audio.isRunning():
            print('start audio thread')
            self.thread_audio.start()

    def toggle_record_video(self):
        self.worker_video.toggle_record()

    def update_svg_circle(self):
        current_offset = self.record_toggle_button.get_background_offset()
        max_offset = self.record_toggle_button.get_max_background_offset()
        if current_offset == 0:
            self.svg_circle_inc = max_offset / 100
        elif current_offset == max_offset:
            self.svg_circle_inc = -max_offset / 100
        self.record_toggle_button.set_background_offset(current_offset + self.svg_circle_inc)
        self.record_toggle_button.update()

    def update_pixmap(self, img):
        self.viewfinder.setPixmap(QPixmap.fromImage(img))

    def update_time(self):
        if self.record_type == 'video':
            if not self.record_toggle_button.isEnabled():
                self.record_toggle_button.setEnabled(True)
        else:
            if not self.record_toggle_button.clickable:
                self.record_toggle_button.setClickable(True)
        time_str = ms_to_time(self.record_timer.elapsed())
        self.record_timer_text.setText(time_str)

    def destroy(self):
        if self.worker_video:
            self.worker_video.destroy()
        if self.worker_audio:
            self.worker_audio.destroy()
        if self.thread_video:
            self.thread_video.quit()
        if self.thread_audio:
            self.thread_audio.quit()

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
    def __init__(self, files, file_process, parent=None):
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
        self.file_type = 'other'
        if not file_process:
            if files.split('.')[-1] == 'mp4':
                self.file_type = 'video'
            else:
                self.file_type = 'audio'
            self.record_area = QLabel(parent=self.area)
            self.record_area_layout = QVBoxLayout()
            if self.file_type == 'video':
                self.record_button = SvgWidgetAspect('assets/video_record_red.svg', (1, 1), clickable=True,
                                                     parent=self.record_area)
            else:
                self.record_button = SvgWidgetAspect('assets/audio_record_linear.svg', (1, 1), clickable=True,
                                                     parent=self.record_area)
            self.record_button.setCursor(QCursor(Qt.PointingHandCursor))
            self.record_button.connect(self.render_record_widget)
            self.record_area_layout.addWidget(self.record_button)
            self.record_area.setLayout(self.record_area_layout)
            if self.file_type == 'audio':
                self.total_areas = 2
                self.setGeometry(495, 820, 300, 150)
            else:
                self.total_areas = 3
        else:
            self.total_areas = 2
        if not self.file_type == 'audio':
            self.radio_area = QLabel(parent=self.area)
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
            self.audio_only = []
            self.video_only = []
            self.audio_video = []
        self.button_area = QLabel(parent=self.area)
        self.button_area_layout = QVBoxLayout()
        self.process_button = QPushButton('Process', parent=self.button_area)
        self.process_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.process_button.clicked.connect(self.process)
        self.button_area_layout.addWidget(self.process_button, alignment=Qt.AlignCenter)
        self.button_area.setLayout(self.button_area_layout)
        if not self.file_type == 'audio':
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

    def render_record_widget(self):
        parent = self.parent()
        clear_widget(self.parent())
        record_widget = RecordWidget(self.file_type, parent=parent)
        if self.file_type == 'video':
            record_widget.render_record_video()
        else:
            record_widget.render_default()
        record_widget.setGeometry(128, 256, 1024, 512)
        record_widget.show()

    def process(self):
        print('process')

    def resizeEvent(self, e):
        self.area.setGeometry(0, 0, self.width(), self.height())
        if self.total_areas == 3:
            self.record_area.setGeometry(0, 0, self.area.width() / self.total_areas, self.area.height())
            self.radio_area.setGeometry(self.area.width() / self.total_areas, 0, self.area.width() / self.total_areas,
                                        self.area.height())
            self.button_area.setGeometry(self.area.width() / self.total_areas * 2, 0,
                                         self.area.width() / self.total_areas, self.area.height())
        else:
            if not self.file_type == 'audio':
                self.radio_area.setGeometry(0, 0, self.area.width() / self.total_areas, self.area.height())
            else:
                self.record_area.setGeometry(0, 0, self.area.width() / self.total_areas, self.area.height())
            self.button_area.setGeometry(self.area.width() / self.total_areas, 0, self.area.width() / self.total_areas,
                                         self.area.height())
        # self.process_button.setGeometry(79, 37, 150, 75)
        if not self.file_type == 'audio':
            min_font = self.radio_button_preferred.font()
            for i in [self.radio_button_preferred, self.radio_button_audio_only, self.radio_button_video_only,
                      self.radio_button_audio_video]:
                font, step = resize_font(i)
                if font.pointSize() < min_font.pointSize():
                    min_font = font
            for i in [self.radio_button_preferred, self.radio_button_audio_only, self.radio_button_video_only,
                      self.radio_button_audio_video]:
                i.setFont(min_font)
        font, step = resize_font(self.process_button)
        self.process_button.setFont(font)


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
        self.upload_icon = SvgWidgetAspect('assets/file_upload_upload.svg', (176, 213), parent=self)

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
        self.audio_record.clicked.connect(self.render_audio_record)
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
        self.threads = []
        self.render_file_upload()

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

    def render_video_record(self):
        clear_widget(self.screen)
        self.clear_thread()
        screen_record_video = RecordWidget('video', parent=self.screen)
        screen_record_video.render_default()
        screen_record_video.setGeometry(128, 256, 1024, 512)
        screen_record_video.show()

    def render_audio_record(self):
        clear_widget(self.screen)
        self.clear_thread()
        screen_record_audio = RecordWidget('audio', parent=self.screen)
        screen_record_audio.render_default()
        screen_record_audio.setGeometry(128, 256, 1024, 512)
        screen_record_audio.show()

    def closeEvent(self, e):
        clear_widget(self)


def main():
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable high dpi scaling
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use high dpi icons
    app = QApplication([])
    window = MainWindow()
    # window = RecordWidget('audio')
    # window = MediaPlayerWidget('record_audio.wav')
    # window.render_default()
    # window.render_record_audio()
    # window.setFixedSize(1200, 800)
    window.show()
    app.exec_()
    print('Finished')


if __name__ == '__main__':
    main()
