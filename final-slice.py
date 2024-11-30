from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread
from multiprocessing import Process, Queue, Pipe

from datetime import datetime
import time

import traceback

from pydub import AudioSegment, effects, utils, generators
from pydub.utils import which
AudioSegment.converter = which("ffmpeg")
import math

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize, CoUninitialize
CLSCTX_ALL = 7

import importlib

icons = importlib.import_module('compiled-ui.icons')
database_functions = importlib.import_module("python+.lib.sqlite3-functions")
convert_time_function = importlib.import_module("python+.lib.convert-time-function")
manage_processes_class = importlib.import_module("python+.main-window.manage-processes.manage-processes")

class Final_Slice:

    def __init__(self, main_self):
        try:
            self.main_self = main_self

            self.put_to_plot = False
            self.put_to_pyaudio = False
            self.put_to_record = False

            # create process
            self.create_process()
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def create_process(self):
        try:
            self.process_number = 9

            self.mother_pipe, self.child_pipe = Pipe()
            self.queue = Queue()
            self.deck_1_queue = Queue()
            self.deck_2_queue = Queue()
            self.music_clip_deck_queue = Queue()
            self.speackers_deck_queue = Queue()
            self.ip_call_1_queue = Queue()
            self.ip_call_2_queue = Queue()
            self.ip_call_3_queue = Queue()

            self.emitter = Emitter(self.mother_pipe)
            self.emitter.error_signal.connect(lambda error_message: self.main_self.open_final_slice_error_window(error_message))
            self.emitter.general_deck_settings.connect(lambda settings: self.general_deck_settings(settings))
            self.emitter.final_slice_ready.connect(lambda slice: self.final_slice_ready(slice))
            self.emitter.windows_volume.connect(lambda volume: self.windows_volume_changed_set_value(volume))
            self.emitter.play_previous_result.connect(lambda result: self.play_previous_result(result))
            self.emitter.start()

            self.child_process = Child_Proc(self.child_pipe, self.queue,self.deck_1_queue,self.deck_2_queue,self.music_clip_deck_queue,self.speackers_deck_queue,self.ip_call_1_queue,self.ip_call_2_queue,self.ip_call_3_queue,self.main_self.sync_processes_instance.condition, self.main_self.sync_processes_instance.frame,self.main_self.sync_processes_instance.quit_event,self.main_self.configuration)
            self.child_process.start()

            manage_processes_class.init_process(self)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def general_deck_settings(self,settings):
        try:
            self.settings = settings

            # general deck play previous
            self.main_self.ui.general_deck_play_previous.clicked.connect(lambda  state:self.play_previous())

            # general deck play or pause
            self.main_self.ui.general_deck_play_or_pause.setStatusTip("Αναπαραγωγή ή παύση όλων. Πατήστε για αναπαραγωγή.")
            self.main_self.ui.general_deck_play_or_pause.clicked.connect(lambda:self.play_or_pause_all())

            # general deck stop all
            self.main_self.ui.general_deck_stop.clicked.connect(lambda: self.stop_all())

            # general deck play next
            self.main_self.ui.general_deck_play_next.clicked.connect(lambda: self.play_next())

            # general deck volume menu
            self.create_menu_for_volume()

            # general deck pan menu
            self.create_menu_for_pan()

            # general deck normalize menu
            self.create_menu_for_normalize()

            # general deck filter menu
            self.create_menu_for_filter()

            # genral deck windows volume menu
            self.create_menu_for_windows_volume()
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def play_previous(self):
        try:
            now = datetime.now()

            #1. stop music clip deck
            self.main_self.ui.music_clip_deck_stop.click()

            #2. stop deck 1
            self.main_self.ui.deck_1_stop.click()

            #3. stop deck 2
            self.main_self.ui.deck_2_stop.click()

            #4. stop speackers deck
            if self.main_self.speackers_deck_instance.deck_status != "stopped":
                self.main_self.ui.speackers_deck_click_to_talk.click()

            time.sleep(self.configuration["sync_cycle_ms"]/1000)

            #5. search for previous in player history
            self.queue.put({"type":"play-previous","now":now})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def play_or_pause_all(self):
        try:
            btn_status_tip = self.main_self.ui.general_deck_play_or_pause.statusTip()
            if btn_status_tip == "Αναπαραγωγή ή παύση όλων. Πατήστε για αναπαραγωγή.":
                self.main_self.ui.general_deck_play_or_pause.setStatusTip("Αναπαραγωγή ή παύση όλων. Πατήστε για παύση.")
                self.main_self.ui.statusbar.showMessage("Αναπαραγωγή ή παύση όλων. Πατήστε για παύση.")

                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/pause-song.png"),QtGui.QIcon.Normal, QtGui.QIcon.Off)
                self.main_self.ui.general_deck_play_or_pause.setIcon(icon)

                if self.main_self.deck_1_instance.deck_status != "playing":
                    self.main_self.deck_1_instance.play_or_pause_clicked()
                if self.main_self.deck_2_instance.deck_status != "playing":
                    self.main_self.deck_2_instance.play_or_pause_clicked()
                if self.main_self.music_clip_deck_instance.deck_status != "playing":
                    self.main_self.music_clip_deck_instance.play_or_pause_clicked()
            else:
                self.main_self.ui.general_deck_play_or_pause.setStatusTip("Αναπαραγωγή ή παύση όλων. Πατήστε για αναπαραγωγή.")
                self.main_self.ui.statusbar.showMessage("Αναπαραγωγή ή παύση όλων. Πατήστε για αναπαραγωγή.")

                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/play-song.png"),QtGui.QIcon.Normal, QtGui.QIcon.Off)
                self.main_self.ui.general_deck_play_or_pause.setIcon(icon)

                if self.main_self.deck_1_instance.deck_status != "paused":
                    self.main_self.deck_1_instance.play_or_pause_clicked()
                if self.main_self.deck_2_instance.deck_status != "paused":
                    self.main_self.deck_2_instance.play_or_pause_clicked()
                if self.main_self.music_clip_deck_instance.deck_status != "paused":
                    self.main_self.music_clip_deck_instance.play_or_pause_clicked()
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def stop_all(self):
        try:
            self.main_self.deck_1_instance.stop_button_clicked()
            self.main_self.deck_2_instance.stop_button_clicked()
            self.main_self.music_clip_deck_instance.stop_button_clicked()
            if self.main_self.speackers_deck_instance.deck_status != "stopped":
                self.main_self.ui.speackers_deck_click_to_talk.click()
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def play_next(self):
        try:
            self.stop_all()
            #to be completed load next item from player list
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def create_menu_for_volume(self):
        try:
            self.menu_for_volume = QtWidgets.QMenu(self.main_self.ui.general_deck_application_volume)
            self.main_self.ui.general_deck_application_volume.setMenu(self.menu_for_volume)

            self.volume_frame = Custom_QFrame(self.menu_for_volume)
            self.volume_frame.installEventFilter(self.volume_frame)
            self.volume_frame.setFixedWidth(600)
            self.volume_frame.setStyleSheet("QFrame{border:1px solid #ABABAB;background-color:rgb(253,253,253);}")
            self.volume_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.volume_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.volume_frame.setObjectName("volume_frame")

            self.volume_horizontalLayout = QtWidgets.QHBoxLayout(self.volume_frame)
            self.volume_horizontalLayout.setObjectName("volume_horizontalLayout")
            self.volume_label = QtWidgets.QLabel(self.volume_frame)
            self.volume_label.setStyleSheet("QLabel{border:none;}")
            self.volume_label.setObjectName("volume_label")
            self.volume_horizontalLayout.addWidget(self.volume_label)

            self.volume_slider = QtWidgets.QSlider(self.volume_frame)
            self.volume_slider.setMaximum(200)
            self.volume_slider.setProperty("value", self.settings["volume"])
            self.volume_slider.setOrientation(QtCore.Qt.Horizontal)
            self.volume_slider.setObjectName("volume_slider")
            self.volume_horizontalLayout.addWidget(self.volume_slider)

            self.volume_label_2 = QtWidgets.QLabel(self.volume_frame)
            self.volume_label_2.setObjectName("volume_label_2")
            self.volume_label_2.setStyleSheet("QLabel{border:none;}")
            self.volume_horizontalLayout.addWidget(self.volume_label_2)

            self.volume_reset = QtWidgets.QPushButton(self.volume_frame)
            self.volume_reset.setMinimumSize(QtCore.QSize(0, 29))
            self.volume_reset.setObjectName("volume_reset")
            self.volume_horizontalLayout.addWidget(self.volume_reset)

            self.volume_label.setText("Ρύθμιση έντασης ήχου:")
            self.volume_label_2.setText(str(self.settings["volume"])+"/200")
            self.volume_reset.setText("Επαναφορά (100/200)")

            # on sound volume changed
            self.volume_slider.valueChanged.connect(lambda slider_value: self.volume_changed(slider_value))

            # on sound volume apply new value
            self.volume_slider.sliderReleased.connect(lambda: self.volume_released())

            # on sound volume pressed
            self.volume_slider.actionTriggered.connect(lambda action: self.volume_action_triggered(action))

            # on sound volume reset
            self.volume_reset.clicked.connect(lambda state: self.volume_resetted())

            volume_widget = QtWidgets.QWidgetAction(self.menu_for_volume)
            volume_widget.setDefaultWidget(self.volume_frame)
            self.menu_for_volume.addAction(volume_widget)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def volume_changed(self, slider_value):
        try:
            self.volume_label_2.setText(str(slider_value) + "/200")
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def volume_released(self):
        try:
            slider_value = self.volume_slider.value()
            self.queue.put({"type": "volume", "value_base_100": slider_value})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def volume_action_triggered(self, action):
        try:
            if action == QtWidgets.QAbstractSlider.SliderSingleStepAdd or action == QtWidgets.QAbstractSlider.SliderSingleStepSub or action == QtWidgets.QAbstractSlider.SliderPageStepAdd or action == QtWidgets.QAbstractSlider.SliderPageStepSub:
                self.timer_2 = QtCore.QTimer()
                self.timer_2.timeout.connect(lambda: self.volume_released())
                self.timer_2.setSingleShot(True)
                self.timer_2.start(500)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def volume_resetted(self):
        try:
            self.volume_slider.setValue(100)
            self.volume_label_2.setText("100/200")
            self.queue.put({"type": "volume", "value_base_100": 100})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def create_menu_for_pan(self):
        try:
            self.menu_for_pan = QtWidgets.QMenu(self.main_self.ui.general_deck_pan)
            self.main_self.ui.general_deck_pan.setMenu(self.menu_for_pan)

            self.pan_frame = Custom_QFrame(self.menu_for_pan)
            self.pan_frame.installEventFilter(self.pan_frame)
            self.pan_frame.setFixedWidth(600)
            self.pan_frame.setStyleSheet("QFrame{background-color:rgb(253,253,253);border:1px solid #ABABAB;}")
            self.pan_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.pan_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.pan_frame.setObjectName("pan_frame")

            self.pan_horizontalLayout = QtWidgets.QHBoxLayout(self.pan_frame)
            self.pan_horizontalLayout.setObjectName("pan_horizontalLayout")
            self.pan_label = QtWidgets.QLabel(self.pan_frame)
            self.pan_label.setObjectName("pan_label")
            self.pan_label.setStyleSheet("QLabel{border:none;}")
            self.pan_horizontalLayout.addWidget(self.pan_label)

            self.pan_slider = QtWidgets.QSlider(self.pan_frame)
            self.pan_slider.setMinimum(-100)
            self.pan_slider.setMaximum(100)
            self.pan_slider.setProperty("value", self.settings["pan"])
            self.pan_slider.setOrientation(QtCore.Qt.Horizontal)
            self.pan_slider.setObjectName("pan_slider")
            self.pan_horizontalLayout.addWidget(self.pan_slider)

            self.pan_label_2 = QtWidgets.QLabel(self.pan_frame)
            self.pan_label_2.setObjectName("pan_label_2")
            self.pan_label_2.setStyleSheet("QLabel{border:none;}")
            self.pan_horizontalLayout.addWidget(self.pan_label_2)
            self.pan_reset = QtWidgets.QPushButton(self.pan_frame)
            self.pan_reset.setObjectName("pan_reset")
            self.pan_horizontalLayout.addWidget(self.pan_reset)

            self.pan_label.setText("Ρύθμιση στερεοφωνικής ισοστάθμισης:")
            self.pan_label_2.setText(str(self.settings["pan"]))
            self.pan_reset.setText("Επαναφορά 0")

            # on sound pan changed
            self.pan_slider.valueChanged.connect(lambda slider_value: self.pan_changed(slider_value))

            # on sound pan apply new value
            self.pan_slider.sliderReleased.connect(lambda: self.pan_released())

            # on sound pan pressed
            self.pan_slider.actionTriggered.connect(lambda action: self.pan_action_triggered(action))

            # on sound volume reset
            self.pan_reset.clicked.connect(lambda state: self.pan_resetted())

            pan_widget = QtWidgets.QWidgetAction(self.menu_for_pan)
            pan_widget.setDefaultWidget(self.pan_frame)
            self.menu_for_pan.addAction(pan_widget)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def pan_changed(self, slider_value):
        try:
            self.pan_label_2.setText(str(slider_value))
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def pan_released(self):
        try:
            slider_value = self.pan_slider.value()
            self.queue.put({"type": "pan", "pan_value": slider_value})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def pan_action_triggered(self, action):
        try:
            if action == QtWidgets.QAbstractSlider.SliderSingleStepAdd or action == QtWidgets.QAbstractSlider.SliderSingleStepSub or action == QtWidgets.QAbstractSlider.SliderPageStepAdd or action == QtWidgets.QAbstractSlider.SliderPageStepSub:
                self.timer_2 = QtCore.QTimer()
                self.timer_2.timeout.connect(lambda: self.pan_released())
                self.timer_2.setSingleShot(True)
                self.timer_2.start(500)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def pan_resetted(self):
        try:
            self.pan_slider.setValue(0)
            self.pan_label_2.setText("0")
            self.queue.put({"type": "pan", "pan_value": 0})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def create_menu_for_normalize(self):
        try:
            self.menu_for_normalize = QtWidgets.QMenu(self.main_self.ui.general_deck_normalize)
            self.main_self.ui.general_deck_normalize.setMenu(self.menu_for_normalize)

            self.normalize_frame = Custom_QFrame(self.menu_for_normalize)
            self.normalize_frame.installEventFilter(self.normalize_frame)
            self.normalize_frame.setFixedWidth(300)
            self.normalize_frame.setStyleSheet("QFrame{background-color:rgb(253,253,253);border:1px solid #ABABAB;}")
            self.normalize_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.normalize_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.normalize_frame.setObjectName("normalize_frame")

            self.horizontalLayout_normalize = QtWidgets.QHBoxLayout(self.normalize_frame)
            self.normalize_checkBox = QtWidgets.QCheckBox(self.normalize_frame)
            self.normalize_checkBox.setObjectName("normalize_checkBox")
            self.normalize_checkBox.setStyleSheet("border:none;")
            if self.settings["is_normalized"]:
                self.normalize_checkBox.setCheckState(QtCore.Qt.Checked)
            else:
                self.normalize_checkBox.setCheckState(QtCore.Qt.Unchecked)
            self.horizontalLayout_normalize.addWidget(self.normalize_checkBox)

            self.normalize_checkBox.setText("Κανονικοποίηση")

            # on normalize changed
            self.normalize_checkBox.stateChanged.connect(lambda new_state: self.normalize_changed(new_state))

            normalize_widget = QtWidgets.QWidgetAction(self.menu_for_normalize)
            normalize_widget.setDefaultWidget(self.normalize_frame)
            self.menu_for_normalize.addAction(normalize_widget)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def normalize_changed(self, new_state):
        try:
            if new_state == QtCore.Qt.Unchecked:
                self.queue.put({"type": "is_normalized", "boolean_value": 0})
            else:
                self.queue.put({"type": "is_normalized", "boolean_value": 1})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def create_menu_for_filter(self):
        try:
            self.menu_for_filter = QtWidgets.QMenu(self.main_self.ui.general_deck_filter)
            self.main_self.ui.general_deck_filter.setMenu(self.menu_for_filter)

            self.filter_frame = Custom_QFrame(self.menu_for_filter)
            self.filter_frame.installEventFilter(self.filter_frame)
            self.filter_frame.setStyleSheet("QFrame{border:1px solid #ABABAB;background-color:rgb(253,253,253);}")
            self.filter_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.filter_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.filter_frame.setObjectName("filter_frame")

            self.filter_horizontalLayout = QtWidgets.QHBoxLayout(self.filter_frame)
            self.filter_horizontalLayout.setObjectName("filter_horizontalLayout")

            self.filter_label_7 = QtWidgets.QLabel(self.filter_frame)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.filter_label_7.sizePolicy().hasHeightForWidth())
            self.filter_label_7.setSizePolicy(sizePolicy)
            self.filter_label_7.setMinimumSize(QtCore.QSize(0, 0))
            self.filter_label_7.setMaximumSize(QtCore.QSize(16777215, 16777215))
            self.filter_label_7.setStyleSheet("QLabel{border:none;}")
            self.filter_label_7.setWordWrap(True)
            self.filter_label_7.setObjectName("filter_label_7")
            self.filter_horizontalLayout.addWidget(self.filter_label_7)

            self.filter_frame_13 = QtWidgets.QFrame(self.filter_frame)
            self.filter_frame_13.setStyleSheet("QFrame{border:none;}")
            self.filter_frame_13.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.filter_frame_13.setFrameShadow(QtWidgets.QFrame.Raised)
            self.filter_frame_13.setObjectName("filter_frame_13")

            self.filter_gridLayout_4 = QtWidgets.QGridLayout(self.filter_frame_13)
            self.filter_gridLayout_4.setContentsMargins(0, 0, 0, 0)
            self.filter_gridLayout_4.setObjectName("filter_gridLayout_4")

            self.filter_high_frequency = QtWidgets.QSpinBox(self.filter_frame_13)
            self.filter_high_frequency.setMinimumSize(QtCore.QSize(0, 29))
            self.filter_high_frequency.setMinimum(20)
            self.filter_high_frequency.setMaximum(20000)
            self.filter_high_frequency.setSingleStep(100)
            self.filter_high_frequency.setValue(20000)
            self.filter_high_frequency.setObjectName("filter_high_frequency")
            self.filter_gridLayout_4.addWidget(self.filter_high_frequency, 1, 1, 1, 1)

            self.filter_label_11 = QtWidgets.QLabel(self.filter_frame_13)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.filter_label_11.sizePolicy().hasHeightForWidth())
            self.filter_label_11.setSizePolicy(sizePolicy)
            self.filter_label_11.setObjectName("filter_label_11")
            self.filter_gridLayout_4.addWidget(self.filter_label_11, 1, 0, 1, 1)

            self.filter_label_13 = QtWidgets.QLabel(self.filter_frame_13)
            self.filter_label_13.setMinimumSize(QtCore.QSize(60, 0))
            self.filter_label_13.setMaximumSize(QtCore.QSize(50, 16777215))
            self.filter_label_13.setAlignment(QtCore.Qt.AlignCenter)
            self.filter_label_13.setObjectName("filter_label_13")
            self.filter_gridLayout_4.addWidget(self.filter_label_13, 1, 2, 1, 1)

            self.filter_reset_filter = QtWidgets.QPushButton(self.filter_frame_13)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.filter_reset_filter.sizePolicy().hasHeightForWidth())
            self.filter_reset_filter.setSizePolicy(sizePolicy)
            self.filter_reset_filter.setMinimumSize(QtCore.QSize(260, 29))
            self.filter_reset_filter.setMaximumSize(QtCore.QSize(205, 16777215))
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/select-default.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.filter_reset_filter.setIcon(icon)
            self.filter_reset_filter.setObjectName("filter_reset_filter")
            self.filter_gridLayout_4.addWidget(self.filter_reset_filter, 1, 3, 1, 1)

            self.filter_label_12 = QtWidgets.QLabel(self.filter_frame_13)
            self.filter_label_12.setMinimumSize(QtCore.QSize(60, 0))
            self.filter_label_12.setMaximumSize(QtCore.QSize(50, 16777215))
            self.filter_label_12.setAlignment(QtCore.Qt.AlignCenter)
            self.filter_label_12.setObjectName("filter_label_12")
            self.filter_gridLayout_4.addWidget(self.filter_label_12, 0, 2, 1, 1)

            self.filter_apply_filter = QtWidgets.QPushButton(self.filter_frame_13)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.filter_apply_filter.sizePolicy().hasHeightForWidth())
            self.filter_apply_filter.setSizePolicy(sizePolicy)
            self.filter_apply_filter.setMinimumSize(QtCore.QSize(260, 29))
            self.filter_apply_filter.setMaximumSize(QtCore.QSize(205, 16777215))
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/apply-filter.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.filter_apply_filter.setIcon(icon1)
            self.filter_apply_filter.setObjectName("filter_apply_filter")
            self.filter_gridLayout_4.addWidget(self.filter_apply_filter, 0, 3, 1, 1)

            self.filter_label_10 = QtWidgets.QLabel(self.filter_frame_13)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.filter_label_10.sizePolicy().hasHeightForWidth())
            self.filter_label_10.setSizePolicy(sizePolicy)
            self.filter_label_10.setObjectName("filter_label_10")
            self.filter_gridLayout_4.addWidget(self.filter_label_10, 0, 0, 1, 1)

            self.filter_low_frequency = QtWidgets.QSpinBox(self.filter_frame_13)
            self.filter_low_frequency.setMinimumSize(QtCore.QSize(0, 29))
            self.filter_low_frequency.setMinimum(20)
            self.filter_low_frequency.setMaximum(20000)
            self.filter_low_frequency.setSingleStep(100)
            self.filter_low_frequency.setValue(20)
            self.filter_low_frequency.setObjectName("filter_low_frequency")
            self.filter_gridLayout_4.addWidget(self.filter_low_frequency, 0, 1, 1, 1)

            self.filter_horizontalLayout.addWidget(self.filter_frame_13)

            self.filter_label_7.setText("Ζωνοπερατό φίλτρο:\n 20Hz-20000Hz")
            self.filter_label_11.setText("Υψηλή συχνότητα αποκοπής:")
            self.filter_label_13.setText("Hz")
            self.filter_reset_filter.setText("Επαναφορά (20Hz - 20000Hz)")
            self.filter_label_12.setText("Hz")
            self.filter_apply_filter.setText("Εφαρμογή φίλτρου")
            self.filter_label_10.setText("Χαμηλή συχνότητα αποκοπής:")


            self.filter_high_frequency.setValue(self.settings["high_frequency"])
            self.filter_high_frequency.setMinimum(self.settings["low_frequency"])
            self.filter_low_frequency.setValue(self.settings["low_frequency"])
            self.filter_low_frequency.setMaximum(self.settings["high_frequency"])


            # on low_frequency change
            self.filter_low_frequency.valueChanged.connect(lambda low_frequency: self.low_frequency_changed(low_frequency))

            # on high_frequency change
            self.filter_high_frequency.valueChanged.connect(lambda high_frequency: self.high_frequency_changed(high_frequency))

            # on apply filter
            self.filter_apply_filter.clicked.connect(lambda state: self.apply_filter_method(state))

            # on reset filter
            self.filter_reset_filter.clicked.connect(lambda state: self.reset_filter_method(state))

            filter_widget = QtWidgets.QWidgetAction(self.menu_for_filter)
            filter_widget.setDefaultWidget(self.filter_frame)
            self.menu_for_filter.addAction(filter_widget)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def low_frequency_changed(self, low_frequency):
        try:
            self.filter_high_frequency.setMinimum(low_frequency)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def high_frequency_changed(self, high_frequency):
        try:
            self.filter_low_frequency.setMaximum(high_frequency)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def apply_filter_method(self, state):
        try:
            low_frequency = self.filter_low_frequency.value()
            high_frequency = self.filter_high_frequency.value()
            self.queue.put({"type": "low_frequency", "low_frequency_value": low_frequency})
            self.queue.put({"type": "high_frequency", "high_frequency_value": high_frequency})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def reset_filter_method(self, state):
        try:
            self.filter_low_frequency.setValue(20)
            self.filter_low_frequency.setMaximum(20000)
            self.filter_high_frequency.setValue(20000)
            self.filter_high_frequency.setMinimum(20)
            self.queue.put({"type": "low_frequency", "low_frequency_value": 20})
            self.queue.put({"type": "high_frequency", "high_frequency_value": 20000})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def create_menu_for_windows_volume(self):
        try:
            self.menu_for_windows_volume = QtWidgets.QMenu(self.main_self.ui.general_deck_windows_volume)
            self.main_self.ui.general_deck_windows_volume.setMenu(self.menu_for_windows_volume)

            self.windows_volume_frame = Custom_QFrame(self.menu_for_windows_volume)
            self.windows_volume_frame.installEventFilter(self.windows_volume_frame)
            self.windows_volume_frame.setFixedWidth(600)
            self.windows_volume_frame.setStyleSheet("QFrame{border:1px solid #ABABAB;background-color:rgb(253,253,253);}")
            self.windows_volume_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.windows_volume_frame.setFrameShadow(QtWidgets.QFrame.Raised)

            self.windows_horizontalLayout = QtWidgets.QHBoxLayout(self.windows_volume_frame)
            self.windows_label = QtWidgets.QLabel(self.windows_volume_frame)
            self.windows_label.setStyleSheet("QLabel{border:none;}")
            self.windows_horizontalLayout.addWidget(self.windows_label)

            self.windows_volume_slider = QtWidgets.QSlider(self.windows_volume_frame)
            self.windows_volume_slider.setMaximum(100)
            '''
            ### CHANGE THIS LINE ###
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume_percentage = int(round(volume.GetMasterVolumeLevelScalar() * 100))
            self.windows_volume_slider.setProperty("value", volume_percentage)
            '''
            self.windows_volume_slider.setOrientation(QtCore.Qt.Horizontal)
            self.windows_horizontalLayout.addWidget(self.windows_volume_slider)

            self.windows_volume_label = QtWidgets.QLabel(self.windows_volume_frame)
            self.windows_volume_label.setStyleSheet("QLabel{border:none;}")
            self.windows_horizontalLayout.addWidget(self.windows_volume_label)

            self.windows_volume_reset = QtWidgets.QPushButton(self.windows_volume_frame)
            self.windows_volume_reset.setMinimumSize(QtCore.QSize(0, 29))
            self.windows_horizontalLayout.addWidget(self.windows_volume_reset)

            self.windows_label.setText("Ρύθμιση έντασης ήχου (windows):")
            ### CHANGE THIS LINE
            #self.windows_volume_label.setText(str(volume_percentage)+"/100")
            self.windows_volume_reset.setText("Επαναφορά (100/100)")

            # on sound volume changed
            self.windows_volume_slider.valueChanged.connect(lambda slider_value: self.windows_volume_changed(slider_value))

            # on sound volume apply new value
            self.windows_volume_slider.sliderReleased.connect(lambda: self.windows_volume_released())

            # on sound volume pressed
            self.windows_volume_slider.actionTriggered.connect(lambda action: self.windows_volume_action_triggered(action))

            # on sound volume reset
            self.windows_volume_reset.clicked.connect(lambda state: self.windows_volume_resetted())

            windows_volume_widget = QtWidgets.QWidgetAction(self.menu_for_windows_volume)
            windows_volume_widget.setDefaultWidget(self.windows_volume_frame)
            self.menu_for_windows_volume.addAction(windows_volume_widget)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def windows_volume_changed(self, slider_value):
        try:
            CoInitialize()
            self.windows_volume_label.setText(str(slider_value) + "/100")
            ### PUT CODE HERE ###
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            scalarVolume = int(slider_value) / 100
            volume.SetMasterVolumeLevelScalar(scalarVolume, None)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)
        finally:
            # Safe release of COM object in the finally block
            self.safe_release(volume)

            # Cleanly uninitialize COM
            CoUninitialize()

    def safe_release(self,com_object):
        try:
            # Check if the COM object exists and is valid before attempting to release
            if com_object:
                com_object.Release()  # Safely attempt to release
                com_object = None  # Clear reference after release
        except (ValueError, OSError) as e:
            # Log or handle the exception gracefully
            print(f"Error during release: {e}")


    def windows_volume_released(self):
        try:
            CoInitialize()
            slider_value = self.windows_volume_slider.value()
            ### PUT CODE HERE ###
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            scalarVolume = int(slider_value) / 100
            volume.SetMasterVolumeLevelScalar(scalarVolume, None)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)
        finally:
            # Safe release of COM object in the finally block
            self.safe_release(volume)

            # Cleanly uninitialize COM
            CoUninitialize()

    def windows_volume_action_triggered(self, action):
        try:
            if action == QtWidgets.QAbstractSlider.SliderSingleStepAdd or action == QtWidgets.QAbstractSlider.SliderSingleStepSub or action == QtWidgets.QAbstractSlider.SliderPageStepAdd or action == QtWidgets.QAbstractSlider.SliderPageStepSub:
                self.timer_2 = QtCore.QTimer()
                self.timer_2.timeout.connect(lambda: self.windows_volume_released())
                self.timer_2.setSingleShot(True)
                self.timer_2.start(500)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def windows_volume_resetted(self):
        try:
            CoInitialize()
            self.windows_volume_slider.setProperty("value", 100)
            self.windows_volume_label.setText(str(100) + "/100")

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            scalarVolume = int(100) / 100
            volume.SetMasterVolumeLevelScalar(scalarVolume, None)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)
        finally:
            # Safe release of COM object in the finally block
            self.safe_release(volume)

            # Cleanly uninitialize COM
            CoUninitialize()

    def final_slice_ready(self,slice):
        try:
            try:
                #if "put_to_ip_record" in dir(self):
                #    if self.put_to_ip_record:
                #        self.main_self.ip_calls_record_deck_instance.queue.put({"type":"slice","slice":slice})
                if self.put_to_plot:
                    self.main_self.final_slice_plot_instance.queue.put({"type":"slice","slice":slice})
                if self.put_to_pyaudio:
                    self.main_self.final_slice_pyaudio_instance.queue.put(
                        {"type": "slice", "slice": slice})
                if self.put_to_record:
                    self.main_self.record_deck_instance.queue.put({"type":"slice","slice":slice})
            except RuntimeError as e:
                print(e)
            except:
                print(traceback.format_exc())
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def windows_volume_changed_set_value(self,volume):
        try:
            self.windows_volume_slider.setProperty("value",int(volume))
            self.windows_volume_label.setText(str(volume)+"/100")
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def play_previous_result(self,result):
        try:
            if result == {}:
                return None
            else:
                relative_type = result["relative_type"]
                item = result["item"]
                if relative_type == "retransmitions":
                    t1 = datetime.strptime(result["datetime_started_played"], "%d-%m-%Y, %H:%M:%S")
                    t2 = datetime.strptime(result["datetime_stoped_played"], "%d-%m-%Y, %H:%M:%S")
                    dt = t2 - t1
                    duration_milliseconds = dt.total_seconds()*1000
                    item["duration_milliseconds"] = duration_milliseconds
                    item["duration_human"] = convert_time_function.convert_duration_from_milliseconds_to_human(duration_milliseconds)
                if relative_type == "sound_clips":
                    self.main_self.music_clip_deck_instance.load_clip(item)
                    self.main_self.ui.music_clip_deck_play_or_pause.click()
                else:
                    self.main_self.deck_1_instance.load_item(item)
                    self.main_self.ui.deck_1_play_or_pause.click()
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

    def close(self):
        try:
            self.queue.put({"type":"close"})
            while(self.queue.qsize()>0):
                time.sleep(self.main_self.configuration["packet_time_ms"]/1000)
            time.sleep(10*self.main_self.configuration["packet_time_ms"]/1000)

            self.child_process.terminate()
            self.emitter.quit()

            queues = [self.queue,self.deck_1_queue,self.deck_2_queue,self.music_clip_deck_queue,self.speackers_deck_queue,self.queue,self.ip_call_2_queue,self.ip_call_3_queue]
            for queue in queues:
                while(queue.qsize()!=0):
                    _ = queue.get()

            manage_processes_class.deinit_process(self)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_final_slice_error_window(error_message)

