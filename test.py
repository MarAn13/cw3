from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap, QImage
import sys
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject, QUrl
from PyQt5.QtMultimedia import QMultimedia, QAudioRecorder, QAudioEncoderSettings
import numpy as np
import cv2 as cv
import pyaudio
import wave


class AudioProcess(QObject):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mic = pyaudio.PyAudio()
        self.mic_state = False

    def record(self):
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


class VideoProcess(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
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


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet('QLabel{background-color: grey;}')
        self.setFixedSize(1000, 1000)
        self.pixmap = QLabel(self)
        self.pixmap.setGeometry(250, 250, 500, 500)
        self.button = QPushButton('Toggle', self)
        self.button.setGeometry(400, 800, 200, 100)
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = VideoProcess()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.update_pixmap)
        self.thread_audio = QThread()
        self.worker_audio = AudioProcess()
        self.worker_audio.moveToThread(self.thread_audio)
        self.thread_audio.started.connect(self.worker_audio.record)
        self.thread_audio.finished.connect(self.worker_audio.deleteLater)
        self.thread_audio.finished.connect(self.thread_audio.deleteLater)
        self.button.clicked.connect(self.toggle_record)
        self.button.clicked.connect(self.toggle_record_audio)

        # Step 6: Start the thread
        self.thread.start()

    def toggle_record_audio(self):
        self.worker_audio.toggle_record()
        self.thread_audio.start()

    def toggle_record(self):
        self.worker.toggle_record()

    def update_pixmap(self, img):
        self.pixmap.setPixmap(QPixmap.fromImage(img))


# @pyqtSlot(np.ndarray)
#     def update_image(self, cv_img):
#         """Updates the image_label with a new opencv image"""
#         qt_img = self.convert_cv_qt(cv_img)
#         self.image_label.setPixmap(qt_img)
#
#     def convert_cv_qt(self, cv_img):
#         """Convert from an opencv image to QPixmap"""
#         rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
#         h, w, ch = rgb_image.shape
#         bytes_per_line = ch * w
#         convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
#         p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
#         return QPixmap.fromImage(p)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())
