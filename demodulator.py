#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Yazılımsal Demodülasyon ve Sinyal Çözümleme Modülü (Software Demodulation)
AM, FM, NBFM demodülasyon algoritmaları, Squelch (susturma), ses çıkışı ve dijital telemetri çözücü.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PyQt5.QtCore import QByteArray, QIODevice, QObject, pyqtSignal
from PyQt5.QtMultimedia import QAudioFormat, QAudioOutput


def demodulate_am(
    iq_samples: np.ndarray,
    squelch_db: float = -80.0,
    volume: float = 1.0,
) -> Tuple[np.ndarray, float]:
    """
    Genlik Modülasyonu (AM) Zarf Algılayıcı Demodülatörü (Envelope Detector).
    
    :param iq_samples: Karmaşık I/Q numpy dizisi
    :param squelch_db: Susturma eşik değeri (dB)
    :param volume: Ses kazanç çarpanı (0.0 - 2.0)
    :return: (demodüle_edilmiş_ses_dizisi, ortalama_güç_db)
    """
    if len(iq_samples) == 0:
        return np.zeros(0, dtype=np.float32), -120.0

    # 1. Zarf Çıkarımı: |I + jQ| = sqrt(I^2 + Q^2)
    envelope = np.abs(iq_samples)

    # 2. Ortalama Sinyal Gücü Hesaplama (dB)
    mean_power = np.mean(envelope**2) + 1e-12
    power_db = float(10.0 * np.log10(mean_power))

    # 3. Susturma (Squelch) Kontrolü
    if power_db < squelch_db:
        return np.zeros(len(iq_samples), dtype=np.float32), power_db

    # 4. DC Bileşeni Kaldır (Yüksek Geçiren / Ortalama Çıkarma)
    audio = envelope - np.mean(envelope)

    # 5. Normalizasyon ve Ses Seviyesi Çarpanı
    max_val = np.max(np.abs(audio)) + 1e-6
    audio_normalized = (audio / max_val) * volume

    return audio_normalized.astype(np.float32), power_db


def demodulate_fm(
    iq_samples: np.ndarray,
    squelch_db: float = -80.0,
    volume: float = 1.0,
) -> Tuple[np.ndarray, float]:
    """
    Frekans Modülasyonu (FM) Faz Farkı / Polar Ayırıcı Demodülatörü (Polar Discriminator).
    
    Formül: dθ/dt ≈ angle(x[n] * conj(x[n-1]))
    
    :param iq_samples: Karmaşık I/Q numpy dizisi
    :param squelch_db: Susturma eşik değeri (dB)
    :param volume: Ses kazanç çarpanı (0.0 - 2.0)
    :return: (demodüle_edilmiş_ses_dizisi, ortalama_güç_db)
    """
    if len(iq_samples) < 2:
        return np.zeros(len(iq_samples), dtype=np.float32), -120.0

    # 1. Ortalama Sinyal Gücü Hesaplama (dB)
    power_db = float(10.0 * np.log10(np.mean(np.abs(iq_samples)**2) + 1e-12))

    # 2. Susturma (Squelch) Kontrolü
    if power_db < squelch_db:
        return np.zeros(len(iq_samples), dtype=np.float32), power_db

    # 3. Polar Ayrıştırma: Faz türevi hesabı
    conj_prod = iq_samples[1:] * np.conj(iq_samples[:-1])
    angle_diff = np.angle(conj_prod)

    # Boyutu eşitlemek için başa 1 eleman ekle
    audio = np.pad(angle_diff, (1, 0), mode="edge")

    # 4. DC Ofset Kaldırma ve Normalizasyon
    audio = audio - np.mean(audio)
    max_val = np.max(np.abs(audio)) + 1e-6
    audio_normalized = (audio / max_val) * volume

    return audio_normalized.astype(np.float32), power_db


def demodulate_nbfm(
    iq_samples: np.ndarray,
    squelch_db: float = -80.0,
    volume: float = 1.0,
) -> Tuple[np.ndarray, float]:
    """
    Dar Bant FM (NBFM) Demodülatörü ve Basit Alçak Geçiren Filtreleme.
    """
    audio, power_db = demodulate_fm(iq_samples, squelch_db=squelch_db, volume=volume)
    if len(audio) > 4:
        # 5-noktalı hareketli ortalama filtresi (De-emphasis / Low-pass simülasyonu)
        audio = np.convolve(audio, np.ones(5) / 5.0, mode="same")
    return audio.astype(np.float32), power_db


