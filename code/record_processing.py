"""
Record processing
"""
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QGridLayout, QSizePolicy, QStyle
from PyQt5.Qt import Qt
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QElapsedTimer, QMutex, QWaitCondition
from PyQt5.QtGui import QImage, QCursor, QIcon, QPixmap
from ui_utils import clear_widget, clear_layout, ms_to_time
from utils import merge
from responsive_svg import SvgWidgetAspect, CustomAudioSvgWidget, ResponsiveIconButton
import pyaudio
import wave
import cv2 as cv
import os
import shutil


class MergeProcess(QObject):
    finished = pyqtSignal(str)

    def __init__(self, input_video, input_audio, output):
        super().__init__()
        self.input_video = input_video
        self.input_audio = input_audio
        self.output = output

    def run(self):
        merge(self.input_video, self.input_audio, self.output)
        self.finished.emit(self.output)


class AudioProcess(QObject):
    finished = pyqtSignal(str)

    def __init__(self, output):
        super().__init__()
        self.mic = None
        self.mic_state = False
        self.mic = pyaudio.PyAudio()
        self.mic_options_chunk = 1024  # Record in chunks of 1024 samples
        self.mic_options_sample_format = pyaudio.paInt16  # 16 bits per sample
        self.mic_options_channels = 1
        self.mic_options_rate = 16000
        self.output = output

    def run(self):
        stream = self.mic.open(
            format=self.mic_options_sample_format,
            channels=self.mic_options_channels,
            rate=self.mic_options_rate,
            frames_per_buffer=self.mic_options_chunk,
            input=True
        )
        frames = []
        check = False
        while self.mic_state:
            if not check:
                from datetime import datetime
                now = datetime.now()

                current_time = now.strftime("%H:%M:%S")

                print('audio', "Current Time is :", current_time)
                check = True
            data = stream.read(self.mic_options_chunk)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        self.mic.terminate()
        print('audio', len(frames),
              self.mic_options_rate / self.mic_options_chunk * len(frames) / self.mic_options_chunk)
        with wave.open(self.output, 'wb') as wf:
            wf.setnchannels(self.mic_options_channels)
            wf.setsampwidth(self.mic.get_sample_size(self.mic_options_sample_format))
            wf.setframerate(self.mic_options_rate)
            wf.writeframes(b''.join(frames))
        self.finished.emit('audio')

    def toggle_record(self):
        print('toggle_record_audio')
        if self.mic_state:
            self.mic_state = False
        else:
            self.mic_state = True

    def get_output(self):
        return self.output

    def destroy(self):
        self.mic_state = False


