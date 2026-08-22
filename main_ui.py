#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Ana Kullanıcı Arayüzü (Main UI)
Modern, koyu taktik temalı PyQt5 ana pencere çerçevesi.
"""

import sys
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette
from PyQt5.QtWidgets import (
    QApplication,
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
    QVBoxLayout,
    QWidget,
)


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

/* --- Panel & GroupBox Stili --- */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    margin-top: 24px;
    padding: 14px 10px 10px 10px;
    font-weight: bold;
    color: #00ff66;
    letter-spacing: 1px;
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
    font-size: 14px;
    padding: 10px 16px;
}

QPushButton#btn_primary:hover {
    background-color: #22683e;
    color: #ffffff;
    border: 1px solid #39ff14;
    box-shadow: 0px 0px 8px rgba(0, 255, 102, 0.4);
}

QPushButton#btn_primary:pressed {
    background-color: #0f301d;
    color: #00e676;
}

/* --- Çerçeve ve Bölücüler --- */
QFrame#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

QFrame#plot_area_container {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
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

/* --- Kaydırma Çubuğu (Scrollbar) --- */
QScrollBar:vertical {
    background: #0d1117;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #00ff66;
}
"""


class TacticalMainWindow(QMainWindow):
    """Antigravity Taktik SDR Terminali Ana Pencere Sınıfı."""

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.init_ui()

    def init_ui(self):
        # 1. Ana Pencere Temel Ayarları
        self.setWindowTitle("Antigravity Taktik SDR Terminali")
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)

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

        # 5. Merkezi Gösterge / Grafik Alanı
        central_display_widget = self.create_central_display()
        splitter.addWidget(central_display_widget)

        # Bölücü Başlangıç Oranları (%22 Kontrol, %78 Grafik)
        splitter.setSizes([280, 1000])

        # 6. Alt Durum Çubuğu (Status Bar)
        self.setup_status_bar()

        # 7. Saat / Zamanlayıcı
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

    def create_sidebar(self) -> QWidget:
        """Sol kontrol paneli bileşenlerini oluşturur."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(260)
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

        # Sistem Başlatma / Durdurma Grubu
        sys_group = QGroupBox("SİSTEM KONTROLÜ")
        sys_layout = QVBoxLayout(sys_group)
        sys_layout.setSpacing(12)

        # "Sistemi Başlat" Butonu
        self.btn_start = QPushButton("Sistemi Başlat")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setToolTip("Terminali başlatır")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.toggle_system)
        sys_layout.addWidget(self.btn_start)

        # Sistem Durum Göstergesi
        self.lbl_system_status = QLabel("● DURUM: BEKLEMEDE")
        self.lbl_system_status.setStyleSheet(
            "color: #ffaa00; font-weight: bold; font-size: 11px; padding: 4px;"
        )
        self.lbl_system_status.setAlignment(Qt.AlignCenter)
        sys_layout.addWidget(self.lbl_system_status)

        layout.addWidget(sys_group)

        # RF Yapılandırma Bilgi Paneli (Gelecek Aşamalar İçin Hazır Alan)
        rf_group = QGroupBox("RF PARAMETRELERİ")
        rf_layout = QVBoxLayout(rf_group)
        rf_layout.setSpacing(8)

        lbl_freq = QLabel("Merkez Frekans: 100.000 MHz")
        lbl_freq.setStyleSheet("color: #8b949e; font-size: 12px;")
        lbl_gain = QLabel("Kazanç: 20 dB")
        lbl_gain.setStyleSheet("color: #8b949e; font-size: 12px;")
        lbl_sample_rate = QLabel("Örnekleme: 2.048 MS/s")
        lbl_sample_rate.setStyleSheet("color: #8b949e; font-size: 12px;")

        rf_layout.addWidget(lbl_freq)
        rf_layout.addWidget(lbl_gain)
        rf_layout.addWidget(lbl_sample_rate)

        layout.addWidget(rf_group)

        # Telemetri / Kayıt Özeti
        telemetry_group = QGroupBox("SİSTEM BİLGİSİ")
        tel_layout = QVBoxLayout(telemetry_group)
        tel_layout.setSpacing(6)

        lbl_engine = QLabel("Motor: PyZMQ & NumPy")
        lbl_engine.setStyleSheet("color: #8b949e; font-size: 11px;")
        lbl_gui_ver = QLabel("Arayüz Sürümü: v1.0.0 (Faz 2)")
        lbl_gui_ver.setStyleSheet("color: #8b949e; font-size: 11px;")

        tel_layout.addWidget(lbl_engine)
        tel_layout.addWidget(lbl_gui_ver)

        layout.addWidget(telemetry_group)

        # Alt Boşluk Doldurucu
        layout.addStretch()

        # Alt Marka Bilgisi
        lbl_footer = QLabel("ANTIGRAVITY // TACTICAL SDR")
        lbl_footer.setStyleSheet("color: #484f58; font-size: 10px; letter-spacing: 2px;")
        lbl_footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_footer)

        return sidebar

    def create_central_display(self) -> QWidget:
        """Merkezi grafik ve gösterge alanını oluşturur."""
        container = QFrame()
        container.setObjectName("plot_area_container")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Gösterge Alanı Başlık Çubuğu
        header_bar = QHBoxLayout()
        title = QLabel("SPEKTRUM VE ŞELALE GÖSTERGESİ")
        title.setStyleSheet(
            "color: #00ff66; font-size: 14px; font-weight: bold; letter-spacing: 1px;"
        )
        header_bar.addWidget(title)
        header_bar.addStretch()

        mode_badge = QLabel("[ MOD: REAL-TIME FFT ]")
        mode_badge.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 11px;")
        header_bar.addWidget(mode_badge)

        layout.addLayout(header_bar)

        # Gelecekteki Grafikler İçin Yer Tutucu Çerçeve (Placeholder Area)
        placeholder_frame = QFrame()
        placeholder_frame.setStyleSheet(
            """
            QFrame {
                background-color: #090d13;
                border: 1px dashed #30363d;
                border-radius: 8px;
            }
            """
        )
        placeholder_layout = QVBoxLayout(placeholder_frame)
        placeholder_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("📡")
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)

        info_title = QLabel("GRAFİK VE SPEKTRUM GÖSTERGE ALANI")
        info_title.setStyleSheet(
            "color: #f0f6fc; font-size: 16px; font-weight: bold; background: transparent;"
        )
        info_title.setAlignment(Qt.AlignCenter)

        info_desc = QLabel(
            "Bu alan Faz 3 ve Faz 4 kapsamında PyQtGraph spektrum analizörü ve şelale (waterfall) göstergesi ile donatılacaktır."
        )
        info_desc.setStyleSheet("color: #8b949e; font-size: 12px; background: transparent;")
        info_desc.setAlignment(Qt.AlignCenter)

        placeholder_layout.addWidget(icon_label)
        placeholder_layout.addWidget(info_title)
        placeholder_layout.addWidget(info_desc)

        layout.addWidget(placeholder_frame)

        return container

    def setup_status_bar(self):
        """Alt taktik durum çubuğunu yapılandırır."""
        status_bar = self.statusBar()

        self.status_msg = QLabel("Hazır")
        self.status_msg.setStyleSheet("color: #00ff66; font-weight: bold;")

        self.freq_badge = QLabel("Frekans: 100.00 MHz")
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
            self.status_msg.setText("Sistem Aktif - Veri Alımı Başlatıldı")
            self.status_msg.setStyleSheet("color: #00ff66; font-weight: bold;")
        else:
            self.btn_start.setText("Sistemi Başlat")
            self.btn_start.setStyleSheet("")  # Varsayılan taktik yeşile döner
            self.lbl_system_status.setText("● DURUM: BEKLEMEDE")
            self.lbl_system_status.setStyleSheet(
                "color: #ffaa00; font-weight: bold; font-size: 11px; padding: 4px;"
            )
            self.status_msg.setText("Sistem Durduruldu - Beklemede")
            self.status_msg.setStyleSheet("color: #ffaa00; font-weight: bold;")


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
