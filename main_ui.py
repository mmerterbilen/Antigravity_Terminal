#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Ana Kullanıcı Arayüzü (Main UI)
Çoklu İş Parçacıklı (QThread) FFT Spektrum & Şelale Göstergesi, RF Link Bütçesi Hesaplayıcı,
I/Q Sinyal Kayıt ve Oynatma (Recording & Playback) Modülü, ZeroMQ ve Taktik Konsol.
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
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
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
    padding: 10px 20px;
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

/* --- Taktik Log Konsolu (QTextEdit) --- */
QTextEdit#console_log {
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

/* --- Girdi Kutuları (QDoubleSpinBox) --- */
QDoubleSpinBox {
    background-color: #0d1117;
    color: #00ff66;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 6px 10px;
    font-family: "Consolas", monospace;
    font-size: 13px;
    font-weight: bold;
    min-height: 22px;
}

QDoubleSpinBox:focus {
    border: 1px solid #00ff66;
    background-color: #111822;
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #21262d;
    border: 1px solid #30363d;
    width: 18px;
}

QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #30363d;
}

/* --- Buton Stili (Taktik Vurgular) --- */
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

QPushButton#btn_record_start {
    background-color: #5c1d24;
    color: #ff7b72;
    border: 1px solid #ff7b72;
    font-size: 12px;
    padding: 7px 10px;
}

QPushButton#btn_record_start:hover {
    background-color: #7a2530;
    color: #ffffff;
}

QPushButton#btn_record_stop {
    background-color: #21262d;
    color: #ff7b72;
    border: 1px solid #ff7b72;
    font-size: 12px;
    padding: 7px 10px;
}

QPushButton#btn_play_start {
    background-color: #1b382b;
    color: #38d39f;
    border: 1px solid #38d39f;
    font-size: 12px;
    padding: 7px 10px;
}

QPushButton#btn_play_start:hover {
    background-color: #25533f;
    color: #ffffff;
}

