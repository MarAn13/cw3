"""
Record processing
"""
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QGridLayout, QSizePolicy, QStyle
from PyQt5.Qt import Qt
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QElapsedTimer
from PyQt5.QtGui import QImage, QCursor, QIcon, QPixmap
from ui_utils import clear_widget, clear_layout, ms_to_time
from utils import merge
from responsive_svg import SvgWidgetAspect, CustomAudioSvgWidget
import pyaudio
import wave
import cv2 as cv


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
            args['svg'] = '../assets/video_record_red.svg'
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
            args['svg'] = '../assets/audio_record_linear.svg'
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
        self.area.setProperty('cssClass', None)
        self.area.setStyleSheet(self.styleSheet())
        self.record_timer_text.setVisible(True)
        self.record_toggle_button = QPushButton(parent=self.area)
        self.record_toggle_button.setIcon(QIcon(QPixmap('../assets/video_record_red.svg')))
        self.record_toggle_button.clicked.connect(self.start_record)
        self.record_toggle_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.record_toggle_button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.record_timer_text, 0, 0, 0, 1, Qt.AlignCenter)
        self.area_layout.addWidget(self.viewfinder, 0, 1, 0, 2, Qt.AlignCenter)
        self.area_layout.addWidget(self.record_toggle_button, 0, 3, 0, 1, Qt.AlignCenter)
        self.area.setLayout(self.area_layout)
        if self.worker_video is None:
            self.worker_video = VideoProcess('temp/record_video.mp4')
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
            self.worker_audio = AudioProcess('temp/record_audio.wav')
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
        parent = self.parent().parent()
        self.record_toggle_button.setCursor(QCursor(Qt.ArrowCursor))
        if self.record_type == 'video':
            merge(video, audio, 'temp/record.mp4')
            output = 'temp/record.mp4'
        else:
            output = 'temp/record_audio.wav'
        clear_widget(self.parent())
        parent.render_media_process(output)

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
