#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Ana Kullanıcı Arayüzü (Main UI)
Gerçek zamanlı FFT Spektrum Analizörü, RF Link Bütçesi ve ZeroMQ Middleware Entegrasyonu.
"""

import sys
import time
import numpy as np
import pyqtgraph as pg
import zmq
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
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
    QVBoxLayout,
    QWidget,
)

from rf_calculator import compute_link_budget
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
    margin-top: 22px;
    padding: 14px 10px 10px 10px;
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

/* --- Buton Stili (Taktik Yeşil Vurgu) --- */
QPushButton {
    background-color: #21262d;
    color: #f0f6fc;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
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
    padding: 9px 16px;
}

QPushButton#btn_primary:hover {
    background-color: #22683e;
    color: #ffffff;
    border: 1px solid #39ff14;
}

QPushButton#btn_ping {
    background-color: #1b2838;
    color: #58a6ff;
    border: 1px solid #58a6ff;
    font-size: 12px;
    padding: 7px 12px;
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

/* --- Çerçeve ve Bölücüler --- */
QFrame#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

QFrame#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px;
}

QSplitter::handle {
    background-color: #30363d;
    width: 2px;
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


class TacticalMainWindow(QMainWindow):
    """Antigravity Taktik SDR Terminali Ana Pencere Sınıfı."""

    def __init__(self):
        super().__init__()
        self.is_running = False

        # DSP & FFT Akış Değişkenleri
        self.sample_rate = 2.048e6  # 2.048 MHz örnekleme
        self.center_freq_mhz = 433.0
        self.fft_size = 1024
        self.total_frames_received = 0
        self.last_fps_time = time.time()
        self.fps_counter = 0

        # ZeroMQ Middleware Başlatma
        self.zmq_pub = None
        self.zmq_sub = None
        self.init_zmq()

        # Arayüzü Kur
        self.init_ui()

        # FFT Veri Alım Zamanlayıcısı (30 ms ~ 33 FPS polling)
        self.dsp_timer = QTimer(self)
        self.dsp_timer.timeout.connect(self.process_incoming_dsp_data)

    def init_zmq(self):
        """ZeroMQ PUB/SUB bileşenlerini ilklendirir."""
        try:
            self.zmq_pub = ZMQPublisher(address="tcp://127.0.0.1:5555", bind_mode=False)
            self.zmq_sub = ZMQSubscriber(address="tcp://127.0.0.1:5555", topics=["IQ", ""])
            print("[ZMQ INIT] ZeroMQ PUB/SUB köprüsü (tcp://127.0.0.1:5555) hazırlandı.")
        except Exception as e:
            print(f"[ZMQ HATA] ZeroMQ ilklendirme hatası: {e}")

    def init_ui(self):
        # 1. Ana Pencere Temel Ayarları
        self.setWindowTitle("Antigravity Taktik SDR Terminali")
        self.resize(1360, 860)
        self.setMinimumSize(1040, 660)

        # 2. Merkezi Widget ve Ana Düzen
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 3. Bölücü (Splitter) ile Esnek Düzen
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter)

        # 4. Sol Kenar Çubuğu (Kontrol Paneli)
        sidebar_widget = self.create_sidebar()
        splitter.addWidget(sidebar_widget)

        # 5. Merkezi Sekme Alanı (Göstergeler ve Hesaplayıcılar)
        central_tabs = self.create_central_tabs()
        splitter.addWidget(central_tabs)

        # Bölücü Başlangıç Oranları (%22 Kontrol, %78 Çalışma Alanı)
        splitter.setSizes([290, 1070])

        # 6. Alt Durum Çubuğu (Status Bar)
        self.setup_status_bar()

        # 7. Saat / Zamanlayıcı
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        # İlk link bütçesi hesaplamasını otomatik tetikle
        self.calculate_rf_coverage()

    def create_sidebar(self) -> QWidget:
        """Sol kontrol paneli bileşenlerini oluşturur."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(270)
        sidebar.setMaximumWidth(360)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

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

        # Sistem Başlatma / Durdurma & ZMQ Test Grubu
        sys_group = QGroupBox("SİSTEM KONTROLÜ")
        sys_layout = QVBoxLayout(sys_group)
        sys_layout.setSpacing(10)

        # "Sistemi Başlat" Butonu
        self.btn_start = QPushButton("Sistemi Başlat")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setToolTip("Terminali başlatır")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.toggle_system)
        sys_layout.addWidget(self.btn_start)

        # "Bağlantı Testi" Butonu (ZMQ Ping Test)
        self.btn_ping = QPushButton("Bağlantı Testi")
        self.btn_ping.setObjectName("btn_ping")
        self.btn_ping.setToolTip("ZeroMQ PUB/SUB köprüsünü PING mesajı ile test eder")
        self.btn_ping.setCursor(Qt.PointingHandCursor)
        self.btn_ping.clicked.connect(self.perform_zmq_ping_test)
        sys_layout.addWidget(self.btn_ping)

        # Sistem Durum Göstergesi
        self.lbl_system_status = QLabel("● DURUM: BEKLEMEDE")
        self.lbl_system_status.setStyleSheet(
            "color: #ffaa00; font-weight: bold; font-size: 11px; padding: 4px;"
        )
        self.lbl_system_status.setAlignment(Qt.AlignCenter)
        sys_layout.addWidget(self.lbl_system_status)

        layout.addWidget(sys_group)

        # RF Donanım Parametreleri
        rf_group = QGroupBox("RF DONANIM PARAMETRELERİ")
        rf_layout = QVBoxLayout(rf_group)
        rf_layout.setSpacing(8)

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

        # Modül Bilgi Kartı
        module_group = QGroupBox("AKTİF MODÜLLER")
        mod_layout = QVBoxLayout(module_group)
        mod_layout.setSpacing(6)

        lbl_m1 = QLabel("✔ Gerçek Zamanlı Spektrum (Aktif)")
        lbl_m1.setStyleSheet("color: #00ff66; font-size: 11px;")
        lbl_m2 = QLabel("✔ RF Link Bütçesi Hesaplayıcı")
        lbl_m2.setStyleSheet("color: #00ff66; font-size: 11px;")
        lbl_m3 = QLabel("✔ ZeroMQ I/Q Veri Akışı (5555)")
        lbl_m3.setStyleSheet("color: #58a6ff; font-size: 11px;")

        mod_layout.addWidget(lbl_m1)
        mod_layout.addWidget(lbl_m2)
        mod_layout.addWidget(lbl_m3)

        layout.addWidget(module_group)

        # Alt Boşluk Doldurucu
        layout.addStretch()

        # Alt Marka Bilgisi
        lbl_footer = QLabel("ANTIGRAVITY // TACTICAL SDR")
        lbl_footer.setStyleSheet("color: #484f58; font-size: 10px; letter-spacing: 2px;")
        lbl_footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_footer)

        return sidebar

    def create_central_tabs(self) -> QWidget:
        """Merkezi sekme yapısını ve içeriğini oluşturur."""
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # 1. Sekme: Gerçek Zamanlı Spektrum Analizörü (Phase 6)
        tab_spectrum = self.create_spectrum_tab()
        self.tab_widget.addTab(tab_spectrum, "📡 Spektrum Analizörü")

        # 2. Sekme: RF Kapsama Alanı (Link Budget)
        tab_rf_coverage = self.create_rf_coverage_tab()
        self.tab_widget.addTab(tab_rf_coverage, "📊 RF Kapsama Alanı")

        return self.tab_widget

    def create_spectrum_tab(self) -> QWidget:
        """Gerçek Zamanlı FFT Spektrum Analizörü Sekmesini oluşturur."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. Başlık ve Telemetri Çubuğu
        header_bar = QHBoxLayout()
        title = QLabel("GERÇEK ZAMANLI SPEKTRUM ANALİZÖRÜ (FFT)")
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

        # 3. PyQtGraph Spektrum Analizör Grafiği
        self.spectrum_plot = pg.PlotWidget()
        self.spectrum_plot.setBackground("#090d13")
        self.spectrum_plot.showGrid(x=True, y=True, alpha=0.3)

        # X ve Y Eksen Etiketleri (Türkçe)
        self.spectrum_plot.setLabel("left", "Genlik", units="dB", color="#c9d1d9")
        self.spectrum_plot.setLabel("bottom", "Frekans (Bant)", units="MHz", color="#c9d1d9")

        # Grafik Başlığı
        self.spectrum_plot.setTitle(
            '<span style="color: #00ff66; font-size: 13px; font-weight: bold;">'
            "Gerçek Zamanlı Spektrum Analizi</span>"
        )
        self.spectrum_plot.setYRange(-120, 10, padding=0.02)

        # Spektrum Çizgisi (Taktik Yeşil)
        self.spectrum_curve = self.spectrum_plot.plot(
            pen=pg.mkPen(color="#00ff66", width=1.8),
            name="Anlık Spektrum"
        )

        # Tepe Tepe Maksimum Tutma Çizgisi (Max-Hold Cyan)
        self.max_hold_curve = self.spectrum_plot.plot(
            pen=pg.mkPen(color="#388bfd", width=1.2, style=Qt.DashLine),
            name="Tepe Tutma (Max-Hold)"
        )
        self.max_hold_data = None

        # Başlangıç boş eğrisi
        freq_axis_initial = np.linspace(
            -self.sample_rate / (2 * 1e6),
            self.sample_rate / (2 * 1e6),
            self.fft_size,
        )
        self.spectrum_curve.setData(freq_axis_initial, np.full(self.fft_size, -100.0))

        layout.addWidget(self.spectrum_plot, stretch=1)

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
        # Hassasiyet Eşiği Çizgisi (-100 dBm)
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

    def process_incoming_dsp_data(self):
        """ZMQ üzerinden gelen I/Q verilerini okur, FFT hesaplar ve grafiği günceller."""
        if not self.zmq_sub:
            return

        latest_iq = None
        # Kuyruktaki tüm paketleri tüketip en son paketi al (Düşük gecikme için)
        while True:
            result = self.zmq_sub.receive_iq_data(flags=zmq.NOBLOCK)
            if result is None:
                break
            _, iq_data = result
            if len(iq_data) > 0:
                latest_iq = iq_data
                self.total_frames_received += 1
                self.fps_counter += 1

        if latest_iq is not None:
            N = len(latest_iq)
            self.fft_size = N

            # 1. Hanning Pencereleme Uygula (Spektral Sızıntıyı Önle)
            window = np.hanning(N)
            windowed_iq = latest_iq * window

            # 2. FFT Hesaplama ve Merkezleme (FFT Shift)
            fft_result = np.fft.fft(windowed_iq, n=N)
            fft_shifted = np.fft.fftshift(fft_result)

            # 3. Logaritmik Büyüklük (dB) Dönüşümü
            magnitude_linear = np.abs(fft_shifted) / N
            magnitude_db = 20.0 * np.log10(np.maximum(magnitude_linear, 1e-7))

            # 4. Frekans Ekseni (MHz Cinsinden Merkez Çevresi)
            half_bw_mhz = (self.sample_rate / 2.0) / 1e6
            freq_axis = np.linspace(-half_bw_mhz, half_bw_mhz, N)

            # 5. Spektrum Eğrisini Güncelle
            self.spectrum_curve.setData(freq_axis, magnitude_db)

            # 6. Max-Hold (Tepe Tutma) Güncelle
            if self.max_hold_data is None or len(self.max_hold_data) != N:
                self.max_hold_data = magnitude_db.copy()
            else:
                self.max_hold_data = np.maximum(self.max_hold_data * 0.995, magnitude_db)
            self.max_hold_curve.setData(freq_axis, self.max_hold_data)

            # 7. Tepe Frekans ve Güç Analizi
            peak_idx = int(np.argmax(magnitude_db))
            peak_freq_khz = freq_axis[peak_idx] * 1000.0
            peak_pwr = magnitude_db[peak_idx]
            noise_floor_est = float(np.median(magnitude_db))

            self.card_peak_freq.setText(f"{peak_freq_khz:+.1f} kHz")
            self.card_peak_pwr.setText(f"{peak_pwr:.1f} dB")
            self.card_noise_floor.setText(f"{noise_floor_est:.1f} dB")

            # FPS Sayacı Güncellemesi
            now = time.time()
            dt = now - self.last_fps_time
            if dt >= 1.0:
                fps = self.fps_counter / dt
                self.card_fps_val.setText(f"{fps:.1f} FPS")
                self.fps_counter = 0
                self.last_fps_time = now

            self.lbl_dsp_badge.setText(f"[ AKIŞ: CANLI ({N} I/Q) ]")
            self.lbl_dsp_badge.setStyleSheet("color: #00ff66; font-weight: bold; font-size: 11px;")

    def calculate_rf_coverage(self):
        """Kullanıcı girişlerine göre Friis Link Bütçesini hesaplar ve grafiği günceller."""
        freq_mhz = self.spin_freq.value()
        tx_power_dbm = self.spin_tx_power.value()
        tx_gain_dbi = self.spin_tx_gain.value()
        rx_gain_dbi = self.spin_rx_gain.value()
        target_dist_km = self.spin_distance.value()

        # Link bütçesini hesapla
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

        # Kartları güncelle
        self.card_fspl_val.setText(f"{target_fspl:.2f} dB")
        self.card_prx_val.setText(f"{target_rx:.2f} dBm")
        self.card_eirp_val.setText(f"{eirp:.2f} dBm")
        self.card_status_val.setText(quality_text)
        self.card_status_val.setStyleSheet(
            f"color: {quality_color}; font-size: 15px; font-weight: bold; font-family: Consolas;"
        )

        # Grafiği güncelle
        self.curve_rx.setData(distances, rx_powers)
        self.point_target.setData([target_dist_km], [target_rx])

        # Hassasiyet eşiği çizgisini güncelle
        threshold_y = np.full_like(distances, -100.0)
        self.line_threshold.setData(distances, threshold_y)

        # Durum çubuğunu güncelle
        self.status_msg.setText(
            f"Link Bütçesi Hesaplandı (f={freq_mhz:.1f} MHz, d={target_dist_km:.2f} km, Prx={target_rx:.2f} dBm)"
        )
        self.freq_badge.setText(f"Frekans: {freq_mhz:.2f} MHz")

    def perform_zmq_ping_test(self):
        """ZeroMQ PUB/SUB köprüsünü test eder ve sonucu konsola ile arayüze yansıtır."""
        # Geçici bağımsız test soketi ile test yap
        success, detail = execute_ping_test(
            address="tcp://127.0.0.1:5555",
        )
        if success:
            self.status_msg.setText("ZMQ Testi Başarılı: PING -> Alındı (tcp://127.0.0.1:5555)")
            self.status_msg.setStyleSheet("color: #00ff66; font-weight: bold;")
        else:
            self.status_msg.setText(f"ZMQ Test Hatası: {detail}")
            self.status_msg.setStyleSheet("color: #ff4d4f; font-weight: bold;")

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
                "color: #00ff66; font-weight: bold; font-size: 11px; padding: 4px;"
            )
            self.status_msg.setText("Sistem Aktif - ZMQ Spektrum Alımı Başlatıldı")
            self.status_msg.setStyleSheet("color: #00ff66; font-weight: bold;")
            
            # FFT alım zamanlayıcısını başlat (~33 FPS)
            self.dsp_timer.start(30)
        else:
            self.btn_start.setText("Sistemi Başlat")
            self.btn_start.setStyleSheet("")  # Varsayılan taktik yeşile döner
            self.lbl_system_status.setText("● DURUM: BEKLEMEDE")
            self.lbl_system_status.setStyleSheet(
                "color: #ffaa00; font-weight: bold; font-size: 11px; padding: 4px;"
            )
            self.status_msg.setText("Sistem Durduruldu - Beklemede")
            self.status_msg.setStyleSheet("color: #ffaa00; font-weight: bold;")
            
            # Zamanlayıcıyı durdur
            self.dsp_timer.stop()
            self.lbl_dsp_badge.setText("[ AKIŞ: DURDURULDU ]")
            self.lbl_dsp_badge.setStyleSheet("color: #ffaa00; font-weight: bold; font-size: 11px;")

    def closeEvent(self, event):
        """Pencere kapatıldığında zamanlayıcıları ve ZeroMQ soketlerini temizler."""
        if hasattr(self, "dsp_timer") and self.dsp_timer.isActive():
            self.dsp_timer.stop()
        if self.zmq_pub:
            self.zmq_pub.close()
        if self.zmq_sub:
            self.zmq_sub.close()
        event.accept()


def main():
    # Fusion stili ve Taktik Tema Uygulaması
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(TACTICAL_STYLESHEET)

    # Koyu Palet Tanımı
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
