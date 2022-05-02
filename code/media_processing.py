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