class VideoProcess(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(QImage)

    def __init__(self, output, mutex, cond):
        super().__init__()
        self.cam = cv.VideoCapture(0)
        self.cam.set(3, 1200)
        self.cam.set(4, 1200)
        self.fps = 30
        self.cam.set(cv.CAP_PROP_FPS, self.fps)
        self.cam_state = True
        self.recorder_state = False
        self.mutex = mutex
        self.cond = cond
        self.output = output

    def run(self):
        frames = []
        check = False
        while self.cam_state:
            ret, frame = self.cam.read()
            if ret:
                frame = cv.flip(frame, 1)
                frame_process = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                height, width, channel = frame_process.shape
                step = channel * width
                img = QImage(frame_process.data, width, height, step, QImage.Format_RGB888)
                self.progress.emit(img)
                self.cond.wait(self.mutex)
                if self.recorder_state:
                    if not check:
                        from datetime import datetime
                        now = datetime.now()

                        current_time = now.strftime("%H:%M:%S")

                        print('video', "Current Time is :", current_time)
                        check = True
                    frames.append(frame)
        print('video', len(frames), len(frames) / self.fps)
        recorder = cv.VideoWriter(self.output, cv.VideoWriter_fourcc('m', 'p', '4', 'v'), self.fps,
                                  (int(self.cam.get(3)), int(self.cam.get(4))))
        if self.cam.isOpened():
            self.cam.release()
        for frame in frames:
            recorder.write(frame)
        recorder.release()
        self.finished.emit('video')

    def toggle_record(self):
        print('toggle_record_video')
        if self.recorder_state:
            self.recorder_state = False
            self.cam_state = False
        else:
            self.recorder_state = True

    def get_output(self):
        return self.output

    def destroy(self):
        self.cam_state = False
        self.recorder_state = False


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
        self.mutex = QMutex()
        self.cond = QWaitCondition()
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
            cam = cv.VideoCapture(0)
            if cam.isOpened():
                cam.release()
                availability = True
            else:
                availability = False
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
        self.preprocess_state = {
            'video': not self.record_type == 'video',
            'audio': False
        }

    def render_record_video(self):
        clear_layout(self.area_layout, delete=True)
        self.area.setProperty('cssClass', None)
        self.area.setStyleSheet(self.styleSheet())
        self.record_timer_text.setVisible(True)
        self.record_toggle_button = ResponsiveIconButton('../assets/video_record_red.svg', parent=self.area)
        self.record_toggle_button.setBrushColor('transparent')
        self.record_toggle_button.clicked.connect(self.start_record)
        self.record_toggle_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.record_toggle_button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.viewfinder.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.area_layout.addWidget(self.record_timer_text, 1, 0, 1, 1)
        self.area_layout.addWidget(self.viewfinder, 0, 1, 3, 4)
        self.area_layout.addWidget(self.record_toggle_button, 1, 5, 1, 1)
        self.area.setLayout(self.area_layout)
        if self.worker_video is None:
            self.mutex.lock()
            self.worker_video = VideoProcess('temp/record_video.mp4', self.mutex, self.cond)
            self.thread_video = self.parent().parent().create_thread()
            self.worker_video.moveToThread(self.thread_video)
            self.thread_video.started.connect(self.worker_video.run)
            self.worker_video.progress.connect(self.update_pixmap)
            self.worker_video.finished.connect(self.preprocess)
            self.worker_video.finished.connect(self.thread_video.quit)
        self.thread_video.start()

    def render_record_audio(self):
        clear_layout(self.area_layout, delete=True)
        self.record_timer_text.setVisible(True)
        self.record_toggle_button = CustomAudioSvgWidget(parent=self.area)
        self.record_toggle_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.area_layout.addWidget(self.record_toggle_button, 0, 0, 1, 1, Qt.AlignCenter)
        self.area_layout.addWidget(self.record_timer_text, 1, 0, 1, 1, Qt.AlignCenter)
        self.area.setLayout(self.area_layout)
        self.timer_audio.timeout.connect(self.update_svg_circle)
        self.timer_audio.start(10)
        self.start_record()

    def start_record(self):
        if self.record_type == 'video':
            self.record_toggle_button.setSVG('../assets/media_stop.svg')
            self.record_toggle_button.disconnect()
            self.record_toggle_button.clicked.connect(self.stop_record)
        else:
            self.record_toggle_button.connect(self.stop_record)
        if self.worker_audio is None:
            self.worker_audio = AudioProcess('temp/record_audio.wav')
            self.thread_audio = self.parent().parent().create_thread()
            self.worker_audio.moveToThread(self.thread_audio)
            self.thread_audio.started.connect(self.worker_audio.run)
            self.worker_audio.finished.connect(self.preprocess)
            self.worker_audio.finished.connect(self.thread_audio.quit)
        self.toggle_record()
        if self.record_type == 'video':
            self.record_toggle_button.setEnabled(False)
        else:
            self.record_toggle_button.setClickable(False)
        self.record_timer.start()
        self.record_repeater.start(100)

    def stop_record(self):
        self.record_timer.restart()
        self.record_repeater.stop()
        if self.record_type == 'audio':
            self.timer_audio.stop()
        self.toggle_record()
        self.record_toggle_button.setCursor(QCursor(Qt.ArrowCursor))
        self.setVisible(False)
        self.parent().parent().render_loading_screen()

    def toggle_record(self):
        if self.worker_video is not None:
            self.worker_video.toggle_record()
        self.worker_audio.toggle_record()
        if not self.thread_audio.isRunning():
            self.thread_audio.start()

    def preprocess(self, process_name):
        self.preprocess_state[process_name] = True
        if not self.preprocess_state['video'] or not self.preprocess_state['audio']:
            return
        audio = self.worker_audio.get_output()
        if self.record_type == 'video':
            video = self.worker_video.get_output()
            self.worker_merge = MergeProcess(video, audio, 'temp/record.mp4')
            self.thread_merge = self.parent().parent().create_thread()
            self.worker_merge.moveToThread(self.thread_merge)
            self.thread_merge.started.connect(self.worker_merge.run)
            self.worker_merge.finished.connect(self.preprocess_output)
            self.worker_merge.finished.connect(self.thread_merge.quit)
            self.thread_merge.start()

    def preprocess_output(self, output):
        if True:
            dst_path = 'data/record_'
            index = 0
            while os.path.exists(f'{dst_path + str(index)}.mp4'):
                index += 1
            shutil.copyfile(output, f'{dst_path + str(index)}.mp4')
        self.parent().parent().render_media_process(output)

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
        self.mutex.lock()
        self.viewfinder.setPixmap(
            QPixmap.fromImage(img).scaled(self.viewfinder.width(), self.viewfinder.height(), Qt.KeepAspectRatio))
        self.mutex.unlock()
        self.cond.wakeAll()

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
