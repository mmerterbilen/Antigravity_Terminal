#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Ana Kullanıcı Arayüzü (Main UI)
Çoklu İş Parçacıklı (QThread) Spektrum & Şelale Göstergesi, AM/FM/NBFM Yazılımsal Demodülasyon,
Dijital Telemetri Çözücü, Ses Çıkışı, I/Q Sinyal Kayıt/Oynatma ve RF Link Bütçesi Hesaplayıcı.
"""

import os
import sys
import time
import numpy as np
import pyqtgraph as pg
import zmq
from PyQt5.QtCore import QMutex, QRectF, Qt, QThread, QTime, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette, QPen, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from demodulator import (
    DigitalDecoder,
    TacticalAudioOutput,
    demodulate_am,
    demodulate_fm,
    demodulate_nbfm,
)
from rf_calculator import compute_link_budget
from signal_recorder import IQPlaybackThread, IQRecorder
from zmq_manager import ZMQPublisher, ZMQSubscriber, execute_ping_test


TACTICAL_STYLESHEET = """
QMainWindow {
    background-color: #0d1117;
}

QWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: "Segoe UI", "Consolas", "Roboto", sans-serif;
    font-size: 13px;
}

/* --- Sekme Çubuğu (QTabWidget) --- */
QTabWidget::pane {
    border: 1px solid #30363d;
    background-color: #0d1117;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #161b22;
    color: #8b949e;
    border: 1px solid #30363d;
    border-bottom: none;
    padding: 10px 18px;
    font-weight: bold;
    font-size: 12px;
    letter-spacing: 0.5px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #21262d;
    color: #00ff66;
    border-top: 2px solid #00ff66;
    border-bottom: 1px solid #21262d;
}

QTabBar::tab:hover:!selected {
    background-color: #1c2128;
    color: #f0f6fc;
}

/* --- Panel & GroupBox Stili --- */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    margin-top: 20px;
    padding: 12px 10px 10px 10px;
    font-weight: bold;
    color: #00ff66;
    letter-spacing: 0.8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 4px;
    color: #00ff66;
    font-size: 11px;
}

/* --- Taktik Log Konsolu & Decoder (QTextEdit) --- */
QTextEdit#console_log, QTextEdit#decoder_log {
    background-color: #080b10;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    line-height: 1.4;
    padding: 8px;
    selection-background-color: #1f3a29;
    selection-color: #00ff66;
}

/* --- Girdi Kutuları & Açılır Liste --- */
QDoubleSpinBox, QComboBox {
    background-color: #0d1117;
    color: #00ff66;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 5px 10px;
    font-family: "Consolas", monospace;
    font-size: 13px;
    font-weight: bold;
    min-height: 22px;
}

QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #00ff66;
    background-color: #111822;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    color: #f0f6fc;
    selection-background-color: #1a4d2e;
    selection-color: #00ff66;
    border: 1px solid #30363d;
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #21262d;
    border: 1px solid #30363d;
    width: 18px;
}

QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #30363d;
}

/* --- Buton Stili --- */
QPushButton {
    background-color: #21262d;
    color: #f0f6fc;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: bold;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #30363d;
    border: 1px solid #00ff66;
    color: #00ff66;
}

QPushButton:pressed {
    background-color: #1b4729;
    border: 1px solid #00ff66;
    color: #ffffff;
}

QPushButton#btn_primary {
    background-color: #1a4d2e;
    color: #00ff66;
    border: 1px solid #00ff66;
    font-size: 13px;
    padding: 8px 14px;
}

QPushButton#btn_primary:hover {
    background-color: #22683e;
    color: #ffffff;
    border: 1px solid #39ff14;
}

QPushButton#btn_audio_active {
    background-color: #1b382b;
    color: #00ff66;
    border: 1px solid #00ff66;
}

QPushButton#btn_record_start {
    background-color: #5c1d24;
    color: #ff7b72;
    border: 1px solid #ff7b72;
}

QPushButton#btn_record_start:hover {
    background-color: #7a2530;
    color: #ffffff;
}

QPushButton#btn_play_start {
    background-color: #1b382b;
    color: #38d39f;
    border: 1px solid #38d39f;
}

QPushButton#btn_play_start:hover {
    background-color: #25533f;
    color: #ffffff;
}

QPushButton#btn_ping {
    background-color: #1b2838;
    color: #58a6ff;
    border: 1px solid #58a6ff;
}

QPushButton#btn_ping:hover {
    background-color: #243b55;
    color: #ffffff;
    border: 1px solid #79c0ff;
}

QPushButton#btn_calculate {
    background-color: #0f3e27;
    color: #00ff66;
    border: 1px solid #00ff66;
    font-size: 14px;
    padding: 10px 18px;
    font-weight: bold;
}

QPushButton#btn_calculate:hover {
    background-color: #1b633f;
    color: #ffffff;
    border: 1px solid #39ff14;
}

QPushButton#btn_small {
    background-color: #161b22;
    color: #8b949e;
    border: 1px solid #30363d;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
}

QPushButton#btn_small:hover {
    color: #f0f6fc;
    border-color: #8b949e;
}

/* --- Çerçeve ve Bölücüler --- */
QFrame#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

QFrame#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 10px;
}

QSplitter::handle {
    background-color: #30363d;
    width: 2px;
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #00ff66;
}

/* --- Durum Çubuğu (Status Bar) --- */
QStatusBar {
    background-color: #161b22;
    border-top: 1px solid #30363d;
    color: #8b949e;
    font-size: 12px;
    padding: 4px;
}

