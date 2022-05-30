"""
Processing media
"""
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QRadioButton, QSlider, QGridLayout, QVBoxLayout, QStyle, \
    QSizePolicy, QGraphicsOpacityEffect
from PyQt5.Qt import Qt
from PyQt5.QtCore import QElapsedTimer, QUrl
from PyQt5.QtGui import QCursor, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import pyqtgraph as pg
from ui_utils import ms_to_time, resize_font, clear_widget
from utils import check_streams, get_from_file, change_config_file, change_file
from responsive_svg import SvgWidgetAspect, ResponsiveIconButton
from result_processing import ResultWidget, ResultProcess, LoadingScreen
import os
import numpy as np
from scipy.io import wavfile


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
            self.timer.start()


class MediaPlayerWidget(QWidget):
    def __init__(self, file, file_type='video', parent=None):
        super().__init__(parent=parent)
        self.setStyleSheet(
            '#area{background-color: #292929; border-radius: 15px}'
            'QLabel{color: #FFFFFF;}'
            '#media_seek{margin: 0px;}'
            '#media_seek::groove:horizontal{border-radius: 5px; height: 18px; margin: 20px 0px 20px 0px; background-color: silver;}'
            '#media_seek::handle:horizontal{border: 3px solid black; height: 20px; width: 20px; margin: -14px 0; border-radius: 5px; background-color: green;}'
            '#media_seek::sub-page:horizontal{border-radius: 5px; margin: 20px 0px 20px 0px; background-color: green;}'
            '#media_volume{margin: 0px;}'
            '#media_volume::groove:vertical{width: 18px; background: qlineargradient(x1:0.5, y1:0, x2:0.5, y2:0.25, x3:0.5, y3:1 stop:0 red, stop:0.25 yellow, stop:1 green);}'
            '#media_volume::handle:vertical{height: 10px; background: black}'
            '#media_volume::sub-page:vertical{background: silver;}'
            'QPushButton{background-color: transparent;}'
        )
        self.setFocus()
        self.setFocusPolicy(Qt.StrongFocus)
        self.source = file
        self.file_type = file_type
        self.area = QWidget(parent=self)
        self.area.setObjectName('area')
        self.area_layout = QGridLayout()
        self.process_widget = self.parent().parent().render_process_widget(file, False)
        self.media_player = QMediaPlayer(flags=QMediaPlayer.VideoSurface, parent=self)
        self.media_player.setNotifyInterval(10)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file)))
        self.value_change_loop_control = True
        if file_type == 'video':
            self.media_player_widget = QVideoWidget(parent=self.area)
            self.media_player.setVideoOutput(self.media_player_widget)
        else:
            self.media_player_widget = pg.PlotWidget(parent=self.area)
            self.media_player_widget_line = pg.InfiniteLine(pen=pg.mkPen(color=QColor('green'), width=5))
        self.control_button_play = ResponsiveIconButton('../assets/media_play.svg', parent=self.area)
        self.control_button_play.setBrushColor('transparent')
        self.control_button_play.setFocusPolicy(Qt.NoFocus)
        self.control_button_play.setCursor(QCursor(Qt.PointingHandCursor))
        self.control_button_play.clicked.connect(self.toggle_play)
        self.control_button_stop = ResponsiveIconButton('../assets/media_stop.svg', parent=self.area)
        self.control_button_stop.setBrushColor('transparent')
        self.control_button_stop.setFocusPolicy(Qt.NoFocus)
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
            self.control_button_play.setSVG('../assets/media_pause.svg')
        else:
            self.control_button_play.setSVG('../assets/media_play.svg')

    def media_player_position_changed(self, position):
        self.value_change_loop_control = False
        self.media_slider.setValue(position)
        if self.file_type == 'audio':
            self.media_player_widget.removeItem(self.media_player_widget_line)
            self.media_player_widget_line.setPos(position / 1000)
            self.media_player_widget.addItem(self.media_player_widget_line)

    def media_player_duration_changed(self, duration):
        self.media_slider.setRange(0, duration)
        self.media_elapsed_time.setText('00:00:00')
        self.media_remained_time.setText(ms_to_time(duration))
        font, step = resize_font(self.media_remained_time)
        self.media_elapsed_time.setFont(font)
        self.media_remained_time.setFont(font)
        if self.file_type == 'audio':
            samplerate, data = wavfile.read(self.source)
            x = np.linspace(0, duration / 1000, len(data))
            self.media_player_widget.plot(x, data)
            range = self.media_player_widget.getViewBox().viewRange()
            self.media_player_widget.getViewBox().setLimits(xMin=range[0][0], xMax=range[0][1],
                                         yMin=range[1][0], yMax=range[1][1])
            self.media_player_widget.setBackground(QColor('#292929'))

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


