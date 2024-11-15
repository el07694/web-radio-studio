from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread
from multiprocessing import Process, Queue, Pipe
import sys,os

from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore import QUrl
from io import BytesIO
import base64

from pydub import AudioSegment, effects, utils
from pydub.utils import which
AudioSegment.converter = which("ffmpeg")

from datetime import datetime
import time

from subprocess import Popen, PIPE
import threading

import math
import copy
import traceback
import importlib

icons = importlib.import_module('compiled-ui.icons')
database_functions = importlib.import_module("python+.lib.sqlite3-functions")
convert_time_function = importlib.import_module("python+.lib.convert-time-function")

class Deck_1:

    def __init__(self,main_self):
        try:
            self.main_self = main_self

            self.deck_status = "stopped"
            self.item = None
            self.put_to_q = False
            self.play_retransmition = False
            self.retransmition_ready = False

            self.main_self.ui.deck_1_play_or_pause.setStatusTip("Αναπαραγωγή ή παύση αρχείου ή αναμετάδοσης στο deck 1. Πατήστε για αναπαραγωγή")
            self.main_self.ui.deck_1_label_name.setText("Deck 1:")

            # create process
            self.create_process()

            self.init_buttons_and_sub_menus()

            self.put_to_q = True
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def create_process(self):
        try:
            self.process_number = 2

            self.mother_pipe, self.child_pipe = Pipe()
            self.queue = Queue()

            self.emitter = Emitter(self.mother_pipe)
            self.emitter.error_signal.connect(lambda error_message: self.main_self.open_deck_1_error_window(error_message))
            self.emitter.deck_1_ready.connect(lambda slice: self.deck_1_slice_ready(slice))
            self.emitter.volume_amplitude.connect(lambda normalized_value: self.display_volume_amplitude(normalized_value))
            self.emitter.current_duration_milliseconds.connect(lambda duration: self.display_current_duration(duration))
            self.emitter.deck_finished.connect(lambda: self.deck_finished())
            #self.emitter.chunk_number_answer.connect(lambda chunk_number: self.main_self.player_list_instance.chunk_number_answer("deck_1",chunk_number))
            self.emitter.url_check_result.connect(lambda result, retransmition: self.url_check_result(result, retransmition))
            self.emitter.fade_out_start.connect(lambda: self.fade_out_start())
            self.emitter.start()

            self.child_process = Child_Proc(self.child_pipe, self.queue,self.main_self.sync_processes_instance.condition, self.main_self.sync_processes_instance.frame,self.main_self.sync_processes_instance.quit_event)
            self.child_process.start()

            counter = 0
            for process in self.main_self.manage_processes_instance.processes:
                if "process_number" in process:
                    if process["process_number"] == self.process_number:
                        self.main_self.manage_processes_instance.processes[counter]["pid"] = self.child_process.pid
                        self.main_self.manage_processes_instance.processes[counter]["start_datetime"] = datetime.now()
                        self.main_self.manage_processes_instance.processes[counter]["status"] = "in_progress"
                        break
                counter += 1

            if self.main_self.manage_proccesses_window_is_open:
                self.main_self.manage_proccesses_window_support_code.queue.put({"type": "table-update", "processes": self.main_self.manage_processes_instance.processes})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def deck_1_slice_ready(self,slice):
        try:
            return None
            #if self.put_to_q:
            #    self.main_self.final_slice_instance.queue.put({"type":"slice","slice":slice})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def display_volume_amplitude(self,normalized_value):
        try:
            if self.deck_status == "stopped":
                normalized_value = 0

            frame_width = self.main_self.ui.deck_1_timeline_container_frame_4.geometry().width()
            stop_red = 255
            stop_green = int(255 * (1 - normalized_value))
            if (stop_green > 255):
                stop_green = 255
            normalized_value = int(frame_width * normalized_value)
            self.main_self.ui.deck_1_timeline_pick_frame_4.setGeometry(QtCore.QRect(0, 0, normalized_value, 16))
            self.main_self.ui.deck_1_timeline_pick_frame_4.setStyleSheet("QFrame{background-color:qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgb(255, 255, 0), stop:1 rgb(" + str(stop_red) + ", " + str(stop_green) + ", 0))}")
            self.main_self.ui.deck_1_timeline_pick_frame_4.update()
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def display_current_duration(self,duration):
        try:
            if self.deck_status == "stopped":
                duration = 0
            duration_human = convert_time_function.convert_duration_from_milliseconds_to_human(duration)
            if self.item is not None:
                self.main_self.ui.deck_1_duration.setText(duration_human +"/" + str(self.item["duration_human"]))

                self.main_self.ui.deck_1_timeslider.blockSignals(True)
                self.main_self.ui.deck_1_timeslider.setValue(int(duration))
                self.main_self.ui.deck_1_timeslider.blockSignals(False)
            else:
                self.main_self.ui.deck_1_duration.setText("00:00:00/-")
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def deck_finished(self):
        try:
            self.deck_status = "stopped"
            self.display_current_duration(0)
            self.display_volume_amplitude(0)
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/play-song.png"), QtGui.QIcon.Normal,QtGui.QIcon.Off)
            self.main_self.ui.deck_1_play_or_pause.setIcon(icon1)

            # self.player_list_instance.deck_finished("deck_1")
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def url_check_result(self, result, retransmition):
        try:
            if result == False:
                self.play_retransmition = False
                self.main_self.open_deck_1_web_error_window(retransmition)
                #if auto dj on continue auto dj
                #if self.main_self.player_list_instance.player_list_settings["auto_dj"]:
                #    self.main_self.player_list_instance.dj_retransmition_error(self.tmp_item)
            else:
                self.tmp_item = retransmition
                self.tmp_item["url_ok"] = True
                self.load_item(self.tmp_item)
                self.retransmition_ready = True
                del self.tmp_item
                if self.play_retransmition:
                    self.play_or_pause_clicked()
        except Exception as e:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def fade_out_start(self):
        try:
            return None
            #if self.main_self.player_list_instance.player_list_settings["auto_dj"]:
            #    self.main_self.player_list_instance.dj_fade_out_start()
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def init_buttons_and_sub_menus(self):
        try:
            # deck stop button
            self.main_self.ui.deck_1_stop.clicked.connect(lambda state:self.stop_button_clicked())

            # deck play or pause button
            self.main_self.ui.deck_1_play_or_pause.clicked.connect(lambda state:self.play_or_pause_clicked())

            # deck timeline
            self.main_self.ui.deck_1_timeslider.sliderReleased.connect(lambda:self.deck_timeline_slider_moved())

            # deck volume menu
            self.create_menu_for_volume()

            # deck pan menu
            self.create_menu_for_pan()

            # deck normalize menu
            self.create_menu_for_normalize()

            # deck filter menu
            self.create_menu_for_filter()

            self.main_self.ui.deck_1_play_or_pause.setFixedWidth(self.main_self.ui.deck_1_volume.sizeHint().width())
            self.main_self.ui.deck_1_stop.setFixedWidth(self.main_self.ui.deck_1_volume.sizeHint().width())
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def stop_button_clicked(self,disable_extra_plays=True):
        try:
            #if disable_extra_plays:
            #    self.main_self.player_list_instance.time_collection_play_in_progress = False
            #    self.main_self.player_list_instance.playlist_play_in_progress = False
            self.deck_status = "stopped"
            self.queue.put({"type":"new-status","status":self.deck_status})
            self.display_current_duration(0)
            self.display_volume_amplitude(0)
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/play-song.png"), QtGui.QIcon.Normal,QtGui.QIcon.Off)
            self.main_self.ui.deck_1_play_or_pause.setIcon(icon1)

            self.main_self.ui.deck_1_timeslider.blockSignals(True)
            self.main_self.ui.deck_1_timeslider.setValue(0)
            self.main_self.ui.deck_1_timeslider.blockSignals(False)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def play_or_pause_clicked(self):
        try:
            if self.item == None:
                return None
            if self.deck_status == "playing":
                self.deck_status = "paused"

                self.main_self.ui.deck_1_play_or_pause.setStatusTip("Αναπαραγωγή ή παύση αρχείου ή αναμετάδοσης στο deck 1. Πατήστε για αναπαραγωγή")

                icon1 = QtGui.QIcon()
                icon1.addPixmap(QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/play-song.png"), QtGui.QIcon.Normal,QtGui.QIcon.Off)
                self.main_self.ui.deck_1_play_or_pause.setIcon(icon1)

            else:
                self.deck_status = "playing"
                self.main_self.ui.deck_1_play_or_pause.setStatusTip(
                    "Αναπαραγωγή ή παύση αρχείου ή αναμετάδοσης στο deck 1. Πατήστε για παύση")

                icon1 = QtGui.QIcon()
                icon1.addPixmap(QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/pause-song.png"), QtGui.QIcon.Normal,QtGui.QIcon.Off)
                self.main_self.ui.deck_1_play_or_pause.setIcon(icon1)
            self.queue.put({"type":"new-status","status":self.deck_status})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def deck_timeline_slider_moved(self):
        try:
            value = self.main_self.ui.deck_1_timeslider.value()
            if (self.deck_status != "stopped"):
                # calculate new chunk_number
                chunk_number = round(value / 125)
                self.queue.put({"type": "duration_changed", "chunk_number": chunk_number})
            else:
                self.main_self.ui.deck_1_timeslider.setProperty("value", 0)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def create_menu_for_volume(self):
        try:
            self.menu_for_volume = QtWidgets.QMenu(self.main_self.ui.deck_1_volume)
            self.main_self.ui.deck_1_volume.setMenu(self.menu_for_volume)

            self.volume_frame = Custom_QFrame(self.menu_for_volume)
            self.volume_frame.installEventFilter(self.volume_frame)
            self.volume_frame.setFixedWidth(600)
            self.volume_frame.setStyleSheet("QFrame{border:1px solid #ABABAB;background-color:rgb(253,253,253);}")
            self.volume_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.volume_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.volume_frame.setObjectName("volume_frame")

            self.volume_horizontalLayout = QtWidgets.QHBoxLayout(self.volume_frame)
            self.volume_horizontalLayout.setObjectName("volume_horizontalLayout")

            self.volume_label_1 = QtWidgets.QLabel(self.volume_frame)
            self.volume_label_1.setStyleSheet("QLabel{border:none;}")
            self.volume_label_1.setObjectName("volume_label_1")
            self.volume_horizontalLayout.addWidget(self.volume_label_1)

            self.volume_slider = QtWidgets.QSlider(self.volume_frame)
            self.volume_slider.setMaximum(200)
            self.volume_slider.setProperty("value", 100)
            self.volume_slider.setOrientation(QtCore.Qt.Horizontal)
            self.volume_slider.setObjectName("volume_slider")
            self.volume_horizontalLayout.addWidget(self.volume_slider)

            self.volume_label_2 = QtWidgets.QLabel(self.volume_frame)
            self.volume_label_2.setObjectName("volume_label")
            self.volume_label_2.setStyleSheet("QLabel{border:none;}")
            self.volume_horizontalLayout.addWidget(self.volume_label_2)

            self.volume_reset = QtWidgets.QPushButton(self.volume_frame)
            self.volume_reset.setMinimumSize(QtCore.QSize(0, 29))
            self.volume_reset.setObjectName("volume_reset")
            self.volume_horizontalLayout.addWidget(self.volume_reset)

            self.volume_label_1.setText("Ρύθμιση έντασης ήχου:")
            self.volume_label_2.setText(str(100)+"/200")
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
            self.main_self.open_deck_1_error_window(error_message)

    def volume_changed(self, slider_value):
        try:
            self.volume_label_2.setText(str(slider_value) + "/200")
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def volume_released(self):
        try:
            slider_value = self.volume_slider.value()
            self.queue.put({"type": "volume", "value_base_100": slider_value})

            #page 4
            #reload player list items
            #self.main_self.ui.main_player_list_treeWidget.clear()
            #self.main_self.player_list_instance.player_list_queue.put({"type": "get-player-list"})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def volume_action_triggered(self, action):
        try:
            if action == QtWidgets.QAbstractSlider.SliderSingleStepAdd or action == QtWidgets.QAbstractSlider.SliderSingleStepSub or action == QtWidgets.QAbstractSlider.SliderPageStepAdd or action == QtWidgets.QAbstractSlider.SliderPageStepSub:
                self.timer_2 = QtCore.QTimer()
                self.timer_2.timeout.connect(lambda: self.volume_released())
                self.timer_2.setSingleShot(True)
                self.timer_2.start(500)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def volume_resetted(self):
        try:
            self.volume_slider.setValue(100)
            self.volume_label_2.setText("100/200")
            self.queue.put({"type": "volume", "value_base_100": 100})

            #page 4
            #reload player list items
            #self.main_self.ui.main_player_list_treeWidget.clear()
            #self.main_self.player_list_instance.player_list_queue.put({"type": "get-player-list"})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def create_menu_for_pan(self):
        try:
            self.menu_for_pan = QtWidgets.QMenu(self.main_self.ui.deck_1_pan)
            self.main_self.ui.deck_1_pan.setMenu(self.menu_for_pan)

            self.pan_frame = Custom_QFrame(self.menu_for_pan)
            self.pan_frame.installEventFilter(self.pan_frame)
            self.pan_frame.setFixedWidth(600)
            self.pan_frame.setStyleSheet("QFrame{background-color:rgb(253,253,253);border:1px solid #ABABAB;}")
            self.pan_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.pan_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.pan_frame.setObjectName("pan_frame")

            self.pan_horizontalLayout = QtWidgets.QHBoxLayout(self.pan_frame)
            self.pan_horizontalLayout.setObjectName("pan_horizontalLayout")

            self.pan_label_1 = QtWidgets.QLabel(self.pan_frame)
            self.pan_label_1.setObjectName("pan_label_1")
            self.pan_label_1.setStyleSheet("QLabel{border:none;}")
            self.pan_horizontalLayout.addWidget(self.pan_label_1)

            self.pan_slider = QtWidgets.QSlider(self.pan_frame)
            self.pan_slider.setMinimum(-100)
            self.pan_slider.setMaximum(100)
            self.pan_slider.setProperty("value", 0)
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

            self.pan_label_1.setText("Ρύθμιση στερεοφωνικής ισοστάθμισης:")
            self.pan_label_2.setText(str(0))
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
            self.main_self.open_deck_1_error_window(error_message)

    def pan_changed(self, slider_value):
        try:
            self.pan_label_2.setText(str(slider_value))
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def pan_released(self):
        try:
            slider_value = self.pan_slider.value()
            self.queue.put({"type": "pan", "pan_value": slider_value})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def pan_action_triggered(self, action):
        try:
            if action == QtWidgets.QAbstractSlider.SliderSingleStepAdd or action == QtWidgets.QAbstractSlider.SliderSingleStepSub or action == QtWidgets.QAbstractSlider.SliderPageStepAdd or action == QtWidgets.QAbstractSlider.SliderPageStepSub:
                self.timer_2 = QtCore.QTimer()
                self.timer_2.timeout.connect(lambda: self.pan_released())
                self.timer_2.setSingleShot(True)
                self.timer_2.start(500)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def pan_resetted(self):
        try:
            self.pan_slider.setValue(0)
            self.pan_label_2.setText("0")
            self.queue.put({"type": "pan", "pan_value": 0})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def create_menu_for_normalize(self):
        try:
            self.menu_for_normalize = QtWidgets.QMenu(self.main_self.ui.deck_1_normalize)
            self.main_self.ui.deck_1_normalize.setMenu(self.menu_for_normalize)

            self.normalize_frame = Custom_QFrame(self.menu_for_normalize)
            self.normalize_frame.installEventFilter(self.normalize_frame)
            self.normalize_frame.setFixedWidth(300)
            self.normalize_frame.setStyleSheet("QFrame{background-color:rgb(253,253,253);border:1px solid #ABABAB;}")
            self.normalize_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.normalize_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.normalize_frame.setObjectName("normalize_frame")

            self.normalize_horizontalLayout = QtWidgets.QHBoxLayout(self.normalize_frame)
            self.normalize_horizontalLayout.setObjectName("normalize_horizontalLayout")

            self.normalize_checkBox = QtWidgets.QCheckBox(self.normalize_frame)
            self.normalize_checkBox.setObjectName("normalize_checkBox")
            self.normalize_checkBox.setStyleSheet("border:none;")
            self.normalize_checkBox.setCheckState(QtCore.Qt.Unchecked)
            self.normalize_horizontalLayout.addWidget(self.normalize_checkBox)

            self.normalize_checkBox.setText("Κανονικοποίηση")

            # on normalize changed
            self.normalize_checkBox.stateChanged.connect(lambda new_state: self.normalize_changed(new_state))

            normalize_widget = QtWidgets.QWidgetAction(self.menu_for_normalize)
            normalize_widget.setDefaultWidget(self.normalize_frame)
            self.menu_for_normalize.addAction(normalize_widget)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def normalize_changed(self, new_state):
        try:
            if new_state == QtCore.Qt.Unchecked:
                self.queue.put({"type": "is_normalized", "boolean_value": 0})
            else:
                self.queue.put({"type": "is_normalized", "boolean_value": 1})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def create_menu_for_filter(self):
        try:
            self.menu_for_filter = QtWidgets.QMenu(self.main_self.ui.deck_1_filter)
            self.main_self.ui.deck_1_filter.setMenu(self.menu_for_filter)

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
            self.main_self.open_deck_1_error_window(error_message)

    def low_frequency_changed(self, low_frequency):
        try:
            self.filter_high_frequency.setMinimum(low_frequency)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def high_frequency_changed(self, high_frequency):
        try:
            self.filter_low_frequency.setMaximum(high_frequency)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def apply_filter_method(self, state):
        try:
            low_frequency = self.filter_low_frequency.value()
            high_frequency = self.filter_high_frequency.value()
            self.queue.put({"type": "low_frequency", "low_frequency_value": low_frequency})
            self.queue.put({"type": "high_frequency", "high_frequency_value": high_frequency})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

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
            self.main_self.open_deck_1_error_window(error_message)

    def load_item(self,item):
        try:
            item = copy.deepcopy(item)
            if item is None:
                return None

            if item["type"] == "retransmitions":
                if "url_ok" not in item:
                    return self.check_radio_url(item)
                elif not item["url_ok"]:
                    return self.check_radio_url(item)

            # 1. stop deck 1
            self.main_self.deck_1_instance.stop_button_clicked(disable_extra_plays=False)

            # 2. change deck 1 title
            self.main_self.ui.deck_1_label_name.setText("Deck 1: "+item["title"])

            # 3. change deck 1 image
            if "image_path" in item:
                image_path = item["image_path"]
                pixmap = QtGui.QPixmap(image_path)
                self.main_self.ui.deck_1_image.setPixmap(pixmap)
                relative_type = item["type"]
            else:
                relative_type = item["type"]
                if relative_type == "station_logo" or relative_type == "station_logos":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/station-logo.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "sound_files" or relative_type == "sound_file":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/sound-file.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "church_news" or relative_type == "church_new":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/church-news.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "ip_calls" or relative_type == "ip_call":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/call.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "news" or relative_type == "new":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/newspaper.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif "record" in relative_type:
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-3/file-record.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "like_today":
                    pixmap = QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/today.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "greek_lessons" or relative_type == "greek_lesson":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/teaching.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "retransmitions" or relative_type == "retransmition":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/retransmition.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "sound_clips" or relative_type == "sound_clip":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/sound-clip.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "time_item" or relative_type == "time_items":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/clock.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "time_item" or relative_type == "time_items":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/clock.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "weather_news" or relative_type == "weather_new":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/weather-news.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "history":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/history.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "documentary":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/best-documentary.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                elif relative_type == "sport_news" or relative_type == "sport_new":
                    pixmap = QtGui.QPixmap(":/menu-icons/assets/icons/menu-icons/menu-1/football.png")
                    self.main_self.ui.deck_1_image.setPixmap(pixmap)
                else:
                    self.main_self.ui.deck_1_image.setPixmap(QtGui.QPixmap(":/rest-icons/assets/icons/rest-icons/deck-image.png"))

            if item is None:
                image_title = ""
            elif "image_title" in item:
                image_title = item["image_title"]
            else:
                image_title = item["title"]
            self.main_self.ui.deck_1_image.setStatusTip(image_title)

            # 3. set current item
            self.item = item

            # change duration_milliseconds in case of time_item with append
            if "time_item" in relative_type:
                time_collection = self.item["time_collection"]
                append = int(time_collection["append"])
                if append:
                    append_item = time_collection["append_item"]
                    append_duration_milliseconds = append_item["duration_milliseconds"]
                    new_duration_milliseconds = self.item["duration_milliseconds"] + append_duration_milliseconds
                    self.item["duration_milliseconds"] = new_duration_milliseconds
                    self.item["duration_human"] = convert_time_function.convert_duration_from_milliseconds_to_human(new_duration_milliseconds)

            # 4. change deck 1 duration
            self.display_current_duration(0)

            # 5. change deck 1 amplitude
            self.display_volume_amplitude(0)

            # 6. set slider max value
            self.main_self.ui.deck_1_timeslider.setMaximum(int(self.item["duration_milliseconds"]))
            self.main_self.ui.deck_1_timeslider.setSingleStep(500)
            self.main_self.ui.deck_1_timeslider.setPageStep(1000)
            self.main_self.ui.deck_1_timeslider.setProperty("value", 0)
            if self.item["type"] != "retransmitions":
                self.main_self.ui.deck_1_timeslider.setEnabled(True)
            else:
                self.main_self.ui.deck_1_timeslider.setEnabled(False)

            #7. set deck volume
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(self.item["volume"])
            self.volume_label_2.setText(str(self.item["volume"])+"/200")
            self.volume_slider.blockSignals(False)


            #8. set deck pan
            self.pan_slider.blockSignals(True)
            self.pan_slider.setValue(int(self.item["pan"]))
            self.pan_label_2.setText(str(self.item["pan"]))
            self.pan_slider.blockSignals(False)


            #9. set deck normalize
            self.normalize_checkBox.blockSignals(True)
            if self.item["normalize"]:
                self.normalize_checkBox.setCheckState(QtCore.Qt.Checked)

            else:
                self.normalize_checkBox.setCheckState(QtCore.Qt.Unchecked)

            self.normalize_checkBox.blockSignals(False)

            #10. set deck filter
            self.filter_low_frequency.blockSignals(True)
            self.filter_high_frequency.blockSignals(True)
            self.filter_low_frequency.setValue(self.item["low_frequency"])
            self.filter_low_frequency.setMaximum(self.item["high_frequency"])
            self.filter_high_frequency.setValue(self.item["high_frequency"])
            self.filter_high_frequency.setMinimum(self.item["low_frequency"])
            self.filter_low_frequency.blockSignals(False)
            self.filter_high_frequency.blockSignals(False)

            # 11. load clip to process
            self.queue.put({"type": "load", "item": self.item})
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def check_radio_url(self,item):
        try:
            self.tmp_item = item
            self.tmp_item["url_ok"] = False

            url_option = self.tmp_item["url_option"]

            if url_option == "dynamic" or url_option == "youtube-stream":
                try:
                    if "web" in dir(self):
                        self.web.loadFinished.disconnect()
                        del self.web
                    self.clearLayout(self.main_self.ui.horizontalLayout_9)
                except Exception as e:
                    error_message = str(traceback.format_exc())
                    print(error_message)
                self.main_self.ui.deck_1_web.show()
                self.web = QWebEngineView(self.main_self.ui.deck_1_web)
                self.web.setPage(WebEnginePage(self.web))

                self.web.load(QUrl(self.tmp_item["url"]))
                self.page_loaded = False
                self.web.show()
                self.main_self.ui.deck_1_web.hide()
                self.web.page().setAudioMuted(True)
                self.web.loadFinished.connect(lambda ok: self.main_page_loaded_finished(ok))
            else:
                self.tmp_item["stream_url"] = self.tmp_item["url"]
                self.queue.put({"type": "check-radio-url", "retransmition": self.tmp_item})
        except:
            error_message = traceback.format_exc()
            print(error_message)
            self.main_self.open_deck_1_error_window(error_message)

    def clearLayout(self, layout):
        try:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def main_page_loaded_finished(self,ok):
        try:
            if (self.page_loaded == False):
                if (ok):
                    self.page_loaded = True
                    javascript = self.tmp_item["javascript_code"]
                    if self.tmp_item["url_option"] == "youtube-stream":
                        javascript = "ytInitialPlayerResponse.streamingData.hlsManifestUrl"
                    self.web.page().runJavaScript(javascript, self.javascript_runned)
                else:
                    self.page_loaded = True
                    self.main_self.open_deck_1_web_error_window(self.tmp_item)
        except:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def javascript_runned(self, radio_url):
        try:
            if radio_url is None:
                radio_url = ""
            if "www" in radio_url or "http" in radio_url:
                pass
            else:
                try:
                    radio_url_decoded = base64.b64decode(radio_url).decode("utf-8")
                    if "www" in radio_url_decoded or "http" in radio_url_decoded:
                        radio_url = radio_url_decoded
                    else:
                        pass
                except:
                    pass

            self.tmp_item["stream_url"] = radio_url
            self.queue.put({"type": "check-radio-url", "retransmition": self.tmp_item})
            self.web.load(QUrl(""))
        except Exception as e:
            error_message = traceback.format_exc()
            self.main_self.open_deck_1_error_window(error_message)

    def close(self):
        try:
            self.stop_button_clicked(disable_extra_plays=True)
            self.child_process.terminate()
            self.emitter.quit()
            while(self.queue.qsize()!=0):
                _ = self.queue.get()

            counter = 0
            for process in self.main_self.manage_processes_instance.processes:
                if "process_number" in process:
                    if process["process_number"] == self.process_number:
                        self.main_self.manage_processes_instance.processes[counter]["pid"] = None
                        self.main_self.manage_processes_instance.processes[counter]["start_datetime"] = None
                        self.main_self.manage_processes_instance.processes[counter]["status"] = "stopped"
                        self.main_self.manage_processes_instance.processes[counter]["cpu"] = 0
                        self.main_self.manage_processes_instance.processes[counter]["ram"] = 0
                counter += 1
            if self.main_self.manage_proccesses_window_is_open:
                self.main_self.manage_proccesses_window_support_code.manage_proccesses_queue.put(
                    {"type": "table-update", "processes": self.main_self.manage_processes_instance.processes})
        except:
            error_message = traceback.format_exc()
            print(error_message)
            self.main_self.open_deck_1_error_window(error_message)

class Emitter(QThread):
    try:
        error_signal = pyqtSignal(str)
        deck_1_ready = pyqtSignal(AudioSegment)
        volume_amplitude = pyqtSignal(float)
        current_duration_milliseconds = pyqtSignal(int)
        deck_finished = pyqtSignal()
        chunk_number_answer = pyqtSignal(int)
        url_check_result = pyqtSignal(bool, dict)
        fade_out_start = pyqtSignal()
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
                elif data["type"] == "slice":
                    self.deck_1_ready.emit(data["slice"])
                elif data["type"] == "volume_amplitude":
                    self.volume_amplitude.emit(data["normalized_value"])
                elif data["type"] == "current_duration_milliseconds":
                    self.current_duration_milliseconds.emit(data["duration"])
                elif data["type"] == "deck_finished":
                    self.deck_finished.emit()
                elif data["type"] == "chunk-number-answer":
                    self.chunk_number_answer.emit(data["chunk-number"])
                elif data["type"] == "url-check-result":
                    self.url_check_result.emit(data["result"], data["retransmition"])
                elif data["type"] == "fade-out-start":
                    self.fade_out_start.emit()
        except:
            error_message = traceback.format_exc()
            self.error_signal.emit(error_message)

class Child_Proc(Process):

    def __init__(self, to_emitter, from_mother,condition, frame_number, quit_event):
        try:
            super().__init__()
            self.daemon = False
            self.to_emitter = to_emitter
            self.data_from_mother = from_mother
            self.condition = condition
            self.frame_number = frame_number
            self.quit_event = quit_event
            self.deck_status = "stopped"
            self.volume = 100
            self.pan = 0
            self.normalize = 0
            self.low_frequency = 20
            self.high_frequency = 20000
            self.item = None
            self.current_duration_milliseconds = 0
            self.chunk_number = 0
            self.packet_time = 125
            self.fade_out_emitted = False

            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # exe
                self.ffmpeg_path = os.path.abspath("extra-files/ffmpeg/ffmpeg.exe")
            else:
                self.ffmpeg_path = os.path.abspath("exe/extra-files/ffmpeg/ffmpeg.exe")
        except:
            try:
                error_message = str(traceback.format_exc())
                to_emitter.send({"type": "error", "error_message": error_message})
            except:
                pass

    def run(self):
        try:
            self.database_functions = database_functions
            self.fetch_player_list_settings()
            current_frame = 0
            while (True):
                with self.condition:
                    self.condition.wait_for(lambda: current_frame <= self.frame_number.value)
                    if self.quit_event.is_set():
                        return None
                self.one_chunk()
                current_frame += 1
        except:
            error_message = str(traceback.format_exc())
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def fetch_player_list_settings(self):
        try:
            self.database_functions = database_functions

            player_fade_out = int(database_functions.read_setting("player_fade_out")["value"])
            player_fade_in = int(database_functions.read_setting("player_fade_in")["value"])
            auto_dj = int(database_functions.read_setting("auto_dj")["value"])
            repeat_player_list = int(database_functions.read_setting("repeat_player_list")["value"])
            is_live = int(database_functions.read_setting("is_live")["value"])

            self.player_list_settings = {
                "player_fade_out":player_fade_out,
                "player_fade_in":player_fade_in,
                "auto_dj":auto_dj,
                "repeat_player_list":repeat_player_list,
                "is_live":is_live
            }
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def one_chunk(self):
        try:
            q_size = self.data_from_mother.qsize()
            if q_size > 0:
                data = self.data_from_mother.get()
            else:
                data = None
            if data is not None:
                if data["type"] == "volume":
                    self.volume = data["value_base_100"]
                    self.update_item()
                elif data["type"] == "pan":
                    self.pan = data["pan_value"]
                    self.update_item()
                elif data["type"] == "is_normalized":
                    self.normalize = data["boolean_value"]
                    self.update_item()
                elif data["type"] == "low_frequency":
                    self.low_frequency = data["low_frequency_value"]
                    self.update_item()
                elif data["type"] == "high_frequency":
                    self.high_frequency = data["high_frequency_value"]
                    self.update_item()
                elif data["type"] == "player-list-settings":
                    self.player_list_settings_previous = self.player_list_settings
                    self.player_list_settings = data["settings"]
                elif data["type"] == "check-radio-url":
                    self.check_radio_url(data["retransmition"])
                elif data["type"] == "duration_changed":
                    self.chunk_number = data["chunk_number"]
                    self.current_duration_milliseconds = self.chunk_number * self.packet_time
                elif data["type"] == "ask-for-chunk-number":
                    self.to_emitter.send({"type":"chunk-number-answer","chunk-number":self.chunk_number})
                elif data["type"] == "new-status":
                    self.deck_status = data["status"]
                    self.update_player_history(self.deck_status)
                    if self.deck_status == "playing":
                        if self.item is not None:
                            if self.item["type"] == "retransmitions":
                                self.start_retransmition()
                    elif self.deck_status == "paused":
                        if self.item is not None:
                            if self.item["type"] == "retransmitions":
                                self.stop_retransmition()
                    else:
                        self.fade_out_emitted = False
                        self.chunk_number = 0
                        self.current_duration_milliseconds = 0
                        if self.item is not None:
                            if self.item["type"] == "retransmitions":
                                self.stop_retransmition()
                elif data["type"] == "load":
                    self.fade_out_emitted = False
                    self.deck_status = "stopped"
                    self.update_player_history(self.deck_status)
                    self.item = data["item"]
                    self.volume = self.item["volume"]
                    self.pan = self.item["pan"]
                    self.normalize = self.item["normalize"]
                    self.low_frequency = self.item["low_frequency"]
                    self.high_frequency = self.item["high_frequency"]
                    self.current_duration_milliseconds = 0
                    self.chunk_number = 0
                    if self.item["type"] !="retransmitions":
                        self.audio_segment = "not-ready"
                        self.read_mp3 = threading.Thread(target=self.load_segment)
                        self.read_mp3.start()
                    else:
                        self.total_duration_milliseconds = self.item["duration_milliseconds"]
                    self.chunk_number = 0
                    self.current_duration_milliseconds = 0
                elif data["type"] == "mp3-file-segment-ready":
                    self.fade_out_emitted = False
                    self.audio_segment = data["audio_segment"]
                    self.total_duration_milliseconds = self.item["duration_milliseconds"]

                    try:
                        self.read_mp3.join()
                        del self.read_mp3
                    except:
                        pass
            if self.item is not None:
                if self.item["type"] != "retransmitions":
                    if self.audio_segment == "not-ready":
                        self.to_emitter.send({"type": "volume_amplitude", "normalized_value": 0})
                        self.to_emitter.send({"type": "current_duration_milliseconds", "duration": 0})
                        return None
                if self.current_duration_milliseconds >= self.total_duration_milliseconds:
                    self.fade_out_emitted = False
                    self.to_emitter.send({"type": "deck_finished"})
                    self.deck_status = "stopped"
                    self.update_player_history(self.deck_status)
                    self.chunk_number = 0
                    self.current_duration_milliseconds = 0
                    if self.item["type"] == "retransmitions":
                        self.stop_retransmition()
                if self.deck_status == "playing":
                    if self.item["type"] != "retransmitions":
                        if ((self.chunk_number + 1) * (self.packet_time) <= self.total_duration_milliseconds):
                            slice = self.audio_segment[self.chunk_number * (self.packet_time):(self.chunk_number + 1) * (self.packet_time)]
                        else:
                            if ((self.chunk_number) * (self.packet_time) < self.current_duration_milliseconds):
                                slice = self.audio_segment[self.chunk_number * (self.packet_time):]
                            else:
                                self.fade_out_emitted = False
                                slice = AudioSegment.empty()
                                self.deck_status = "stopped"
                                self.update_player_history(self.deck_status)
                                self.to_emitter.send({"type": "deck_finished"})
                                self.chunk_number = 0
                                self.current_duration_milliseconds = 0
                    else:
                        slice = self.read_retransmition_slice()
                        if slice == AudioSegment.empty():
                            self.to_emitter.send({"type": "volume_amplitude", "normalized_value": 0})
                            self.to_emitter.send({"type": "current_duration_milliseconds","duration": self.current_duration_milliseconds})
                            return None
                    if self.pan != 0:
                        slice = slice.pan(self.pan / 100)
                    try:
                        if self.low_frequency > 20:
                            slice = effects.high_pass_filter(slice, self.low_frequency)
                        if self.high_frequency > 20000:
                            slice = effects.low_pass_filter(slice, self.high_frequency)
                    except:
                        pass
                    volume = self.volume
                    if self.total_duration_milliseconds > 5000:
                        if self.chunk_number*self.packet_time<5000 and self.player_list_settings["player_fade_in"]:
                            volume = volume*self.fade_in(self.chunk_number*self.packet_time)
                        if self.chunk_number*self.packet_time>self.total_duration_milliseconds-5000 and self.player_list_settings["player_fade_out"]:
                            volume = volume*self.fade_out(self.chunk_number*self.packet_time,self.total_duration_milliseconds)
                    if (volume == 0):
                        db_volume = -200
                    else:
                        db_volume = 20 * math.log10(volume / 100)
                    slice = slice + db_volume
                    if self.normalize:
                        slice = self.normalize_method(slice, 0.1)

                    chunk_time = len(slice)

                    average_data_value = slice.max
                    normalized_value = abs(average_data_value) / slice.max_possible_amplitude
                    if normalized_value > 1:
                        normalized_value = 1
                    if self.deck_status == "stopped":
                        normalized_value = 0

                    self.to_emitter.send({"type": "volume_amplitude", "normalized_value": normalized_value})

                    self.now = datetime.now()

                    self.chunk_number += 1
                    if (self.chunk_number*self.packet_time>=self.total_duration_milliseconds-5000) and (self.player_list_settings["player_fade_out"] or self.player_list_settings["player_fade_in"]):
                        if self.fade_out_emitted == False:
                            self.fade_out_emitted = True
                            self.to_emitter.send({"type":"fade-out-start"})
                    else:
                        if "player_list_settings_previous" in dir(self):
                            if (self.chunk_number * self.packet_time >= self.total_duration_milliseconds - 5000) and (
                                    self.player_list_settings_previous["player_fade_out"] or self.player_list_settings_previous[
                                "player_fade_in"]):
                                if self.fade_out_emitted == False:
                                    self.fade_out_emitted = True
                                    self.to_emitter.send({"type": "fade-out-start"})
                                    del self.player_list_settings_previous

                    self.current_duration_milliseconds += chunk_time

                    self.to_emitter.send({"type": "current_duration_milliseconds", "duration": self.current_duration_milliseconds})
                    self.to_emitter.send({"type": "slice", "slice": slice})
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def update_item(self):
        try:
            if self.item == None:
                return
            else:
                self.item["volume"] = self.volume
                self.item["normalize"] = self.normalize
                self.item["pan"] = self.pan
                self.item["low_frequency"] = self.low_frequency
                self.item["high_frequency"] = self.high_frequency
                self.database_functions.update_item_by_type(self.item["type"],self.item)
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def check_radio_url(self, retransmition):
        try:
            retransmition_ok = self.check_retransmition(retransmition["stream_url"])
            self.to_emitter.send({"type": "url-check-result", "result": retransmition_ok, "retransmition": retransmition})
        except:
            error_message = str(traceback.format_exc())
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def check_retransmition(self, stream_url):
        try:
            # check if stream_url represents a valid online live web radio using ffmpeg and subprocess
            if os.path.exists("deck_1_retransmition_check.mp3"):
                os.remove("deck_1_retransmition_check.mp3")

            self.p1 = Popen([self.ffmpeg_path, '-y', '-t', '10', '-loglevel', 'quiet', '-i', stream_url,'deck_1_retransmition_check.mp3'], stdout=PIPE, stdin=PIPE,stderr=PIPE, shell=True)
            self.p1.wait()
            self.p1.communicate(b"q")
            self.p1.terminate()
            self.p1.wait()
            rc = self.p1.returncode
            if os.path.exists("deck_1_retransmition_check.mp3"):
                os.remove("deck_1_retransmition_check.mp3")
            if int(rc) == 0:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def update_player_history(self,deck_status):
        try:
            if self.item is not None:
                now = datetime.now()
                if deck_status == "playing":
                    self.player_history = {
                        "datetime_started_played":now.strftime("%d-%m-%Y, %H:%M:%S"),
                        "datetime_stoped_played":"",
                        "relative_type":self.item["type"],
                        "relative_number":self.item["id"],
                        "deck":"deck_1",
                        "updated":0
                    }
                    self.player_history = self.database_functions.import_player_history(self.player_history)
                else:
                    if "player_history" in dir(self):
                        self.player_history["updated"] = 1
                        self.player_history["datetime_stoped_played"] = now.strftime("%d-%m-%Y, %H:%M:%S")
                        self.player_history = self.database_functions.update_player_history(self.player_history)
                        if self.deck_status == "stopped":
                            del self.player_history
        except:
            error_message = str(traceback.format_exc())
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def start_retransmition(self):
        try:
            self.stop_retransmition()
            self.deck_1_ffmpeg_retransmition = Popen([self.ffmpeg_path, '-y', '-loglevel', 'quiet', '-i', self.item["stream_url"],'deck_1_retransmition.mp3'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def stop_retransmition(self):
        try:
            try:
                if "deck_1_ffmpeg_retransmition" in dir(self):
                    self.deck_1_ffmpeg_retransmition.communicate(b"q")
                    self.deck_1_ffmpeg_retransmition.terminate()
                    self.deck_1_ffmpeg_retransmition.wait()
            except:
                pass

            try:
                if "retransmition_file" in dir(self):
                    self.retransmition_file.close()
                    del self.retransmition_file
                    del self.mp3_q
            except:
                pass

            if os.path.exists("deck_1_retransmition.mp3"):
                os.remove("deck_1_retransmition.mp3")
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def load_segment(self):
        try:
            if "type" in self.item:
                relative_type = self.item["type"]
            elif "relative_type" in self.item:
                relative_type = self.item["relative_type"]

            if "time_item" not in relative_type:
                saved_path = self.item["saved_path"]
                try:
                    audio_segment = AudioSegment.from_file(saved_path, format="mp3")
                except:
                    audio_segment = AudioSegment.from_file(saved_path, format="mp4")
                self.data_from_mother.put({"type":"mp3-file-segment-ready","audio_segment":audio_segment})
            else:#in case of time_item check for append and merge the two mp3 files if neccessary
                time_collection = self.item["time_collection"]
                append = int(time_collection["append"])
                if append:
                    extra_item = time_collection["append_item"]
                    #extra item will not be playlist or time collection or retransmition, just a simple item
                    time_item_saved_path = self.item["saved_path"]
                    try:
                        time_item_segment = AudioSegment.from_file(time_item_saved_path, format="mp3")
                    except:
                        time_item_segment = AudioSegment.from_file(time_item_saved_path, format="mp4")
                    append_item_saved_path = extra_item["saved_path"]
                    try:
                        append_audio_segment = AudioSegment.from_file(append_item_saved_path, format="mp3")
                    except:
                        append_audio_segment = AudioSegment.from_file(append_item_saved_path, format="mp4")
                    audio_segment_final = time_item_segment + append_audio_segment
                    self.data_from_mother.put({"type": "mp3-file-segment-ready", "audio_segment": audio_segment_final})
                else:
                    saved_path = self.item["saved_path"]
                    try:
                        audio_segment = AudioSegment.from_file(saved_path, format="mp3")
                    except:
                        audio_segment = AudioSegment.from_file(saved_path, format="mp4")
                    self.data_from_mother.put({"type":"mp3-file-segment-ready","audio_segment":audio_segment})
            return None
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def read_retransmition_slice(self):
        try:
            if self.deck_status != "playing":
                return AudioSegment.empty()
            self.packet_size = 4096
            self.new_sample_rate = 44800

            if os.path.exists("deck_1_retransmition.mp3"):
                if "retransmition_file" not in dir(self):
                    self.retransmition_file = open("deck_1_retransmition.mp3", "rb")
                    self.mp3_q = AudioSegment.empty()
                if len(self.mp3_q) < self.packet_time:
                    chunk = False
                    while not chunk:
                        chunk = self.retransmition_file.read(32 * self.packet_size)
                        if not chunk:
                            return AudioSegment.empty()

                    chunk = BytesIO(chunk)
                    success = False
                    while (success == False):
                        try:
                            slice = AudioSegment.from_mp3(chunk)
                            success = True
                        except:
                            success = False
                    slice = slice.set_frame_rate(self.new_sample_rate)

                    self.mp3_q = self.mp3_q + slice
                    slice = self.mp3_q[0:self.packet_time]
                    self.mp3_q = self.mp3_q[self.packet_time:]
                else:
                    slice = self.mp3_q[0:self.packet_time]
                    self.mp3_q = self.mp3_q[self.packet_time:]

            else:
                return AudioSegment.empty()

            return slice
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def normalize_method(self, seg, headroom):
        try:
            peak_sample_val = seg.max

            # if the max is 0, this audio segment is silent, and can't be normalized
            if peak_sample_val == 0:
                return seg

            target_peak = seg.max_possible_amplitude * utils.db_to_float(-headroom)
            # target_peak = seg.max_possible_amplitude * (percent_headroom)

            needed_boost = utils.ratio_to_db(target_peak / peak_sample_val)
            return seg.apply_gain(needed_boost)
        except:
            error_message = traceback.format_exc()
            print(error_message)
            self.to_emitter.send({"type": "error", "error_message": error_message})
            return seg

    def fade_in(self,time_milliseconds):
        try:
            if time_milliseconds>5000:
                return 1
            elif time_milliseconds == 0:
                return 0
            else:
                fade_in = 3*time_milliseconds
                fade_in = fade_in ** (1./3)
                fade_in = fade_in / ((15000) ** (1./3))
                return fade_in
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

    def fade_out(self,time_milliseconds,total_duration_milliseconds):
        try:
            if time_milliseconds>=total_duration_milliseconds:
                return 0
            elif time_milliseconds<total_duration_milliseconds-5000:
                return 1
            else:
                fade_out = total_duration_milliseconds - time_milliseconds
                fade_out = fade_out*3
                fade_out = fade_out ** (1./3)
                fade_out = fade_out / ((15000) ** (1. / 3))
                return fade_out
        except:
            error_message = traceback.format_exc()
            self.to_emitter.send({"type": "error", "error_message": error_message})

class WebEnginePage(QWebEnginePage):
	def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
		pass

class Custom_QFrame(QtWidgets.QFrame):
    def __init__(self, parent, *args, **kwargs):
        super(QtWidgets.QFrame, self).__init__(parent, *args, **kwargs)

    def eventFilter(self, obj, event):
        if event.type() in [QtCore.QEvent.MouseButtonRelease]:
            return True
        return super(QtWidgets.QFrame, self).eventFilter(obj, event)