class Emitter(QThread):
    try:
        error_signal = pyqtSignal(str)
        general_deck_settings = pyqtSignal(dict)
        final_slice_ready = pyqtSignal(AudioSegment)
        windows_volume = pyqtSignal(int)
        play_previous_result = pyqtSignal(dict)
    except:
        pass

    def __init__(self, from_process: Pipe):
        try:
            super().__init__()
            self.data_from_process = from_process
        except:
            error_message = traceback.format_exc()
            self.error_signal.emit(error_message)

    def run(self):
        try:
            while True:
                data = self.data_from_process.recv()
                if data["type"] == "error":
                    self.error_signal.emit(data["error_message"])
                elif data["type"] == "general_deck_settings":
                    self.general_deck_settings.emit(data["settings"])
                elif data["type"] == "final_slice":
                    self.final_slice_ready.emit(data["slice"])
                elif data["type"] == "windows_volume":
                    self.windows_volume.emit(data["volume"])
                elif data["type"] == "play-previous-result":
                    self.play_previous_result.emit(data["result"])
        except:
            error_message = traceback.format_exc()
            self.error_signal.emit(error_message)

class Child_Proc(Process):

    def __init__(self, to_emitter, from_mother,deck_1_queue,deck_2_queue,music_clip_deck_queue,speackers_deck_queue,ip_call_1_queue,ip_call_2_queue,ip_call_3_queue,condition, frame_number, quit_event,configuration):
        try:
            super().__init__()
            self.daemon = False
            self.to_emitter = to_emitter
            self.data_from_mother = from_mother
            self.condition = condition
            self.frame_number = frame_number
            self.quit_event = quit_event
            self.configuration = configuration
            self.deck_1_queue = deck_1_queue
            self.deck_2_queue = deck_2_queue
            self.music_clip_deck_queue = music_clip_deck_queue
            self.speackers_deck_queue = speackers_deck_queue
            self.ip_call_1_queue = ip_call_1_queue
            self.ip_call_2_queue = ip_call_2_queue
            self.ip_call_3_queue = ip_call_3_queue

            #sine_segment = generators.Sine(1000).to_audio_segment()
            #sine_segment = sine_segment.set_frame_rate(self.configuration["final_slice_sample_rate"])
            #sine_segment = sine_segment[(1000 - int(self.configuration["packet_time_ms"])) / 2:self.configuration["packet_time_ms"] + (1000 - int(self.configuration["packet_time_ms"])) / 2]
            #self.silent_segment = sine_segment - 200
            self.silent_segment = AudioSegment.silent(self.configuration["packet_time_ms"],self.configuration["final_slice_sample_rate"])

            self.packet_time = self.configuration["packet_time_ms"]

            self.time_inactivity = 0
        except:
            try:
                error_message = str(traceback.format_exc())
                to_emitter.send({"type": "error", "error_message": error_message})
            except:
                pass

    def safe_release(self,com_object):
        try:
            # Check if the COM object exists and is valid before attempting to release
            if com_object:
                com_object.Release()  # Safely attempt to release
                com_object = None  # Clear reference after release
        except (ValueError, OSError) as e:
            # Log or handle the exception gracefully
            print(f"Error during release: {e}")

    def __del__(self):
        try:
            # Ensure safe release of the COM object if it's still valid
            if hasattr(self, 'windows_volume') and self.windows_volume:
                self.safe_release(self.windows_volume)
        except Exception as e:
            # Catch any errors in destructor to avoid unhandled exceptions
            print(f"Destructor error: {e}")

    def run(self):
        try:
            CoInitialize()

            # Initialize your other necessary components
            self.database_functions = database_functions
            self.fetch_general_deck_settings()

            # Initialize Audio Endpoint Volume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.windows_volume = cast(interface, POINTER(IAudioEndpointVolume))

            # Fetch initial volume state and emit
            self.volume_percentage = int(round(self.windows_volume.GetMasterVolumeLevelScalar() * 100))
            self.to_emitter.send({"type": "windows_volume", "volume": self.volume_percentage})

            current_frame = 0
            while True:
                with self.condition:
                    self.condition.wait_for(lambda: current_frame <= self.frame_number.value)
                    if self.quit_event.is_set():
                        break  # Clean exit from loop

                # Process a chunk of data (e.g., audio/video)
                r = self.one_chunk()
                if r == "close":
                    # Safe release of COM object in the finally block
                    if hasattr(self, 'windows_volume') and self.windows_volume:
                        self.safe_release(self.windows_volume)

                    # Cleanly uninitialize COM
                    CoUninitialize()
                    return None
                current_frame += 1

        except Exception as e:
            # Send error details if something goes wrong
            error_message = str(traceback.format_exc())
            print(error_message)
            self.to_emitter.send({"type": "error", "error_message": error_message})

        finally:
            # Safe release of COM object in the finally block
            if hasattr(self, 'windows_volume') and self.windows_volume:
                self.safe_release(self.windows_volume)

            # Cleanly uninitialize COM
            CoUninitialize()

    def fetch_general_deck_settings(self):
        try:
            self.volume = int(self.database_functions.read_setting("general_deck_sound_volume")["value"])
            self.is_normalized = int(self.database_functions.read_setting("general_deck_normalize")["value"])
            self.pan = float(self.database_functions.read_setting("general_deck_pan")["value"])
            self.low_frequency = int(self.database_functions.read_setting("general_deck_low_frequency")["value"])
            self.high_frequency = int(self.database_functions.read_setting("general_deck_high_frequency")["value"])

            self.general_deck_settings = {
                "volume":self.volume,
                "is_normalized":self.is_normalized,
                "pan":self.pan,
                "low_frequency":self.low_frequency,
                "high_frequency":self.high_frequency
            }

            self.to_emitter.send({"type": "general_deck_settings", "settings": self.general_deck_settings})
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def one_chunk(self):
        try:
            self.update_windows_volume()
            # Handle data from mother queue (general settings)
            data = None
            if self.data_from_mother.qsize() > 0:
                data = self.data_from_mother.get()

            if data:
                data_type = data.get("type")
                if data_type == "close":
                    return "close"
                if data_type == "volume":
                    self.general_deck_settings["volume"] = data["value_base_100"]
                elif data_type == "pan":
                    self.general_deck_settings["pan"] = data["pan_value"]
                elif data_type == "is_normalized":
                    self.general_deck_settings["is_normalized"] = data["boolean_value"]
                elif data_type == "low_frequency":
                    self.general_deck_settings["low_frequency"] = data["low_frequency_value"]
                elif data_type == "high_frequency":
                    self.general_deck_settings["high_frequency"] = data["high_frequency_value"]
                elif data_type == "play-previous":
                    self.search_for_previous(data["now"])

                # Save updated settings if applicable
                if data_type in ["volume", "pan", "is_normalized", "low_frequency", "high_frequency"]:
                    self.save_general_deck_settings()

            # Retrieve slices from various queues
            slices = {
                "deck_1": AudioSegment.empty(),
                "deck_2": AudioSegment.empty(),
                "music_clip_deck": AudioSegment.empty(),
                "speackers_deck": AudioSegment.empty(),
                "ip_call_1": AudioSegment.empty(),
                "ip_call_2": AudioSegment.empty(),
                "ip_call_3": AudioSegment.empty()
            }

            queues = {
                "deck_1": self.deck_1_queue,
                "deck_2": self.deck_2_queue,
                "music_clip_deck": self.music_clip_deck_queue,
                "speackers_deck": self.speackers_deck_queue,
                "ip_call_1": self.ip_call_1_queue,
                "ip_call_2": self.ip_call_2_queue,
                "ip_call_3": self.ip_call_3_queue
            }

            # Check each queue for available slices
            for key, queue in queues.items():
                if queue.qsize() > 0:
                    data = queue.get()
                    slices[key] = data["slice"]

            # Overlay slices in the specified order
            # Iterate over all audio slices
            slice = AudioSegment.empty()
            for audio_slice in list(slices.values()):
                # Check if the current slice is non-empty
                if len(audio_slice) > 0:
                    # If the base slice is still empty, assign the first non-empty slice
                    if len(slice) == 0:
                        slice = audio_slice
                    else:
                        # Overlay the current slice onto the base slice
                        slice = slice.overlay(audio_slice)

            # Handle inactivity
            if slice == AudioSegment.empty():
                self.time_inactivity += 125
                if self.time_inactivity >= 5 * 60 * 1000:
                    print("5 minutes of inactivity")
                    self.time_inactivity = 0
                slice = self.silent_segment
            else:
                self.time_inactivity = 0

            # Apply pan, frequency filters, and volume adjustments
            if self.general_deck_settings["pan"] != 0:
                slice = slice.pan(self.general_deck_settings["pan"] / 100)

            try:
                if self.general_deck_settings["low_frequency"] > 20:
                    slice = effects.high_pass_filter(slice, self.general_deck_settings["low_frequency"])
                if self.general_deck_settings["high_frequency"] > 20000:
                    slice = effects.low_pass_filter(slice, self.general_deck_settings["high_frequency"])
            except:
                pass

            # Volume adjustment
            db_volume = -200 if self.general_deck_settings["volume"] == 0 else 20 * math.log10(
                self.general_deck_settings["volume"] / 100)
            slice = slice + db_volume

            # Normalization if enabled
            if self.general_deck_settings["is_normalized"]:
                slice = self.normalize_method(slice, 0.1)

            # Send the final slice
            self.to_emitter.send({"type": "final_slice", "slice": slice})

        except Exception as e:
            error_message = str(e)
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def update_windows_volume(self):
        windows_volume = None  # Explicitly initialize
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            windows_volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume_percentage = int(round(windows_volume.GetMasterVolumeLevelScalar() * 100))
            if volume_percentage != self.volume_percentage:
                self.volume_percentage = volume_percentage
                self.to_emitter.send({"type": "windows_volume", "volume": self.volume_percentage})
        except:
            error_message = str(traceback.format_exc())
            self.to_emitter.send({"type": "error", "error_message": error_message})
        finally:
            if windows_volume:
                try:
                    windows_volume.Release()  # Explicit release
                except ValueError as e:
                    self.to_emitter.send({"type": "error", "error_message": f"Release error: {e}"})
                windows_volume = None  # Clear reference

    def search_for_previous(self,now):
        try:
            now_str = now.strftime("%d-%m-%Y, %H:%M:%S")
            previous_item = database_functions.search_for_previous(now_str)
            if previous_item != {}:
                self.to_emitter.send({"type":"play-previous-result","result":previous_item})
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def save_general_deck_settings(self):
        try:
            database_functions.update_setting({"value":self.general_deck_settings["volume"],"setting":"general_deck_sound_volume"})
            database_functions.update_setting({"value":self.general_deck_settings["is_normalized"],"setting":"general_deck_normalize"})
            database_functions.update_setting({"value":self.general_deck_settings["pan"],"setting":"general_deck_pan"})
            database_functions.update_setting({"value":self.general_deck_settings["low_frequency"],"setting":"general_deck_low_frequency"})
            database_functions.update_setting({"value":self.general_deck_settings["high_frequency"],"setting":"general_deck_high_frequency"})
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def normalize_method(self, seg, headroom):
        try:
            peak_sample_val = seg.max

            if peak_sample_val == 0:
                return seg

            target_peak = seg.max_possible_amplitude * utils.db_to_float(-headroom)

            needed_boost = utils.ratio_to_db(target_peak / peak_sample_val)
            return seg.apply_gain(needed_boost)
        except:
            error_message = traceback.format_exc()
            print(error_message)
            self.to_emitter.send({"type": "error", "error_message": error_message})
            return seg

class Custom_QFrame(QtWidgets.QFrame):
    def __init__(self, parent, *args, **kwargs):
        super(QtWidgets.QFrame, self).__init__(parent, *args, **kwargs)

    def eventFilter(self, obj, event):
        if event.type() in [QtCore.QEvent.MouseButtonRelease]:
            return True
        return super(QtWidgets.QFrame, self).eventFilter(obj, event)