class ProcessWidget(QWidget):
    def __init__(self, files, file_process, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            '#area{background-color: #2D2D2D; border-radius: 15px;}'
            'QPushButton{color: #50C878;background-color: #303933;border: 1px solid #3E3E3E;border-radius: 15px;}'
            'QRadioButton{color: #FFFFFF;}'
            'QRadioButton::indicator{width: 10px; height: 10px; background-color: #FFFFFF;}'
            'QRadioButton::indicator::checked{image: url(../assets/radio_button_indicator.svg);}'
            'QRadioButton[cssClass~=disabled]{color: grey;}'
            'QRadioButton::indicator[cssClass~=disabled]{background-color: grey;}'
        )
        # self.setGeometry(345, 820, 600, 150)
        self.area = QLabel(parent=self)
        self.area.setObjectName('area')
        self.file_type = 'other'
        if not file_process:
            if files.split('.')[-1] == 'mp4':
                self.file_type = 'video'
            else:
                self.file_type = 'audio'
            files = [files]
            self.record_area = QLabel(parent=self.area)
            self.record_area_layout = QVBoxLayout()
            if self.file_type == 'video':
                self.record_button = SvgWidgetAspect('../assets/video_record_red.svg', (1, 1), clickable=True,
                                                     parent=self.record_area)
            else:
                self.record_button = SvgWidgetAspect('../assets/audio_record_linear.svg', (1, 1), clickable=True,
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
            self.radio_button_preferred.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.radio_button_preferred.setChecked(True)
            self.radio_button_audio_only = QRadioButton('audio-only', parent=self.radio_area)
            self.radio_button_audio_only.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.radio_button_video_only = QRadioButton('video-only', parent=self.radio_area)
            self.radio_button_video_only.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.radio_button_audio_video = QRadioButton('audio-video', parent=self.radio_area)
            self.radio_button_audio_video.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
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
        self.result = {
            'audio-only': None,
            'video-only': None,
            'audio-video': None
        }
        self.threads = []
        self.workers = []
        files = [os.path.abspath(file) for file in files]
        if not self.file_type == 'audio':
            self.check_files(files)
        else:
            self.audio_only = files

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
        parent = self.parent().parent()
        record_widget = parent.render_record(self.file_type)
        if self.file_type == 'video':
            record_widget.render_record_video()

    def process(self):
        parent = self.parent().parent()
        if parent.screen_widgets['media_widget']:
            parent.screen_widgets['media_widget'].setVisible(False)
        if parent.screen_widgets['file_upload_widget']:
            parent.screen_widgets['file_upload_widget'].setVisible(False)
        self.setVisible(False)
        parent.render_loading_screen()
        config = get_from_file('config.txt', '')
        if self.file_type != 'audio':
            if self.radio_button_preferred.isChecked():
                raw_files = [[self.audio_only, 'audio-only'], [self.video_only, 'video-only'],
                             [self.audio_video, 'audio-video']]
            elif self.radio_button_audio_only.isChecked():
                raw_files = [[self.audio_only + self.audio_video, 'audio-only']]
                self.result['video-only'] = []
                self.result['audio-video'] = []
            elif self.radio_button_video_only.isChecked():
                raw_files = [[self.video_only + self.audio_video, 'video-only']]
                self.result['audio-only'] = []
                self.result['audio-video'] = []
            else:
                raw_files = [[self.audio_video, 'audio-video']]
                self.result['audio-only'] = []
                self.result['video-only'] = []
        else:
            raw_files = [[self.audio_only, 'audio-only']]
            self.result['video-only'] = []
            self.result['audio-video'] = []
        for files, mode in raw_files:
            if len(files) > 0:
                data = get_from_file('data.txt', '')
                param = mode[0].upper() + mode[1:] + ' used'
                change_file('data.txt', param, int(data[param]) + len(files))
                for param, param_val in [['TEST_DEMO_DECODING', config['Decoder']],
                                         ['TEST_DEMO_NOISY', config['Use noise']],
                                         ['USE_LM', config['Use LM']], ['NOISE_SNR_DB', int(config['Audio SNR'])]]:
                    change_config_file(mode, param, param_val)
                thread = parent.create_thread()
                worker = ResultProcess(files, mode, int(config['Video SNR']))
                worker.moveToThread(thread)
                thread.started.connect(worker.process)
                worker.finished.connect(self.process_result)
                thread.start()
                self.threads.append(thread)
                self.workers.append(worker)
            else:
                self.result[mode] = []

    def process_result(self, result, mode):
        self.result[mode] = result
        if self.result['audio-only'] is not None and self.result['video-only'] is not None and self.result[
            'audio-video'] is not None:
            result = dict()
            for mode, res in self.result.items():
                if len(res) != 0:
                    for key, val in res.items():
                        res[key] = [mode, val]
                result.update(res)
            self.parent().parent().render_result_process(result)

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
            min_font.setPointSize(min_font.pointSize() - 1)
            for i in [self.radio_button_preferred, self.radio_button_audio_only, self.radio_button_video_only,
                      self.radio_button_audio_video]:
                i.setFont(min_font)
        font, step = resize_font(self.process_button)
        self.process_button.setFont(font)