class DigitalDecoder:
    """Sentetik Taktik Dijital Paket Çözümleyici (Digital Frame & Telemetry Decoder)."""

    def __init__(self):
        self.frame_counter = 0
        self.callsigns = ["TK-SDR-01", "GÖKTÜRK-ALPHA", "TAKTİK-KOMUTA-7", "ANKA-SİNYAL-04"]
        self.tactical_nodes = ["MERKEZ ÜS", "İLERİ GÖZETLEME", "RÖLE İSTASYONU", "MOBİL SDR"]

    def decode_frame(self, iq_samples: np.ndarray, frame_idx: int) -> Optional[Dict[str, Any]]:
        """
        I/Q sinyalinden simüle edilmiş dijital taktik telemetri paketini çözer.
        """
        # Her 15 karede bir yeni bir taktik dijital paket tespit et
        if frame_idx % 15 == 0 and len(iq_samples) > 0:
            self.frame_counter += 1
            node_idx = (frame_idx // 15) % len(self.callsigns)
            callsign = self.callsigns[node_idx]
            node_type = self.tactical_nodes[node_idx]

            # Koordinat ve telemetri hesabı
            lat = 39.9255 + 0.005 * np.sin(frame_idx * 0.1)
            lon = 32.8662 + 0.005 * np.cos(frame_idx * 0.1)
            pwr_val = 10.0 * np.log10(np.mean(np.abs(iq_samples)**2) + 1e-12)

            return {
                "paket_no": self.frame_counter,
                "cagri_kodu": callsign,
                "istasyon": node_type,
                "protokol": "TAKTİK FSK-9600",
                "koordinat": f"{lat:.4f}° K, {lon:.4f}° D",
                "rssi_dbm": round(pwr_val, 1),
                "ber_orani": f"{max(0.0001, 0.002 * np.random.rand()):.4%}",
                "mesaj": f"[GÖREV AKTİF] Durum Raporu #{self.frame_counter:04d} - Sinyal Kararlı",
                "zaman": time.strftime("%H:%M:%S"),
            }
        return None


class TacticalAudioOutput(QObject):
    """
    PyQt5 QtMultimedia QAudioOutput kullanarak PCM ses akışını
    sistem hoparlörlerine ileten taktik ses motoru.
    """

    def __init__(self, sample_rate: int = 8000):
        super().__init__()
        self.sample_rate = sample_rate
        self.is_active = False
        self.audio_output: Optional[QAudioOutput] = None
        self.audio_device: Optional[QIODevice] = None
        self.init_audio_engine()

    def init_audio_engine(self):
        """Ses formatını ve QAudioOutput nesnesini yapılandırır."""
        audio_format = QAudioFormat()
        audio_format.setSampleRate(self.sample_rate)
        audio_format.setChannelCount(1)
        audio_format.setSampleSize(16)
        audio_format.setCodec("audio/pcm")
        audio_format.setByteOrder(QAudioFormat.LittleEndian)
        audio_format.setSampleType(QAudioFormat.SignedInt)

        try:
            self.audio_output = QAudioOutput(audio_format)
            self.audio_output.setVolume(0.8)
        except Exception as e:
            print(f"[SES UYARI] QAudioOutput başlatılamadı: {e}")

    def start_audio(self):
        """Ses akışını başlatır."""
        if self.audio_output and not self.is_active:
            try:
                self.audio_device = self.audio_output.start()
                self.is_active = True
            except Exception as e:
                print(f"[SES HATA] Ses cihazı başlatılamadı: {e}")
                self.is_active = False

    def stop_audio(self):
        """Ses akışını durdurur."""
        if self.audio_output and self.is_active:
            try:
                self.audio_output.stop()
            except Exception:
                pass
            self.is_active = False
            self.audio_device = None

    def write_audio_samples(self, float_samples: np.ndarray):
        """Demodüle edilmiş float32 ses örneklerini int16 PCM formatına dönüştürüp hoparlöre yazar."""
        if not self.is_active or self.audio_device is None or len(float_samples) == 0:
            return

        try:
            # Örnekleme oranını audio_rate'e yaklaştırmak için alt-örnekle (decimate)
            if len(float_samples) > 256:
                step = max(1, len(float_samples) // 256)
                resampled = float_samples[::step]
            else:
                resampled = float_samples

            # Float [-1.0 .. 1.0] -> Int16 [-32767 .. 32767]
            clipped = np.clip(resampled, -1.0, 1.0)
            int16_samples = (clipped * 32767.0).astype(np.int16)
            raw_bytes = int16_samples.tobytes()

            if self.audio_output.bytesFree() >= len(raw_bytes):
                self.audio_device.write(raw_bytes)
        except Exception as e:
            print(f"[SES HATA] Yazma hatası: {e}")