QStatusBar QLabel {
    background-color: transparent;
    padding: 0 8px;
}
"""


def create_tactical_colormap():
    """Taktik Koyu Tema için yüksek kontrastlı LUT renk haritası oluşturur."""
    pos = np.array([0.0, 0.25, 0.55, 0.8, 1.0])
    colors = np.array([
        [9, 13, 19, 255],     # Zemin Koyu Gri/Siyah
        [15, 62, 39, 255],    # Koyu Taktik Zümrüt Yeşili
        [0, 230, 118, 255],   # Canlı Taktik Yeşil
        [88, 166, 255, 255],  # Elektrik Camgöbeği (Cyan)
        [255, 255, 255, 255], # Parlak Beyaz (En Yüksek Tepe)
    ], dtype=np.ubyte)
    return pg.ColorMap(pos, colors)


class DSPWorkerThread(QThread):
    """
    Arka planda ZMQ I/Q verisi alan, FFT ve yazılımsal AM/FM/NBFM demodülasyonu
    hesaplayan, canlı I/Q kaydını dosyaya yazan optimize edilmiş çoklu iş parçacığı.
    """

    # Sinyaller
    spectrum_ready = pyqtSignal(np.ndarray, np.ndarray, float, float, float, int)
    demod_audio_ready = pyqtSignal(np.ndarray, float)  # (audio_samples, power_db)
    digital_payload_ready = pyqtSignal(dict)           # (decoded_frame_dict)
    record_stats_signal = pyqtSignal(int, int, float)  # (samples, frames, size_mb)
    log_signal = pyqtSignal(str, str)

    def __init__(self, address: str = "tcp://127.0.0.1:5555", sample_rate: float = 2.048e6):
        super().__init__()
        self.address = address
        self.sample_rate = sample_rate
        self.center_freq_mhz = 433.0
        self._running = False
        self.window_cache = {}
        self.recorder = IQRecorder(output_dir="records")
        self.decoder = DigitalDecoder()

        # Demodülasyon Parametreleri
        self.demod_mode = "OFF"  # "OFF", "AM", "FM", "NBFM"
        self.squelch_db = -80.0
        self.volume = 1.0
        self.frame_index = 0

    def run(self):
        """İş parçacığı ana döngüsü."""
        self._running = True
        ctx = zmq.Context()
        sub = ZMQSubscriber(address=self.address, topics=["IQ", ""], context=ctx)

        poller = zmq.Poller()
        if sub.socket:
            poller.register(sub.socket, zmq.POLLIN)

        self.log_signal.emit("BİLGİ", "Arka plan DSP & Demodülasyon iş parçacığı (QThread) aktif edildi.")

        try:
            while self._running:
                socks = dict(poller.poll(20))
                if sub.socket and sub.socket in socks and socks[sub.socket] == zmq.POLLIN:
                    latest_iq = None
                    while True:
                        result = sub.receive_iq_data(flags=zmq.NOBLOCK)
                        if result is None:
                            break
                        _, iq_data = result
                        if len(iq_data) > 0:
                            latest_iq = iq_data
                            if self.recorder.is_recording:
                                self.recorder.write_iq_data(iq_data)

                    if latest_iq is not None and self._running:
                        N = len(latest_iq)
                        self.frame_index += 1

                        # 1. Hanning Penceresi ve FFT
                        if N not in self.window_cache:
                            self.window_cache[N] = np.hanning(N)
                        window = self.window_cache[N]

                        windowed_iq = latest_iq * window
                        fft_result = np.fft.fft(windowed_iq, n=N)
                        fft_shifted = np.fft.fftshift(fft_result)

                        magnitude_linear = np.abs(fft_shifted) / N
                        magnitude_db = 20.0 * np.log10(np.maximum(magnitude_linear, 1e-7))

                        half_bw_mhz = (self.sample_rate / 2.0) / 1e6
                        freq_axis = np.linspace(-half_bw_mhz, half_bw_mhz, N)

                        peak_idx = int(np.argmax(magnitude_db))
                        peak_freq_khz = float(freq_axis[peak_idx] * 1000.0)
                        peak_pwr = float(magnitude_db[peak_idx])
                        noise_floor_est = float(np.median(magnitude_db))

                        self.spectrum_ready.emit(
                            freq_axis,
                            magnitude_db,
                            peak_freq_khz,
                            peak_pwr,
                            noise_floor_est,
                            N,
                        )

                        # 2. Yazılımsal Demodülasyon (AM / FM / NBFM)
                        if self.demod_mode != "OFF":
                            if self.demod_mode == "AM":
                                audio, pwr_db = demodulate_am(
                                    latest_iq, squelch_db=self.squelch_db, volume=self.volume
                                )
                            elif self.demod_mode == "NBFM":
                                audio, pwr_db = demodulate_nbfm(
                                    latest_iq, squelch_db=self.squelch_db, volume=self.volume
                                )
                            else:  # FM
                                audio, pwr_db = demodulate_fm(
                                    latest_iq, squelch_db=self.squelch_db, volume=self.volume
                                )

                            self.demod_audio_ready.emit(audio, pwr_db)

                        # 3. Dijital Taktik Telemetri Çözümleme
                        decoded_pkt = self.decoder.decode_frame(latest_iq, self.frame_index)
                        if decoded_pkt:
                            self.digital_payload_ready.emit(decoded_pkt)

                        # 4. Kayıt İstatistikleri
                        if self.recorder.is_recording:
                            stats = self.recorder.get_stats()
                            self.record_stats_signal.emit(
                                stats["samples"], stats["frames"], stats["size_mb"]
                            )

        except Exception as e:
            self.log_signal.emit("HATA", f"DSP İş parçacığında hata: {e}")
        finally:
            if self.recorder.is_recording:
                self.recorder.stop_recording()
            sub.close()
            ctx.term()
            self.log_signal.emit("BİLGİ", "Arka plan DSP iş parçacığı güvenle kapatıldı.")

    def set_demod_config(self, mode: str, squelch_db: float, volume: float):
        """Demodülasyon yapılandırmasını günceller."""
        self.demod_mode = mode
        self.squelch_db = squelch_db
        self.volume = volume

    def start_recording(self, filepath: Optional[str] = None):
        path = self.recorder.start_recording(
            filepath=filepath,
            sample_rate=self.sample_rate,
            center_freq_mhz=self.center_freq_mhz,
        )
        if path:
            self.log_signal.emit("KAYIT", f"Sinyal dosyası kaydediliyor: {os.path.basename(path)}")

    def stop_recording(self) -> Optional[dict]:
        stats = self.recorder.stop_recording()
        if stats:
            self.log_signal.emit(
                "KAYIT",
                f"Kayıt tamamlandı: {os.path.basename(stats['file_path'])} "
                f"({stats['total_samples']} örnek, {stats['total_bytes']/1024/1024:.2f} MB)",
            )
        return stats

    def stop(self):
        self._running = False
        self.wait(1500)


class TacticalMainWindow(QMainWindow):
    """Antigravity Taktik SDR Terminali Ana Pencere Sınıfı."""

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.is_recording = False
        self.is_playing = False
        self.audio_output_enabled = False

        # DSP & FFT Parametreleri
        self.sample_rate = 2.048e6
        self.center_freq_mhz = 433.0
        self.fft_size = 1024
        self.history_depth = 150
        self.total_frames_received = 0
        self.last_fps_time = time.time()
        self.fps_counter = 0

        # Şelale 2D Tamponu
        self.waterfall_data = np.full((self.fft_size, self.history_depth), -115.0, dtype=np.float32)

        # Oynatma İş Parçacığı & Ses Motoru
        self.playback_thread: Optional[IQPlaybackThread] = None
        self.selected_playback_filepath = ""
        self.audio_engine = TacticalAudioOutput(sample_rate=8000)

        # ZeroMQ PUB (Ping Testi)
        self.zmq_pub = None
        self.init_zmq()

        # Arayüzü Kur
        self.init_ui()

        # Optimize Edilmiş Çoklu İş Parçacığı (QThread) Motoru
        self.dsp_worker = DSPWorkerThread(address="tcp://127.0.0.1:5555", sample_rate=self.sample_rate)
        self.dsp_worker.center_freq_mhz = self.center_freq_mhz
        self.dsp_worker.spectrum_ready.connect(self.on_spectrum_data_ready)
        self.dsp_worker.demod_audio_ready.connect(self.on_demod_audio_ready)
        self.dsp_worker.digital_payload_ready.connect(self.on_digital_payload_decoded)
        self.dsp_worker.record_stats_signal.connect(self.on_record_stats_update)
        self.dsp_worker.log_signal.connect(self.log_message)

        # Başlangıç Loglarını Konsola İlet
        self.log_message("SYSTEM", "Antigravity Taktik SDR Terminali başlatıldı (Faz 12 - Demodülasyon & Çözücü Aktif).")
        self.log_message("INFO", "Taktik GUI, AM/FM Demodülatör ve Dijital Telemetri motoru hazır.")

        # İlk link bütçesi hesaplamasını otomatik tetikle
        self.calculate_rf_coverage()

    def init_zmq(self):
        try:
            self.zmq_pub = ZMQPublisher(address="tcp://127.0.0.1:5555", bind_mode=False)
        except Exception as e:
            print(f"[ZMQ HATA] {e}")

    def init_ui(self):
        self.setWindowTitle("Antigravity Taktik SDR Terminali")
        self.resize(1440, 930)
        self.setMinimumSize(1120, 740)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        main_layout.addWidget(main_splitter)

        sidebar_widget = self.create_sidebar()
        main_splitter.addWidget(sidebar_widget)

        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)

        main_splitter.setSizes([320, 1120])

        self.setup_status_bar()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

    def create_sidebar(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(300)
        sidebar.setMaximumWidth(380)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Başlık
        header_layout = QVBoxLayout()
        header_title = QLabel("KONTROL PANELİ")
        header_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #00ff66; letter-spacing: 1.5px;"
        )
        header_subtitle = QLabel("TAKTİK SDR YÖNETİM MERKEZİ")
        header_subtitle.setStyleSheet("font-size: 10px; color: #8b949e; letter-spacing: 1px;")
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)
        layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #30363d; max-height: 1px;")
        layout.addWidget(line)

        # 1. Sistem Kontrolü
        sys_group = QGroupBox("SİSTEM KONTROLÜ")
        sys_layout = QVBoxLayout(sys_group)
        sys_layout.setSpacing(8)

        self.btn_start = QPushButton("Sistemi Başlat")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setToolTip("Terminali ve veri alımını başlatır")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.toggle_system)
        sys_layout.addWidget(self.btn_start)

        self.btn_ping = QPushButton("Bağlantı Testi")
        self.btn_ping.setObjectName("btn_ping")
        self.btn_ping.setToolTip("ZeroMQ PUB/SUB köprüsünü PING mesajı ile test eder")
        self.btn_ping.setCursor(Qt.PointingHandCursor)
        self.btn_ping.clicked.connect(self.perform_zmq_ping_test)
        sys_layout.addWidget(self.btn_ping)

        self.lbl_system_status = QLabel("● DURUM: BEKLEMEDE")
        self.lbl_system_status.setStyleSheet(
            "color: #ffaa00; font-weight: bold; font-size: 11px; padding: 2px;"
        )
        self.lbl_system_status.setAlignment(Qt.AlignCenter)
        sys_layout.addWidget(self.lbl_system_status)

        layout.addWidget(sys_group)

        # 2. I/Q Sinyal Kaydı ve Oynatma
        record_group = QGroupBox("I/Q SİNYAL KAYDI VE OYNATMA")
        rec_layout = QVBoxLayout(record_group)
        rec_layout.setSpacing(8)

        lbl_rec_sub = QLabel("HAM I/Q KAYIT MOTORU")
        lbl_rec_sub.setStyleSheet("font-size: 10px; color: #ff7b72; font-weight: bold;")
        rec_layout.addWidget(lbl_rec_sub)

        self.btn_record = QPushButton("Kaydı Başlat")
        self.btn_record.setObjectName("btn_record_start")
        self.btn_record.setToolTip("Canlı I/Q veri akışını diske (.raw ve SigMF meta) kaydeder")
        self.btn_record.setCursor(Qt.PointingHandCursor)
        self.btn_record.clicked.connect(self.toggle_recording)
        rec_layout.addWidget(self.btn_record)

        self.lbl_record_status = QLabel("● KAYIT: PASİF")
        self.lbl_record_status.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.lbl_record_status.setAlignment(Qt.AlignCenter)
        rec_layout.addWidget(self.lbl_record_status)

        rec_line = QFrame()
        rec_line.setFrameShape(QFrame.HLine)
        rec_line.setStyleSheet("background-color: #21262d; max-height: 1px;")
        rec_layout.addWidget(rec_line)

        lbl_play_sub = QLabel("SİNYAL OYNATICI (PLAYBACK)")
        lbl_play_sub.setStyleSheet("font-size: 10px; color: #38d39f; font-weight: bold;")
        rec_layout.addWidget(lbl_play_sub)

        play_file_layout = QHBoxLayout()
        self.btn_browse = QPushButton("Dosya Seç")
        self.btn_browse.setObjectName("btn_small")
        self.btn_browse.setToolTip("Kayıtlı I/Q dosyasını seçin")
        self.btn_browse.clicked.connect(self.browse_iq_file)
        play_file_layout.addWidget(self.btn_browse)

        self.lbl_selected_file = QLabel("Dosya: Seçilmedi")
        self.lbl_selected_file.setStyleSheet("color: #8b949e; font-size: 11px;")
        play_file_layout.addWidget(self.lbl_selected_file, stretch=1)
        rec_layout.addLayout(play_file_layout)

        self.chk_loop = QCheckBox("Döngüsel Oynat (Loop)")
        self.chk_loop.setChecked(True)
        self.chk_loop.setStyleSheet("color: #8b949e; font-size: 11px;")
        rec_layout.addWidget(self.chk_loop)

        self.btn_play = QPushButton("Oynatmayı Başlat")
        self.btn_play.setObjectName("btn_play_start")
        self.btn_play.setToolTip("Seçili I/Q dosyasını ZMQ üzerinden canlı sinyal gibi yayınlar")
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.clicked.connect(self.toggle_playback)
        rec_layout.addWidget(self.btn_play)

        self.lbl_playback_status = QLabel("● OYNATMA: PASİF")
        self.lbl_playback_status.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.lbl_playback_status.setAlignment(Qt.AlignCenter)
        rec_layout.addWidget(self.lbl_playback_status)

        layout.addWidget(record_group)

        # 3. RF Donanım Parametreleri
        rf_group = QGroupBox("RF DONANIM PARAMETRELERİ")
        rf_layout = QVBoxLayout(rf_group)
        rf_layout.setSpacing(6)

        lbl_freq = QLabel(f"Merkez Frekans: {self.center_freq_mhz:.2f} MHz")
        lbl_freq.setStyleSheet("color: #8b949e; font-size: 12px;")
        lbl_gain = QLabel("Donanım Kazancı: 20 dB")
        lbl_gain.setStyleSheet("color: #8b949e; font-size: 12px;")
        lbl_sample_rate = QLabel(f"Örnekleme Hızı: {self.sample_rate/1e6:.3f} MS/s")
        lbl_sample_rate.setStyleSheet("color: #8b949e; font-size: 12px;")

        rf_layout.addWidget(lbl_freq)
        rf_layout.addWidget(lbl_gain)
        rf_layout.addWidget(lbl_sample_rate)

        layout.addWidget(rf_group)

        # 4. Aktif Modüller
        module_group = QGroupBox("AKTİF MODÜLLER")
        mod_layout = QVBoxLayout(module_group)
        mod_layout.setSpacing(5)

        lbl_m1 = QLabel("✔ AM / FM / NBFM Demodülatör")
        lbl_m1.setStyleSheet("color: #00ff66; font-size: 11px;")
        lbl_m2 = QLabel("✔ Dijital Telemetri Çözücü")
        lbl_m2.setStyleSheet("color: #00ff66; font-size: 11px;")
        lbl_m3 = QLabel("✔ I/Q Kayıt & Oynatma")
        lbl_m3.setStyleSheet("color: #00ff66; font-size: 11px;")
        lbl_m4 = QLabel("✔ Spektrum & Şelale Göstergesi")
        lbl_m4.setStyleSheet("color: #00ff66; font-size: 11px;")

        mod_layout.addWidget(lbl_m1)
        mod_layout.addWidget(lbl_m2)
        mod_layout.addWidget(lbl_m3)
        mod_layout.addWidget(lbl_m4)

        layout.addWidget(module_group)

        layout.addStretch()

        lbl_footer = QLabel("ANTIGRAVITY // TACTICAL SDR")
        lbl_footer.setStyleSheet("color: #484f58; font-size: 10px; letter-spacing: 2px;")
        lbl_footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_footer)

        scroll.setWidget(sidebar)
        return scroll

    def create_right_panel(self) -> QWidget:
        right_container = QWidget()
        layout = QVBoxLayout(right_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.setChildrenCollapsible(False)

        # 1. Merkezi Sekme Alanı (3 Sekme)
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        tab_spectrum_waterfall = self.create_spectrum_waterfall_tab()
        self.tab_widget.addTab(tab_spectrum_waterfall, "📡 Spektrum & Şelale")

        tab_demodulation = self.create_demodulation_tab()
        self.tab_widget.addTab(tab_demodulation, "📻 Demodülasyon & Çözücü")

        tab_rf_coverage = self.create_rf_coverage_tab()
        self.tab_widget.addTab(tab_rf_coverage, "📊 RF Kapsama Alanı")

        self.right_splitter.addWidget(self.tab_widget)

        # 2. Sistem Logları Konsol Paneli
        console_panel = self.create_console_panel()
        self.right_splitter.addWidget(console_panel)

        self.right_splitter.setSizes([710, 180])

        layout.addWidget(self.right_splitter)
        return right_container

    def create_demodulation_tab(self) -> QWidget:
        """Yazılımsal Demodülasyon (AM/FM/NBFM) ve Dijital Çözücü Sekmesini oluşturur."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. Başlık Çubuğu
        header_bar = QHBoxLayout()
        title = QLabel("YAZILIMSAL DEMODÜLASYON & DİJİTAL SİNYAL ÇÖZÜCÜ")
        title.setStyleSheet(
            "color: #00ff66; font-size: 15px; font-weight: bold; letter-spacing: 1px;"
        )
        header_bar.addWidget(title)
        header_bar.addStretch()

        self.lbl_demod_badge = QLabel("[ MOD: KAPALI ]")
        self.lbl_demod_badge.setStyleSheet("color: #8b949e; font-weight: bold; font-size: 11px;")
        header_bar.addWidget(self.lbl_demod_badge)
        layout.addLayout(header_bar)

        # 2. Demodülasyon & Ses Kontrol Paneli
        ctrl_group = QGroupBox("DEMODÜLASYON VE SES KONTROLÜ")
        grid = QGridLayout(ctrl_group)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        # Demodülasyon Modu Seçici
        lbl_mode = QLabel("Demodülasyon Modu:")
        self.cmb_demod_mode = QComboBox()
        self.cmb_demod_mode.addItems(["KAPALI (Off)", "AM Alıcısı", "FM Alıcısı", "NBFM (Dar Bant FM)"])
        self.cmb_demod_mode.currentIndexChanged.connect(self.on_demod_config_changed)
        self.cmb_demod_mode.setToolTip("Yazılımsal demodülasyon algoritmasını seçer")

        # Susturma (Squelch) Ayarı
        lbl_squelch = QLabel("Susturma (Squelch):")
        self.spin_squelch = QDoubleSpinBox()
        self.spin_squelch.setRange(-120.0, 0.0)
        self.spin_squelch.setValue(-80.0)
        self.spin_squelch.setDecimals(1)
        self.spin_squelch.setSingleStep(2.0)
        self.spin_squelch.setSuffix(" dB")
        self.spin_squelch.setToolTip("Bu eşiğin altındaki sinyaller susturulur (Squelch)")
        self.spin_squelch.valueChanged.connect(self.on_demod_config_changed)

        # Ses Seviyesi (Volume)
        lbl_vol = QLabel("Ses Seviyesi:")
        self.spin_volume = QDoubleSpinBox()
        self.spin_volume.setRange(0.0, 200.0)
        self.spin_volume.setValue(100.0)
        self.spin_volume.setDecimals(0)
        self.spin_volume.setSingleStep(5.0)
        self.spin_volume.setSuffix(" %")
        self.spin_volume.setToolTip("Demodüle edilmiş ses çıkış kazancı")
        self.spin_volume.valueChanged.connect(self.on_demod_config_changed)

        # "Sesi Başlat" / "Sesi Kapat" Butonu
        self.btn_audio = QPushButton("Sesi Başlat")
        self.btn_audio.setObjectName("btn_audio_active")
        self.btn_audio.setToolTip("Demodüle edilen sesi hoparlöre aktarır")
        self.btn_audio.setCursor(Qt.PointingHandCursor)
        self.btn_audio.clicked.connect(self.toggle_audio_output)

        grid.addWidget(lbl_mode, 0, 0)
        grid.addWidget(self.cmb_demod_mode, 0, 1)
        grid.addWidget(lbl_squelch, 0, 2)
        grid.addWidget(self.spin_squelch, 0, 3)
        grid.addWidget(lbl_vol, 0, 4)
        grid.addWidget(self.spin_volume, 0, 5)
        grid.addWidget(self.btn_audio, 0, 6)

        layout.addWidget(ctrl_group)

        # 3. İki Bölümlü Alt Alan (Üstte Ses Dalga Şekli, Altta Dijital Telemetri Çözücü)
        demod_splitter = QSplitter(Qt.Vertical)
        demod_splitter.setChildrenCollapsible(False)

        # 3A. Ses Dalga Şekli (Audio Waveform Plot)
        audio_frame = QFrame()
        audio_layout = QVBoxLayout(audio_frame)
        audio_layout.setContentsMargins(0, 0, 0, 0)
        audio_layout.setSpacing(6)

        audio_header = QHBoxLayout()
        lbl_wave_title = QLabel("DEMODÜLE SES DALGA ŞEKLİ (OSİLOSKOP)")
        lbl_wave_title.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 11px;")
        audio_header.addWidget(lbl_wave_title)
        audio_header.addStretch()

        self.lbl_squelch_status = QLabel("SQUELCH: AÇIK")
        self.lbl_squelch_status.setStyleSheet("color: #00ff66; font-size: 10px; font-weight: bold;")
        audio_header.addWidget(self.lbl_squelch_status)

        self.lbl_audio_pwr = QLabel("GÜÇ: -- dB")
        self.lbl_audio_pwr.setStyleSheet("color: #8b949e; font-size: 10px;")
        audio_header.addWidget(self.lbl_audio_pwr)

        audio_layout.addLayout(audio_header)

        self.audio_plot = pg.PlotWidget()
        self.audio_plot.setBackground("#090d13")
        self.audio_plot.showGrid(x=True, y=True, alpha=0.25)
        self.audio_plot.setLabel("left", "Genlik", color="#c9d1d9")
        self.audio_plot.setLabel("bottom", "Örnek", color="#c9d1d9")
        self.audio_plot.setYRange(-1.2, 1.2, padding=0.05)

        self.audio_curve = self.audio_plot.plot(
            pen=pg.mkPen(color="#38d39f", width=1.5),
            name="Ses Dalga Şekli"
        )
        audio_layout.addWidget(self.audio_plot)

        demod_splitter.addWidget(audio_frame)

        # 3B. Dijital Telemetri Çözücü (Digital Decoder Terminal)
        decoder_frame = QFrame()
        decoder_layout = QVBoxLayout(decoder_frame)
        decoder_layout.setContentsMargins(0, 0, 0, 0)
        decoder_layout.setSpacing(6)

        dec_header = QHBoxLayout()
        lbl_dec_title = QLabel("DİJİTAL VERİ ÇÖZÜCÜ (DECODER & TELEMETRY)")
        lbl_dec_title.setStyleSheet("color: #00ff66; font-weight: bold; font-size: 11px;")
        dec_header.addWidget(lbl_dec_title)
        dec_header.addStretch()

        btn_clear_dec = QPushButton("Temizle")
        btn_clear_dec.setObjectName("btn_small")
        btn_clear_dec.clicked.connect(self.clear_decoder_log)
        dec_header.addWidget(btn_clear_dec)

        decoder_layout.addLayout(dec_header)

        self.txt_decoder = QTextEdit()
        self.txt_decoder.setObjectName("decoder_log")
        self.txt_decoder.setReadOnly(True)
        self.txt_decoder.setAcceptRichText(True)
        decoder_layout.addWidget(self.txt_decoder)

        demod_splitter.addWidget(decoder_frame)
        demod_splitter.setSizes([260, 260])

        layout.addWidget(demod_splitter, stretch=1)
        return container

    def on_demod_config_changed(self):
        """Kullanıcı demodülasyon ayarını değiştirdiğinde QThread motorunu günceller."""
        raw_mode = self.cmb_demod_mode.currentText()
        if "AM" in raw_mode:
            mode = "AM"
            badge_color = "#38d39f"
        elif "NBFM" in raw_mode:
            mode = "NBFM"
            badge_color = "#58a6ff"
        elif "FM" in raw_mode:
            mode = "FM"
            badge_color = "#00ff66"
        else:
            mode = "OFF"
            badge_color = "#8b949e"

        squelch_db = self.spin_squelch.value()
        volume = self.spin_volume.value() / 100.0

        self.dsp_worker.set_demod_config(mode=mode, squelch_db=squelch_db, volume=volume)

        self.lbl_demod_badge.setText(f"[ MOD: {mode} ]")
        self.lbl_demod_badge.setStyleSheet(f"color: {badge_color}; font-weight: bold; font-size: 11px;")
        self.log_message("BİLGİ", f"Demodülatör yapılandırması güncellendi: Mod={mode}, Squelch={squelch_db:.1f}dB, Ses=%{volume*100:.0f}")

    def toggle_audio_output(self):
        """Hoparlör ses çıkışını açar veya kapatır."""
        self.audio_output_enabled = not self.audio_output_enabled
        if self.audio_output_enabled:
            self.btn_audio.setText("Sesi Kapat")
            self.btn_audio.setStyleSheet("background-color: #5c1d24; color: #ff7b72; border: 1px solid #ff7b72;")
            self.audio_engine.start_audio()
            self.log_message("BİLGİ", "Taktik ses çıkışı hoparlörlere aktarılıyor.")
        else:
            self.btn_audio.setText("Sesi Başlat")
            self.btn_audio.setStyleSheet("background-color: #1b382b; color: #00ff66; border: 1px solid #00ff66;")
            self.audio_engine.stop_audio()
            self.log_message("BİLGİ", "Ses çıkışı kapatıldı.")

    def on_demod_audio_ready(self, audio_samples: np.ndarray, power_db: float):
        """Demodüle edilen ses dalga şeklini ve susturma durumunu günceller."""
        if len(audio_samples) > 0:
            # Osiloskop eğrisini güncelle
            x_axis = np.arange(len(audio_samples))
            self.audio_curve.setData(x_axis, audio_samples)

            # Hoparlöre aktar
            if self.audio_output_enabled:
                self.audio_engine.write_audio_samples(audio_samples)

        # Susturma / Güç Durumu
        self.lbl_audio_pwr.setText(f"GÜÇ: {power_db:.1f} dB")
        if power_db < self.spin_squelch.value():
            self.lbl_squelch_status.setText("SQUELCH: SUSTURULDU")
            self.lbl_squelch_status.setStyleSheet("color: #ff7b72; font-size: 10px; font-weight: bold;")
        else:
            self.lbl_squelch_status.setText("SQUELCH: AÇIK (SİNYAL AKTİF)")
            self.lbl_squelch_status.setStyleSheet("color: #00ff66; font-size: 10px; font-weight: bold;")

    def on_digital_payload_decoded(self, pkt: dict):
        """Çözülen dijital taktik telemetri paketini ekrana formatlı olarak yansıtır."""
        pkt_no = pkt["paket_no"]
        callsign = pkt["cagri_kodu"]
        station = pkt["istasyon"]
        proto = pkt["protokol"]
        coords = pkt["koordinat"]
        rssi = pkt["rssi_dbm"]
        ber = pkt["ber_orani"]
        msg = pkt["mesaj"]
        ts = pkt["zaman"]

        html = (
            f'<div style="margin-bottom: 6px; border-bottom: 1px solid #21262d; padding-bottom: 4px;">'
            f'<span style="color: #6e7681;">[{ts}]</span> '
            f'<span style="color: #00ff66; font-weight: bold;">[PAKET #{pkt_no:04d}]</span> '
            f'<span style="color: #58a6ff; font-weight: bold;">{callsign}</span> '
            f'<span style="color: #8b949e;">({station})</span> | '
            f'<span style="color: #ffd33d;">Protokol: {proto}</span> | '
            f'<span style="color: #38d39f;">Konum: {coords}</span> | '
            f'<span style="color: #79c0ff;">RSSI: {rssi} dBm</span> | '
            f'<span style="color: #ff7b72;">BER: {ber}</span><br>'
            f'<span style="color: #f0f6fc; margin-left: 20px;">↳ {msg}</span>'
            f'</div>'
        )
        self.txt_decoder.append(html)
        self.txt_decoder.moveCursor(QTextCursor.End)
        self.log_message("BİLGİ", f"Dijital Telemetri Çözüldü: {callsign} ({coords}) RSSI={rssi}dBm")

    def clear_decoder_log(self):
        self.txt_decoder.clear()

    def create_console_panel(self) -> QWidget:
        container = QFrame()
        container.setStyleSheet("background-color: #161b22; border-top: 1px solid #30363d;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title_label = QLabel("SİSTEM LOGLARI")
        title_label.setStyleSheet("color: #00ff66; font-weight: bold; font-size: 12px; letter-spacing: 1px;")

        badge = QLabel("[ CANLI KONSOL GÜNLÜĞÜ ]")
        badge.setStyleSheet("color: #8b949e; font-size: 10px;")

        btn_clear = QPushButton("Temizle")
        btn_clear.setObjectName("btn_small")
        btn_clear.setToolTip("Konsol loglarını temizler")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self.clear_logs)

        header.addWidget(title_label)
        header.addWidget(badge)
        header.addStretch()
        header.addWidget(btn_clear)

        layout.addLayout(header)

        self.txt_console = QTextEdit()
        self.txt_console.setObjectName("console_log")
        self.txt_console.setReadOnly(True)
        self.txt_console.setAcceptRichText(True)
        layout.addWidget(self.txt_console)

        return container

    def log_message(self, level: str, message: str):
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        level_upper = level.upper()

        if level_upper in ["SYSTEM", "SİSTEM"]:
            tag = "SİSTEM"
            tag_color = "#00ff66"
            text_color = "#f0f6fc"
        elif level_upper in ["INFO", "BİLGİ"]:
            tag = "BİLGİ"
            tag_color = "#58a6ff"
            text_color = "#c9d1d9"
        elif level_upper in ["STATUS", "DURUM"]:
            tag = "DURUM"
            tag_color = "#39ff14"
            text_color = "#f0f6fc"
        elif level_upper in ["KAYIT"]:
            tag = "KAYIT"
            tag_color = "#ff7b72"
            text_color = "#ffa198"
        elif level_upper in ["OYNATMA", "PLAYBACK"]:
            tag = "OYNATMA"
            tag_color = "#38d39f"
            text_color = "#7ee787"
        elif level_upper in ["WARN", "UYARI"]:
            tag = "UYARI"
            tag_color = "#ffaa00"
            text_color = "#ffd33d"
        elif level_upper in ["ERROR", "HATA"]:
            tag = "HATA"
            tag_color = "#ff4d4f"
            text_color = "#ff7b72"
        elif level_upper in ["RF", "RF ANALİZ"]:
            tag = "RF ANALİZ"
            tag_color = "#38d39f"
            text_color = "#e6edf3"
        elif level_upper in ["SUCCESS", "BAŞARILI"]:
            tag = "BAŞARILI"
            tag_color = "#00ff66"
            text_color = "#f0f6fc"
        else:
            tag = level_upper
            tag_color = "#8b949e"
            text_color = "#c9d1d9"

        formatted_html = (
            f'<div style="margin-bottom: 2px;">'
            f'<span style="color: #6e7681; font-weight: normal;">[{timestamp}]</span> '
            f'<span style="color: {tag_color}; font-weight: bold;">[{tag}]</span> '
            f'<span style="color: {text_color};">{message}</span>'
            f'</div>'
        )

        self.txt_console.append(formatted_html)
        self.txt_console.moveCursor(QTextCursor.End)

    def clear_logs(self):
        self.txt_console.clear()
        self.log_message("SYSTEM", "Konsol günlüğü temizlendi.")

    def create_spectrum_waterfall_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_bar = QHBoxLayout()
        title = QLabel("GERÇEK ZAMANLI SPEKTRUM & ŞELALE GÖSTERGESİ")
        title.setStyleSheet(
            "color: #00ff66; font-size: 15px; font-weight: bold; letter-spacing: 1px;"
        )
        header_bar.addWidget(title)
        header_bar.addStretch()

        self.lbl_dsp_badge = QLabel("[ AKIŞ: BEKLEMEDE ]")
        self.lbl_dsp_badge.setStyleSheet("color: #ffaa00; font-weight: bold; font-size: 11px;")
        header_bar.addWidget(self.lbl_dsp_badge)

        layout.addLayout(header_bar)

        hud_layout = QHBoxLayout()
        hud_layout.setSpacing(12)

        self.card_peak_freq = QLabel("-- kHz")
        c1 = self.create_hud_card("TEPE FREKANSI OFSETİ", self.card_peak_freq, "#00ff66")
        hud_layout.addWidget(c1)

        self.card_peak_pwr = QLabel("-- dB")
        c2 = self.create_hud_card("TEPE GÜCÜ", self.card_peak_pwr, "#58a6ff")
        hud_layout.addWidget(c2)

        self.card_noise_floor = QLabel("-- dB")
        c3 = self.create_hud_card("TABAN GÜRÜLTÜSÜ", self.card_noise_floor, "#f0f6fc")
        hud_layout.addWidget(c3)

        self.card_fps_val = QLabel("0.0 FPS")
        c4 = self.create_hud_card("GÖSTERİM HIZI", self.card_fps_val, "#ffaa00")
        hud_layout.addWidget(c4)

        layout.addLayout(hud_layout)

        display_splitter = QSplitter(Qt.Vertical)
        display_splitter.setChildrenCollapsible(False)

        self.spectrum_plot = pg.PlotWidget()
        self.spectrum_plot.setBackground("#090d13")
        self.spectrum_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectrum_plot.setLabel("left", "Genlik (dB)", color="#c9d1d9")
        self.spectrum_plot.setLabel("bottom", "Frekans (Bant)", units="MHz", color="#c9d1d9")
        self.spectrum_plot.setTitle(
            '<span style="color: #00ff66; font-size: 12px; font-weight: bold;">'
            "Gerçek Zamanlı Spektrum Analizi</span>"
        )
        self.spectrum_plot.setYRange(-120, 10, padding=0.02)

        self.spectrum_curve = self.spectrum_plot.plot(
            pen=pg.mkPen(color="#00ff66", width=1.8),
            name="Anlık Spektrum"
        )
        self.max_hold_curve = self.spectrum_plot.plot(
            pen=pg.mkPen(color="#388bfd", width=1.2, style=Qt.DashLine),
            name="Tepe Tutma (Max-Hold)"
        )
        self.max_hold_data = None

        display_splitter.addWidget(self.spectrum_plot)

        self.waterfall_plot = pg.PlotWidget()
        self.waterfall_plot.setBackground("#090d13")
        self.waterfall_plot.setLabel("left", "Zaman", color="#c9d1d9")
        self.waterfall_plot.setLabel("bottom", "Frekans", units="MHz", color="#c9d1d9")
        self.waterfall_plot.setTitle(
            '<span style="color: #00ff66; font-size: 12px; font-weight: bold;">'
            "Şelale Ekranı (Zaman Geçmişi)</span>"
        )

        self.waterfall_plot.setXLink(self.spectrum_plot)

        self.waterfall_img = pg.ImageItem()
        self.waterfall_plot.addItem(self.waterfall_img)

        tactical_cmap = create_tactical_colormap()
        lut = tactical_cmap.getLookupTable(0.0, 1.0, 256)
        self.waterfall_img.setLookupTable(lut)

        half_bw_mhz = (self.sample_rate / 2.0) / 1e6
        self.waterfall_img.setRect(QRectF(-half_bw_mhz, 0, 2.0 * half_bw_mhz, self.history_depth))
        self.waterfall_img.setImage(self.waterfall_data, autoLevels=False, levels=[-110.0, -25.0])

        display_splitter.addWidget(self.waterfall_plot)
        display_splitter.setSizes([320, 320])

        layout.addWidget(display_splitter, stretch=1)
        return container

    def create_rf_coverage_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header_bar = QHBoxLayout()
        title = QLabel("RF LİNK BÜTÇESİ & KAPSAMA ALANI ANALİZİ")
        title.setStyleSheet(
            "color: #00ff66; font-size: 15px; font-weight: bold; letter-spacing: 1px;"
        )
        header_bar.addWidget(title)
        header_bar.addStretch()

        badge = QLabel("[ MODEL: FRİİS SERBEST UZAY YAYILIMI (FSPL) ]")
        badge.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 11px;")
        header_bar.addWidget(badge)
        layout.addLayout(header_bar)

        input_group = QGroupBox("RF İLETİM VE ALICI PARAMETRELERİ")
        grid = QGridLayout(input_group)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(12)

        lbl_freq = QLabel("Frekans (MHz):")
        self.spin_freq = QDoubleSpinBox()
        self.spin_freq.setRange(1.0, 60000.0)
        self.spin_freq.setValue(433.0)
        self.spin_freq.setDecimals(2)
        self.spin_freq.setSingleStep(10.0)
        self.spin_freq.setToolTip("Taşıyıcı sinyalin merkez frekansı (MHz cinsinden)")

        lbl_tx_power = QLabel("İletim Gücü (dBm):")
        self.spin_tx_power = QDoubleSpinBox()
        self.spin_tx_power.setRange(-30.0, 100.0)
        self.spin_tx_power.setValue(20.0)
        self.spin_tx_power.setDecimals(1)
        self.spin_tx_power.setSingleStep(1.0)
        self.spin_tx_power.setToolTip("Verici çıkış gücü (dBm cinsinden)")

        lbl_tx_gain = QLabel("Tx Kazancı (dBi):")
        self.spin_tx_gain = QDoubleSpinBox()
        self.spin_tx_gain.setRange(-20.0, 60.0)
        self.spin_tx_gain.setValue(2.15)
        self.spin_tx_gain.setDecimals(2)
        self.spin_tx_gain.setSingleStep(0.5)
        self.spin_tx_gain.setToolTip("Verici anten kazancı (dBi cinsinden)")

        lbl_rx_gain = QLabel("Rx Kazancı (dBi):")
        self.spin_rx_gain = QDoubleSpinBox()
        self.spin_rx_gain.setRange(-20.0, 60.0)
        self.spin_rx_gain.setValue(2.15)
        self.spin_rx_gain.setDecimals(2)
        self.spin_rx_gain.setSingleStep(0.5)
        self.spin_rx_gain.setToolTip("Alıcı anten kazancı (dBi cinsinden)")

        lbl_distance = QLabel("Hedef Mesafe (km):")
        self.spin_distance = QDoubleSpinBox()
        self.spin_distance.setRange(0.01, 1000.0)
        self.spin_distance.setValue(10.0)
        self.spin_distance.setDecimals(2)
        self.spin_distance.setSingleStep(1.0)
        self.spin_distance.setToolTip("Analiz edilecek hedef mesafe (km cinsinden)")

        self.btn_calc = QPushButton("Hesapla")
        self.btn_calc.setObjectName("btn_calculate")
        self.btn_calc.setToolTip("Friis denklemini kullanarak RF link bütçesini ve menzil eğrisini hesaplar")
        self.btn_calc.setCursor(Qt.PointingHandCursor)
        self.btn_calc.clicked.connect(self.calculate_rf_coverage)

        grid.addWidget(lbl_freq, 0, 0)
        grid.addWidget(self.spin_freq, 0, 1)
        grid.addWidget(lbl_tx_power, 0, 2)
        grid.addWidget(self.spin_tx_power, 0, 3)
        grid.addWidget(lbl_tx_gain, 0, 4)
        grid.addWidget(self.spin_tx_gain, 0, 5)

        grid.addWidget(lbl_rx_gain, 1, 0)
        grid.addWidget(self.spin_rx_gain, 1, 1)
        grid.addWidget(lbl_distance, 1, 2)
        grid.addWidget(self.spin_distance, 1, 3)
        grid.addWidget(self.btn_calc, 1, 4, 1, 2)

        layout.addWidget(input_group)

        hud_layout = QHBoxLayout()
        hud_layout.setSpacing(12)

        self.card_fspl_val = QLabel("-- dB")
        card_fspl = self.create_hud_card("SERBEST UZAY KAYBI (FSPL)", self.card_fspl_val, "#f0f6fc")
        hud_layout.addWidget(card_fspl)

        self.card_prx_val = QLabel("-- dBm")
        card_prx = self.create_hud_card("HEDEF ALINAN GÜÇ (Prx)", self.card_prx_val, "#00ff66")
        hud_layout.addWidget(card_prx)

        self.card_eirp_val = QLabel("-- dBm")
        card_eirp = self.create_hud_card("EIRP (IŞIMA GÜCÜ)", self.card_eirp_val, "#58a6ff")
        hud_layout.addWidget(card_eirp)

        self.card_status_val = QLabel("HESAPLANIYOR")
        card_status = self.create_hud_card("BAĞLANTI KALİTESİ", self.card_status_val, "#00ff66")
        hud_layout.addWidget(card_status)

        layout.addLayout(hud_layout)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#090d13")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("left", "Alınan Güç", units="dBm", color="#c9d1d9")
        self.plot_widget.setLabel("bottom", "Mesafe", units="km", color="#c9d1d9")
        self.plot_widget.setTitle(
            '<span style="color: #00ff66; font-size: 13px; font-weight: bold;">'
            "Alınan Güç - Mesafe Eğrisi (Friis İletim Modeli)</span>"
        )
        self.plot_widget.addLegend(offset=(20, 20), labelTextColor="#c9d1d9")

        self.curve_rx = self.plot_widget.plot(
            pen=pg.mkPen(color="#00ff66", width=2.5),
            name="Alınan Güç Eğrisi (Prx)"
        )
        self.point_target = self.plot_widget.plot(
            pen=None,
            symbol="o",
            symbolSize=10,
            symbolBrush=pg.mkBrush("#ff4d4f"),
            name="Hedef Mesafe Noktası"
        )
        self.line_threshold = self.plot_widget.plot(
            pen=pg.mkPen(color="#ffaa00", width=1.5, style=Qt.DashLine),
            name="Referans Hassasiyet Eşiği (-100 dBm)"
        )

        layout.addWidget(self.plot_widget, stretch=1)
        return container

    def create_hud_card(self, title_text: str, value_label: QLabel, val_color: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("color: #8b949e; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")

        value_label.setStyleSheet(f"color: {val_color}; font-size: 15px; font-weight: bold; font-family: Consolas;")

        layout.addWidget(lbl_title)
        layout.addWidget(value_label)
        return frame

    def on_spectrum_data_ready(
        self,
        freq_axis: np.ndarray,
        magnitude_db: np.ndarray,
        peak_freq_khz: float,
        peak_pwr: float,
        noise_floor_est: float,
        N: int,
    ):
        self.fft_size = N
        self.total_frames_received += 1
        self.fps_counter += 1

        self.spectrum_curve.setData(freq_axis, magnitude_db)

        if self.max_hold_data is None or len(self.max_hold_data) != N:
            self.max_hold_data = magnitude_db.copy()
        else:
            self.max_hold_data = np.maximum(self.max_hold_data * 0.995, magnitude_db)
        self.max_hold_curve.setData(freq_axis, self.max_hold_data)

        if self.waterfall_data.shape[0] != N:
            half_bw_mhz = (self.sample_rate / 2.0) / 1e6
            self.waterfall_data = np.full((N, self.history_depth), -115.0, dtype=np.float32)
            self.waterfall_img.setRect(QRectF(-half_bw_mhz, 0, 2.0 * half_bw_mhz, self.history_depth))

        self.waterfall_data = np.roll(self.waterfall_data, 1, axis=1)
        self.waterfall_data[:, 0] = magnitude_db.astype(np.float32)
        self.waterfall_img.setImage(self.waterfall_data, autoLevels=False, levels=[-110.0, -25.0])

        self.card_peak_freq.setText(f"{peak_freq_khz:+.1f} kHz")
        self.card_peak_pwr.setText(f"{peak_pwr:.1f} dB")
        self.card_noise_floor.setText(f"{noise_floor_est:.1f} dB")

        now = time.time()
        dt = now - self.last_fps_time
        if dt >= 1.0:
            fps = self.fps_counter / dt
            self.card_fps_val.setText(f"{fps:.1f} FPS")
            self.fps_counter = 0
            self.last_fps_time = now

        badge_text = f"[ AKIŞ: CANLI ({N} I/Q) ]"
        if self.is_playing:
            badge_text = f"[ AKIŞ: OYNATMA ({N} I/Q) ]"
        self.lbl_dsp_badge.setText(badge_text)
        self.lbl_dsp_badge.setStyleSheet("color: #00ff66; font-weight: bold; font-size: 11px;")

    def on_record_stats_update(self, samples: int, frames: int, size_mb: float):
        if self.is_recording:
            self.lbl_record_status.setText(f"● KAYIT: {size_mb:.2f} MB ({frames} Kare)")
            self.lbl_record_status.setStyleSheet("color: #ff7b72; font-weight: bold; font-size: 11px;")

    def toggle_recording(self):
        if not self.is_running and not self.is_recording:
            self.log_message("UYARI", "Kayıt yapabilmek için önce 'Sistemi Başlat' ile veri akışını açınız.")
            return

        self.is_recording = not self.is_recording
        if self.is_recording:
            self.btn_record.setText("Kaydı Durdur")
            self.btn_record.setObjectName("btn_record_stop")
            self.btn_record.setStyleSheet(
                "background-color: #7a2530; color: #ffffff; border: 1px solid #ff7b72;"
            )
            self.lbl_record_status.setText("● KAYIT: BAŞLATILIYOR...")
            self.lbl_record_status.setStyleSheet("color: #ff7b72; font-weight: bold; font-size: 11px;")
            self.dsp_worker.start_recording()
        else:
            self.btn_record.setText("Kaydı Başlat")
            self.btn_record.setObjectName("btn_record_start")
            self.btn_record.setStyleSheet("")
            stats = self.dsp_worker.stop_recording()
            if stats:
                self.lbl_record_status.setText(f"● KAYIT: TAMAMLANDI ({stats['total_bytes']/1024/1024:.2f} MB)")
                self.lbl_record_status.setStyleSheet("color: #00ff66; font-size: 11px;")
            else:
                self.lbl_record_status.setText("● KAYIT: PASİF")
                self.lbl_record_status.setStyleSheet("color: #8b949e; font-size: 11px;")

    def browse_iq_file(self):
        records_dir = os.path.abspath("records")
        if not os.path.exists(records_dir):
            os.makedirs(records_dir, exist_ok=True)

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Oynatılacak I/Q Sinyal Dosyasını Seçin",
            records_dir,
            "I/Q Veri Dosyaları (*.raw *.dat *.bin *.iq);;Tüm Dosyalar (*.*)",
        )
        if filepath:
            self.selected_playback_filepath = filepath
            filename = os.path.basename(filepath)
            self.lbl_selected_file.setText(f"Dosya: {filename}")
            self.lbl_selected_file.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 11px;")
            self.log_message("OYNATMA", f"Oynatma dosyası seçildi: {filename}")

    def toggle_playback(self):
        if not self.selected_playback_filepath:
            self.log_message("UYARI", "Lütfen önce 'Dosya Seç' butonunu kullanarak bir I/Q dosyası seçin.")
            return

        if not self.is_playing:
            loop_enabled = self.chk_loop.isChecked()
            self.playback_thread = IQPlaybackThread(
                filepath=self.selected_playback_filepath,
                address="tcp://127.0.0.1:5555",
                chunk_size=1024,
                target_fps=20.0,
                loop=loop_enabled,
            )
            self.playback_thread.playback_progress.connect(self.on_playback_progress)
            self.playback_thread.playback_finished.connect(self.on_playback_finished)
            self.playback_thread.log_signal.connect(self.log_message)

            self.is_playing = True
            self.btn_play.setText("Oynatmayı Durdur")
            self.btn_play.setStyleSheet(
                "background-color: #6e1a24; color: #ff7b72; border: 1px solid #ff7b72;"
            )
            self.lbl_playback_status.setText("● OYNATMA: BAŞLATILIYOR...")
            self.lbl_playback_status.setStyleSheet("color: #38d39f; font-weight: bold; font-size: 11px;")

            if not self.is_running:
                self.toggle_system()

            self.playback_thread.start()
        else:
            if self.playback_thread:
                self.playback_thread.stop()
            self.on_playback_finished()

    def on_playback_progress(self, frame_idx: int, total_frames: int, progress_pct: float):
        self.lbl_playback_status.setText(f"● OYNATILIYOR: %{progress_pct:.0f} ({frame_idx}/{total_frames})")
        self.lbl_playback_status.setStyleSheet("color: #38d39f; font-weight: bold; font-size: 11px;")

    def on_playback_finished(self):
        self.is_playing = False
        self.btn_play.setText("Oynatmayı Başlat")
        self.btn_play.setStyleSheet("")
        self.lbl_playback_status.setText("● OYNATMA: PASİF")
        self.lbl_playback_status.setStyleSheet("color: #8b949e; font-size: 11px;")

    def calculate_rf_coverage(self):
        freq_mhz = self.spin_freq.value()
        tx_power_dbm = self.spin_tx_power.value()
        tx_gain_dbi = self.spin_tx_gain.value()
        rx_gain_dbi = self.spin_rx_gain.value()
        target_dist_km = self.spin_distance.value()

        results = compute_link_budget(
            frequency_mhz=freq_mhz,
            tx_power_dbm=tx_power_dbm,
            tx_gain_dbi=tx_gain_dbi,
            rx_gain_dbi=rx_gain_dbi,
            target_distance_km=target_dist_km,
        )

        distances = results["distances"]
        rx_powers = results["rx_powers"]
        target_fspl = results["target_fspl"]
        target_rx = results["target_rx_power"]
        eirp = results["eirp_dbm"]
        quality_text = results["quality_text"]
        quality_color = results["quality_color"]

        self.card_fspl_val.setText(f"{target_fspl:.2f} dB")
        self.card_prx_val.setText(f"{target_rx:.2f} dBm")
        self.card_eirp_val.setText(f"{eirp:.2f} dBm")
        self.card_status_val.setText(quality_text)
        self.card_status_val.setStyleSheet(
            f"color: {quality_color}; font-size: 15px; font-weight: bold; font-family: Consolas;"
        )

        self.curve_rx.setData(distances, rx_powers)
        self.point_target.setData([target_dist_km], [target_rx])

        threshold_y = np.full_like(distances, -100.0)
        self.line_threshold.setData(distances, threshold_y)

        self.status_msg.setText(
            f"Link Bütçesi Hesaplandı (f={freq_mhz:.1f} MHz, d={target_dist_km:.2f} km, Prx={target_rx:.2f} dBm)"
        )
        self.freq_badge.setText(f"Frekans: {freq_mhz:.2f} MHz")

        self.log_message(
            "RF ANALİZ",
            f"Link Bütçesi: f={freq_mhz:.1f}MHz | d={target_dist_km:.2f}km | FSPL={target_fspl:.2f}dB | Prx={target_rx:.2f}dBm | Kalite={quality_text}"
        )

    def perform_zmq_ping_test(self):
        self.log_message("BİLGİ", "ZeroMQ bağlantı testi başlatılıyor (tcp://127.0.0.1:5555)...")
        success, detail = execute_ping_test(
            address="tcp://127.0.0.1:5555",
        )
        if success:
            self.status_msg.setText("ZMQ Testi Başarılı: PING -> Alındı (tcp://127.0.0.1:5555)")
            self.status_msg.setStyleSheet("color: #00ff66; font-weight: bold;")
            self.log_message("BAŞARILI", f"ZMQ Bağlantı Testi Başarılı: {detail}")
        else:
            self.status_msg.setText(f"ZMQ Test Hatası: {detail}")
            self.status_msg.setStyleSheet("color: #ff4d4f; font-weight: bold;")
            self.log_message("HATA", f"ZMQ Bağlantı Testi Başarısız: {detail}")

    def setup_status_bar(self):
        status_bar = self.statusBar()

        self.status_msg = QLabel("Hazır")
        self.status_msg.setStyleSheet("color: #00ff66; font-weight: bold;")

        self.freq_badge = QLabel(f"Frekans: {self.center_freq_mhz:.2f} MHz")
        self.freq_badge.setStyleSheet("color: #8b949e;")

        self.clock_label = QLabel(QTime.currentTime().toString("HH:mm:ss"))
        self.clock_label.setStyleSheet("color: #58a6ff; font-family: Consolas;")

        status_bar.addWidget(QLabel("DURUM: "))
        status_bar.addWidget(self.status_msg)
        status_bar.addPermanentWidget(self.freq_badge)
        status_bar.addPermanentWidget(self.clock_label)

    def update_clock(self):
        self.clock_label.setText(QTime.currentTime().toString("HH:mm:ss"))

    def toggle_system(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_start.setText("Sistemi Durdur")
            self.btn_start.setStyleSheet(
                """
                QPushButton#btn_primary {
                    background-color: #6e1a24;
                    color: #ff7b72;
                    border: 1px solid #ff7b72;
                }
                QPushButton#btn_primary:hover {
                    background-color: #8b2330;
                    color: #ffffff;
                }
                """
            )
            self.lbl_system_status.setText("● DURUM: ÇALIŞIYOR")
            self.lbl_system_status.setStyleSheet(
                "color: #00ff66; font-weight: bold; font-size: 11px; padding: 2px;"
            )
            self.status_msg.setText("Sistem Aktif - QThread DSP Spektrum, Şelale & Demodülasyon Başlatıldı")
            self.status_msg.setStyleSheet("color: #00ff66; font-weight: bold;")
            
            self.dsp_worker.start()
            self.log_message("DURUM", "Veri Akışı Aktif - Çoklu iş parçacıklı (QThread) DSP motoru başlatıldı.")
        else:
            self.btn_start.setText("Sistemi Başlat")
            self.btn_start.setStyleSheet("")
            self.lbl_system_status.setText("● DURUM: BEKLEMEDE")
            self.lbl_system_status.setStyleSheet(
                "color: #ffaa00; font-weight: bold; font-size: 11px; padding: 2px;"
            )
            self.status_msg.setText("Sistem Durduruldu - Beklemede")
            self.status_msg.setStyleSheet("color: #ffaa00; font-weight: bold;")
            
            if self.is_recording:
                self.toggle_recording()

            if self.is_playing:
                self.toggle_playback()

            if self.audio_output_enabled:
                self.toggle_audio_output()

            self.dsp_worker.stop()
            self.lbl_dsp_badge.setText("[ AKIŞ: DURDURULDU ]")
            self.lbl_dsp_badge.setStyleSheet("color: #ffaa00; font-weight: bold; font-size: 11px;")
            self.log_message("DURUM", "Veri Akışı Durduruldu - DSP motoru beklemede.")

    def closeEvent(self, event):
        self.log_message("SYSTEM", "Terminal kapatılıyor. Kayıtlar ve soketler temizleniyor...")
        if hasattr(self, "dsp_worker") and self.dsp_worker.isRunning():
            self.dsp_worker.stop()
        if self.playback_thread and self.playback_thread.isRunning():
            self.playback_thread.stop()
        if self.audio_output_enabled:
            self.audio_engine.stop_audio()
        if self.zmq_pub:
            self.zmq_pub.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(TACTICAL_STYLESHEET)

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(13, 17, 23))
    dark_palette.setColor(QPalette.WindowText, QColor(201, 209, 217))
    dark_palette.setColor(QPalette.Base, QColor(22, 27, 34))
    dark_palette.setColor(QPalette.AlternateBase, QColor(13, 17, 23))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(22, 27, 34))
    dark_palette.setColor(QPalette.ToolTipText, QColor(201, 209, 217))
    dark_palette.setColor(QPalette.Text, QColor(201, 209, 217))
    dark_palette.setColor(QPalette.Button, QColor(33, 38, 45))
    dark_palette.setColor(QPalette.ButtonText, QColor(240, 246, 252))
    dark_palette.setColor(QPalette.BrightText, QColor(0, 255, 102))
    dark_palette.setColor(QPalette.Link, QColor(88, 166, 255))
    dark_palette.setColor(QPalette.Highlight, QColor(0, 255, 102))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)

    window = TacticalMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