QPushButton#btn_ping {
    background-color: #1b2838;
    color: #58a6ff;
    border: 1px solid #58a6ff;
    font-size: 12px;
    padding: 6px 12px;
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
    Arka planda ZMQ I/Q verisi alan, FFT hesaplayan ve canlı I/Q kaydını
    dosyaya yazan çoklu iş parçacığı (QThread).
    """

    # Sinyal: (Frekans Ekseni, Genlik dB, Tepe Frekansı kHz, Tepe Gücü dB, Taban Gürültüsü dB, Örnek Sayısı)
    spectrum_ready = pyqtSignal(np.ndarray, np.ndarray, float, float, float, int)
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

    def run(self):
        """İş parçacığı ana döngüsü."""
        self._running = True
        ctx = zmq.Context()
        sub = ZMQSubscriber(address=self.address, topics=["IQ", ""], context=ctx)

        poller = zmq.Poller()
        if sub.socket:
            poller.register(sub.socket, zmq.POLLIN)

        self.log_signal.emit("BİLGİ", "Arka plan DSP iş parçacığı (QThread) aktif edildi.")

        try:
            while self._running:
                # 20 ms zaman aşımı ile soketi yokla
                socks = dict(poller.poll(20))
                if sub.socket and sub.socket in socks and socks[sub.socket] == zmq.POLLIN:
                    # En son pakete kadar tamponu oku
                    latest_iq = None
                    while True:
                        result = sub.receive_iq_data(flags=zmq.NOBLOCK)
                        if result is None:
                            break
                        _, iq_data = result
                        if len(iq_data) > 0:
                            latest_iq = iq_data
                            # Canlı kayıt aktifse diske yaz
                            if self.recorder.is_recording:
                                self.recorder.write_iq_data(iq_data)

                    if latest_iq is not None and self._running:
                        N = len(latest_iq)

                        # Hanning Penceresi
                        if N not in self.window_cache:
                            self.window_cache[N] = np.hanning(N)
                        window = self.window_cache[N]

                        # FFT Hesaplama ve Merkezleme (Shift)
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

                        # Kayıt istatistikleri sinyali
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

    def start_recording(self, filepath: Optional[str] = None):
        """Kayıt işlemini başlatır."""
        path = self.recorder.start_recording(
            filepath=filepath,
            sample_rate=self.sample_rate,
            center_freq_mhz=self.center_freq_mhz,
        )
        if path:
            self.log_signal.emit("KAYIT", f"Sinyal dosyası kaydediliyor: {os.path.basename(path)}")

    def stop_recording(self) -> Optional[dict]:
        """Kayıt işlemini durdurur."""
        stats = self.recorder.stop_recording()
        if stats:
            self.log_signal.emit(
                "KAYIT",
                f"Kayıt tamamlandı: {os.path.basename(stats['file_path'])} "
                f"({stats['total_samples']} örnek, {stats['total_bytes']/1024/1024:.2f} MB)",
            )
        return stats

    def stop(self):
        """İş parçacığını güvenle durdurur."""
        self._running = False
        self.wait(1500)


class TacticalMainWindow(QMainWindow):
    """Antigravity Taktik SDR Terminali Ana Pencere Sınıfı."""

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.is_recording = False
        self.is_playing = False

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

        # Oynatma İş Parçacığı
        self.playback_thread: Optional[IQPlaybackThread] = None
        self.selected_playback_filepath = ""

        # ZeroMQ PUB (Ping Testi için)
        self.zmq_pub = None
        self.init_zmq()

        # Arayüzü Kur
        self.init_ui()

        # Optimize Edilmiş Çoklu İş Parçacığı (QThread) Motoru
        self.dsp_worker = DSPWorkerThread(address="tcp://127.0.0.1:5555", sample_rate=self.sample_rate)
        self.dsp_worker.center_freq_mhz = self.center_freq_mhz
        self.dsp_worker.spectrum_ready.connect(self.on_spectrum_data_ready)
        self.dsp_worker.record_stats_signal.connect(self.on_record_stats_update)
        self.dsp_worker.log_signal.connect(self.log_message)

        # Başlangıç Loglarını Konsola İlet
        self.log_message("SYSTEM", "Antigravity Taktik SDR Terminali başlatıldı (Faz 11 - Kayıt/Oynatma Aktif).")
        self.log_message("INFO", "Taktik GUI teması ve I/Q kayıt/oynatma motoru hazır.")

        # İlk link bütçesi hesaplamasını otomatik tetikle
        self.calculate_rf_coverage()

    def init_zmq(self):
        """ZeroMQ PUB bileşenini ilklendirir."""
        try:
            self.zmq_pub = ZMQPublisher(address="tcp://127.0.0.1:5555", bind_mode=False)
        except Exception as e:
            print(f"[ZMQ HATA] {e}")

    def init_ui(self):
        # 1. Ana Pencere Temel Ayarları
        self.setWindowTitle("Antigravity Taktik SDR Terminali")
        self.resize(1420, 920)
        self.setMinimumSize(1100, 720)

        # 2. Merkezi Widget ve Ana Düzen
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 3. Yatay Bölücü (Splitter): Sol Kontrol Paneli | Sağ Çalışma Alanı
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        main_layout.addWidget(main_splitter)

        # 4. Sol Kenar Çubuğu (Kontrol Paneli)
        sidebar_widget = self.create_sidebar()
        main_splitter.addWidget(sidebar_widget)

        # 5. Sağ Alan: Dikey Bölücü (Üstte Sekmeler, Altta Sistem Logları Konsolu)
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)

        # Yatay Bölücü Başlangıç Oranları (%23 Kontrol, %77 Çalışma Alanı)
        main_splitter.setSizes([320, 1100])

        # 6. Alt Durum Çubuğu (Status Bar)
        self.setup_status_bar()

        # 7. Saat / Zamanlayıcı
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

    def create_sidebar(self) -> QWidget:
        """Sol kontrol paneli bileşenlerini oluşturur."""
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

        # Başlık ve Rozet
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

        # Ayırıcı Çizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #30363d; max-height: 1px;")
        layout.addWidget(line)

        # 1. Sistem Kontrol Grubu
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

        # 2. I/Q Sinyal Kayıt ve Oynatma Grubu (Faz 11)
        record_group = QGroupBox("I/Q SİNYAL KAYDI VE OYNATMA")
        rec_layout = QVBoxLayout(record_group)
        rec_layout.setSpacing(8)

        # Kayıt Alt Bölümü
        lbl_rec_sub = QLabel("HAM I/Q KAYIT MOTORU")
        lbl_rec_sub.setStyleSheet("font-size: 10px; color: #ff7b72; font-weight: bold;")
        rec_layout.addWidget(lbl_rec_sub)

        rec_btn_layout = QHBoxLayout()
        self.btn_record = QPushButton("Kaydı Başlat")
        self.btn_record.setObjectName("btn_record_start")
        self.btn_record.setToolTip("Canlı I/Q veri akışını diske (.raw ve SigMF meta) kaydeder")
        self.btn_record.setCursor(Qt.PointingHandCursor)
        self.btn_record.clicked.connect(self.toggle_recording)
        rec_btn_layout.addWidget(self.btn_record)
        rec_layout.addLayout(rec_btn_layout)

        self.lbl_record_status = QLabel("● KAYIT: PASİF")
        self.lbl_record_status.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.lbl_record_status.setAlignment(Qt.AlignCenter)
        rec_layout.addWidget(self.lbl_record_status)

        # Ayırıcı
        rec_line = QFrame()
        rec_line.setFrameShape(QFrame.HLine)
        rec_line.setStyleSheet("background-color: #21262d; max-height: 1px;")
        rec_layout.addWidget(rec_line)

        # Oynatma (Playback) Alt Bölümü
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
        self.lbl_selected_file.setToolTip("Oynatılacak kayıt dosyası")
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

        # 4. Aktif Modüller Bilgisi
        module_group = QGroupBox("AKTİF MODÜLLER")
        mod_layout = QVBoxLayout(module_group)
        mod_layout.setSpacing(5)

        lbl_m1 = QLabel("✔ I/Q Kayıt & Oynatma (Aktif)")
        lbl_m1.setStyleSheet("color: #00ff66; font-size: 11px;")
        lbl_m2 = QLabel("✔ QThread Çoklu İş Parçacığı")
        lbl_m2.setStyleSheet("color: #00ff66; font-size: 11px;")
        lbl_m3 = QLabel("✔ Spektrum Analizörü & Şelale")
        lbl_m3.setStyleSheet("color: #00ff66; font-size: 11px;")
        lbl_m4 = QLabel("✔ RF Link Bütçesi Hesaplayıcı")
        lbl_m4.setStyleSheet("color: #00ff66; font-size: 11px;")

        mod_layout.addWidget(lbl_m1)
        mod_layout.addWidget(lbl_m2)
        mod_layout.addWidget(lbl_m3)
        mod_layout.addWidget(lbl_m4)

        layout.addWidget(module_group)

        # Alt Boşluk Doldurucu
        layout.addStretch()

        # Marka Altlığı
        lbl_footer = QLabel("ANTIGRAVITY // TACTICAL SDR")
        lbl_footer.setStyleSheet("color: #484f58; font-size: 10px; letter-spacing: 2px;")
        lbl_footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_footer)

        scroll.setWidget(sidebar)
        return scroll

    def create_right_panel(self) -> QWidget:
        """Sağ çalışma alanını (Sekmeler + Sistem Logları Konsolu) oluşturur."""
        right_container = QWidget()
        layout = QVBoxLayout(right_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Dikey Bölücü: Üstte Sekmeler (%75), Altta Log Konsolu (%25)
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.setChildrenCollapsible(False)

        # 1. Merkezi Sekme Alanı
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        tab_spectrum_waterfall = self.create_spectrum_waterfall_tab()
        self.tab_widget.addTab(tab_spectrum_waterfall, "📡 Spektrum & Şelale")

        tab_rf_coverage = self.create_rf_coverage_tab()
        self.tab_widget.addTab(tab_rf_coverage, "📊 RF Kapsama Alanı")

        self.right_splitter.addWidget(self.tab_widget)

        # 2. Sistem Logları Konsol Paneli
        console_panel = self.create_console_panel()
        self.right_splitter.addWidget(console_panel)

        # Başlangıç Dikey Boyutları (700px Üst, 180px Log Konsolu)
        self.right_splitter.setSizes([700, 180])

        layout.addWidget(self.right_splitter)
        return right_container

    def create_console_panel(self) -> QWidget:
        """Sistem Logları Konsol Widget'ını oluşturur."""
        container = QFrame()
        container.setStyleSheet("background-color: #161b22; border-top: 1px solid #30363d;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(6)

        # Konsol Başlık Çubuğu
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

        # Log Metin Alanı (QTextEdit, Read-Only)
        self.txt_console = QTextEdit()
        self.txt_console.setObjectName("console_log")
        self.txt_console.setReadOnly(True)
        self.txt_console.setAcceptRichText(True)
        layout.addWidget(self.txt_console)

        return container

    def log_message(self, level: str, message: str):
        """
        Taktik konsola zaman damgalı ve renk kodlu Türkçe log iletisi ekler.
        """
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
        """Konsol ekranını temizler."""
        self.txt_console.clear()
        self.log_message("SYSTEM", "Konsol günlüğü temizlendi.")

    def create_spectrum_waterfall_tab(self) -> QWidget:
        """Gerçek Zamanlı FFT Spektrum Analizörü ve Şelale Ekranını oluşturur."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 1. Başlık ve Telemetri Çubuğu
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

        # 2. Spektrum Telemetri HUD Kartları
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

        # 3. Dikey Bölücü (Splitter): Üstte Spektrum Analizörü, Altta Şelale Ekranı
        display_splitter = QSplitter(Qt.Vertical)
        display_splitter.setChildrenCollapsible(False)

        # 3A. PyQtGraph Spektrum Analizör Grafiği (Üst Panel)
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

        # 3B. PyQtGraph Şelale (Waterfall / Spektrogram) Grafiği (Alt Panel)
        self.waterfall_plot = pg.PlotWidget()
        self.waterfall_plot.setBackground("#090d13")
        self.waterfall_plot.setLabel("left", "Zaman", color="#c9d1d9")
        self.waterfall_plot.setLabel("bottom", "Frekans", units="MHz", color="#c9d1d9")
        self.waterfall_plot.setTitle(
            '<span style="color: #00ff66; font-size: 12px; font-weight: bold;">'
            "Şelale Ekranı (Zaman Geçmişi)</span>"
        )

        # Frekans eksenlerini senkronize bağla (X-Link)
        self.waterfall_plot.setXLink(self.spectrum_plot)

        # 2D Waterfall Görüntü Öğesi (ImageItem)
        self.waterfall_img = pg.ImageItem()
        self.waterfall_plot.addItem(self.waterfall_img)

        # Taktik Renk Haritasını (LUT) Uygula
        tactical_cmap = create_tactical_colormap()
        lut = tactical_cmap.getLookupTable(0.0, 1.0, 256)
        self.waterfall_img.setLookupTable(lut)

        # Başlangıç Boyutlandırma ve Sınırları
        half_bw_mhz = (self.sample_rate / 2.0) / 1e6
        self.waterfall_img.setRect(QRectF(-half_bw_mhz, 0, 2.0 * half_bw_mhz, self.history_depth))
        self.waterfall_img.setImage(self.waterfall_data, autoLevels=False, levels=[-110.0, -25.0])

        display_splitter.addWidget(self.waterfall_plot)

        # Dikey Bölücü Oranları (%50 Spektrum, %50 Şelale)
        display_splitter.setSizes([320, 320])

        layout.addWidget(display_splitter, stretch=1)

        return container

    def create_rf_coverage_tab(self) -> QWidget:
        """RF Link Bütçesi ve Kapsama Alanı Hesaplayıcı Sekmesini oluşturur."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Başlık ve Bilgi Çubuğu
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

        # 2. Parametre Giriş Paneli (Taktik Koyu Grup)
        input_group = QGroupBox("RF İLETİM VE ALICI PARAMETRELERİ")
        grid = QGridLayout(input_group)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(12)

        # Frekans (MHz)
        lbl_freq = QLabel("Frekans (MHz):")
        self.spin_freq = QDoubleSpinBox()
        self.spin_freq.setRange(1.0, 60000.0)
        self.spin_freq.setValue(433.0)
        self.spin_freq.setDecimals(2)
        self.spin_freq.setSingleStep(10.0)
        self.spin_freq.setToolTip("Taşıyıcı sinyalin merkez frekansı (MHz cinsinden)")

        # İletim Gücü (dBm)
        lbl_tx_power = QLabel("İletim Gücü (dBm):")
        self.spin_tx_power = QDoubleSpinBox()
        self.spin_tx_power.setRange(-30.0, 100.0)
        self.spin_tx_power.setValue(20.0)
        self.spin_tx_power.setDecimals(1)
        self.spin_tx_power.setSingleStep(1.0)
        self.spin_tx_power.setToolTip("Verici çıkış gücü (dBm cinsinden)")

        # Tx Kazancı (dBi)
        lbl_tx_gain = QLabel("Tx Kazancı (dBi):")
        self.spin_tx_gain = QDoubleSpinBox()
        self.spin_tx_gain.setRange(-20.0, 60.0)
        self.spin_tx_gain.setValue(2.15)
        self.spin_tx_gain.setDecimals(2)
        self.spin_tx_gain.setSingleStep(0.5)
        self.spin_tx_gain.setToolTip("Verici anten kazancı (dBi cinsinden)")

        # Rx Kazancı (dBi)
        lbl_rx_gain = QLabel("Rx Kazancı (dBi):")
        self.spin_rx_gain = QDoubleSpinBox()
        self.spin_rx_gain.setRange(-20.0, 60.0)
        self.spin_rx_gain.setValue(2.15)
        self.spin_rx_gain.setDecimals(2)
        self.spin_rx_gain.setSingleStep(0.5)
        self.spin_rx_gain.setToolTip("Alıcı anten kazancı (dBi cinsinden)")

        # Hedef Mesafe (km)
        lbl_distance = QLabel("Hedef Mesafe (km):")
        self.spin_distance = QDoubleSpinBox()
        self.spin_distance.setRange(0.01, 1000.0)
        self.spin_distance.setValue(10.0)
        self.spin_distance.setDecimals(2)
        self.spin_distance.setSingleStep(1.0)
        self.spin_distance.setToolTip("Analiz edilecek hedef mesafe (km cinsinden)")

        # "Hesapla" Butonu
        self.btn_calc = QPushButton("Hesapla")
        self.btn_calc.setObjectName("btn_calculate")
        self.btn_calc.setToolTip("Friis denklemini kullanarak RF link bütçesini ve menzil eğrisini hesaplar")
        self.btn_calc.setCursor(Qt.PointingHandCursor)
        self.btn_calc.clicked.connect(self.calculate_rf_coverage)

        # Izgaraya Yerleştirme
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

        # 3. Sonuç Özet Kartları (HUD Göstergeleri)
        hud_layout = QHBoxLayout()
        hud_layout.setSpacing(12)

        # Kart 1: FSPL
        self.card_fspl_val = QLabel("-- dB")
        card_fspl = self.create_hud_card("SERBEST UZAY KAYBI (FSPL)", self.card_fspl_val, "#f0f6fc")
        hud_layout.addWidget(card_fspl)

        # Kart 2: Alınan Güç (Prx)
        self.card_prx_val = QLabel("-- dBm")
        card_prx = self.create_hud_card("HEDEF ALINAN GÜÇ (Prx)", self.card_prx_val, "#00ff66")
        hud_layout.addWidget(card_prx)

        # Kart 3: EIRP
        self.card_eirp_val = QLabel("-- dBm")
        card_eirp = self.create_hud_card("EIRP (IŞIMA GÜCÜ)", self.card_eirp_val, "#58a6ff")
        hud_layout.addWidget(card_eirp)

        # Kart 4: Sinyal Durumu
        self.card_status_val = QLabel("HESAPLANIYOR")
        card_status = self.create_hud_card("BAĞLANTI KALİTESİ", self.card_status_val, "#00ff66")
        hud_layout.addWidget(card_status)

        layout.addLayout(hud_layout)

        # 4. PyQtGraph Alınan Güç - Mesafe Grafiği
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

        # Eğriler ve Çizgiler
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
        """HUD metrik kartı oluşturur."""
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
        """
        QThread tarafından hesaplanan FFT verilerini güvenle alır ve GUI grafiklerini günceller.
        """
        self.fft_size = N
        self.total_frames_received += 1
        self.fps_counter += 1

        # 1. Spektrum Çizgisini Güncelle
        self.spectrum_curve.setData(freq_axis, magnitude_db)

        # 2. Max-Hold Güncelle
        if self.max_hold_data is None or len(self.max_hold_data) != N:
            self.max_hold_data = magnitude_db.copy()
        else:
            self.max_hold_data = np.maximum(self.max_hold_data * 0.995, magnitude_db)
        self.max_hold_curve.setData(freq_axis, self.max_hold_data)

        # 3. Şelale (Waterfall) Güncelle
        if self.waterfall_data.shape[0] != N:
            half_bw_mhz = (self.sample_rate / 2.0) / 1e6
            self.waterfall_data = np.full((N, self.history_depth), -115.0, dtype=np.float32)
            self.waterfall_img.setRect(QRectF(-half_bw_mhz, 0, 2.0 * half_bw_mhz, self.history_depth))

        self.waterfall_data = np.roll(self.waterfall_data, 1, axis=1)
        self.waterfall_data[:, 0] = magnitude_db.astype(np.float32)
        self.waterfall_img.setImage(self.waterfall_data, autoLevels=False, levels=[-110.0, -25.0])

        # 4. HUD Telemetri Kartlarını Güncelle
        self.card_peak_freq.setText(f"{peak_freq_khz:+.1f} kHz")
        self.card_peak_pwr.setText(f"{peak_pwr:.1f} dB")
        self.card_noise_floor.setText(f"{noise_floor_est:.1f} dB")

        # 5. FPS Sayacı Güncellemesi
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
        """Kayıt istatistikleri arayüz etiketini günceller."""
        if self.is_recording:
            self.lbl_record_status.setText(f"● KAYIT: {size_mb:.2f} MB ({frames} Kare)")
            self.lbl_record_status.setStyleSheet("color: #ff7b72; font-weight: bold; font-size: 11px;")

    def toggle_recording(self):
        """Canlı I/Q kaydını başlatır veya durdurur."""
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
        """Oynatılacak kayıt dosyasını seçtirir."""
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
        """Kayıtlı I/Q dosyasının ZMQ üzerinden oynatılmasını yönetir."""
        if not self.selected_playback_filepath:
            self.log_message("UYARI", "Lütfen önce 'Dosya Seç' butonunu kullanarak bir I/Q dosyası seçin.")
            return

        if not self.is_playing:
            # Oynatmayı Başlat
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

            # Eğer terminal sistemi çalışmıyorsa otomatik başlat
            if not self.is_running:
                self.toggle_system()

            self.playback_thread.start()
        else:
            # Oynatmayı Durdur
            if self.playback_thread:
                self.playback_thread.stop()
            self.on_playback_finished()

    def on_playback_progress(self, frame_idx: int, total_frames: int, progress_pct: float):
        """Oynatma ilerleme durumunu günceller."""
        self.lbl_playback_status.setText(f"● OYNATILIYOR: %{progress_pct:.0f} ({frame_idx}/{total_frames})")
        self.lbl_playback_status.setStyleSheet("color: #38d39f; font-weight: bold; font-size: 11px;")

    def on_playback_finished(self):
        """Oynatma bittiğinde veya durdurulduğunda UI elemanlarını sıfırlar."""
        self.is_playing = False
        self.btn_play.setText("Oynatmayı Başlat")
        self.btn_play.setStyleSheet("")
        self.lbl_playback_status.setText("● OYNATMA: PASİF")
        self.lbl_playback_status.setStyleSheet("color: #8b949e; font-size: 11px;")

    def calculate_rf_coverage(self):
        """Kullanıcı girişlerine göre Friis Link Bütçesini hesaplar ve grafiği günceller."""
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
        """ZeroMQ PUB/SUB köprüsünü test eder ve sonucu konsola ile arayüze yansıtır."""
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
        """Alt taktik durum çubuğunu yapılandırır."""
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
        """Durum çubuğundaki saati günceller."""
        self.clock_label.setText(QTime.currentTime().toString("HH:mm:ss"))

    def toggle_system(self):
        """Sistemi başlat / durdur eylemini yönetir."""
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
            self.status_msg.setText("Sistem Aktif - QThread DSP Spektrum & Şelale Alımı Başlatıldı")
            self.status_msg.setStyleSheet("color: #00ff66; font-weight: bold;")
            
            self.dsp_worker.start()
            self.log_message("DURUM", "Veri Akışı Aktif - Çoklu iş parçacıklı (QThread) FFT & Şelale alımı başlatıldı.")
        else:
            self.btn_start.setText("Sistemi Başlat")
            self.btn_start.setStyleSheet("")
            self.lbl_system_status.setText("● DURUM: BEKLEMEDE")
            self.lbl_system_status.setStyleSheet(
                "color: #ffaa00; font-weight: bold; font-size: 11px; padding: 2px;"
            )
            self.status_msg.setText("Sistem Durduruldu - Beklemede")
            self.status_msg.setStyleSheet("color: #ffaa00; font-weight: bold;")
            
            # Kayıt açıksa durdur
            if self.is_recording:
                self.toggle_recording()

            # Oynatma açıksa durdur
            if self.is_playing:
                self.toggle_playback()

            self.dsp_worker.stop()
            self.lbl_dsp_badge.setText("[ AKIŞ: DURDURULDU ]")
            self.lbl_dsp_badge.setStyleSheet("color: #ffaa00; font-weight: bold; font-size: 11px;")
            self.log_message("DURUM", "Veri Akışı Durduruldu - DSP motoru beklemede.")

    def closeEvent(self, event):
        """Pencere kapatıldığında arka plan iş parçacıklarını ve ZeroMQ soketlerini temizler."""
        self.log_message("SYSTEM", "Terminal kapatılıyor. Kayıtlar ve soketler temizleniyor...")
        if hasattr(self, "dsp_worker") and self.dsp_worker.isRunning():
            self.dsp_worker.stop()
        if self.playback_thread and self.playback_thread.isRunning():
            self.playback_thread.stop()
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
