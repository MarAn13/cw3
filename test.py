from PyQt5.QtWidgets import (QWidget, QSlider, QLineEdit, QLabel, QPushButton, QScrollArea, QApplication,
                             QHBoxLayout, QVBoxLayout, QMainWindow, QGridLayout)
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics, QPainter, QImage
from PyQt5.Qt import QSizePolicy, QCamera, QVideoEncoderSettings, QMediaRecorder, QUrl, QFile, QMultimedia, QCameraViewfinder, QCameraInfo
from PyQt5.QtSvg import QSvgRenderer, QSvgWidget
import sys



class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedSize(1000, 1000)
        self.widget = QWidget(parent=self)
        self.widget.setFixedSize(self.size())
        self.layout = QHBoxLayout()
        self.camera = None
        self.viewfinder = QCameraViewfinder()
        available_cameras = QCameraInfo.availableCameras()
        if not available_cameras:
            return False
        self.set_camera(available_cameras[0])
        self.layout.addWidget(self.viewfinder)
        self.viewfinder.show()
        self.show()
        self.widget.setLayout(self.layout)
        return
        recorder_video_settings = recorder.videoSettings()
        recorder_video_settings.setQuality(QMultimedia.VeryHighQuality)
        recorder_video_settings.setFrameRate(30)
        recorder_video_settings.setCodec('video/mp4')
        recorder.setVideoSettings(recorder_video_settings)
        recorder.setContainerFormat('mp4')
        camera.setCaptureMode(QCamera.CaptureVideo)
        camera.focus()
        save_file = QFile('test_record_0.mp4')
        recorder.setOutputLocation(QUrl.fromLocalFile(save_file.fileName()))
        recorder.record()
        return

    def set_camera(self, cam):
        # getting the selected camera
        self.camera = QCamera(cam)
        # setting view finder to the camera
        self.camera.setViewfinder(self.viewfinder)
        # setting capture mode to the camera
        self.camera.setCaptureMode(QCamera.CaptureVideo)
        # start the camera
        self.camera.start()

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
