#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - I/Q Sinyal Kayıt ve Oynatma Modülü (Recording & Playback)
Canlı RF I/Q ikili (binary) akışlarını metaverisi ile birlikte diske kaydeder ve
kaydedilmiş sinyalleri ZMQ üzerinden donanım simülasyonu şeklinde tekrar oynatır.
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import zmq
from PyQt5.QtCore import QThread, pyqtSignal

from zmq_manager import ZMQPublisher, DEFAULT_ZMQ_ADDRESS


class IQRecorder:
    """I/Q Ham İkili Veri ve Metaveri Kayıt Yöneticisi."""

    def __init__(self, output_dir: str = "records"):
        self.output_dir = output_dir
        self.is_recording = False
        self.current_file = None
        self.current_filepath = ""
        self.meta_filepath = ""
        self.sample_rate = 2.048e6
        self.center_freq_mhz = 433.0
        self.total_samples_written = 0
        self.total_frames_written = 0
        self.bytes_written = 0
        self.start_time = 0.0

        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir, exist_ok=True)
            except OSError as e:
                print(f"[KAYIT HATA] Kayıt klasörü oluşturulamadı: {e}")

    def start_recording(
        self,
        filepath: Optional[str] = None,
        sample_rate: float = 2.048e6,
        center_freq_mhz: float = 433.0,
    ) -> str:
        """
        Yeni bir I/Q ikili dosya kaydı başlatır.
        :return: Oluşturulan dosya yolu
        """
        if self.is_recording:
            self.stop_recording()

        self.sample_rate = sample_rate
        self.center_freq_mhz = center_freq_mhz
        self.total_samples_written = 0
        self.total_frames_written = 0
        self.bytes_written = 0
        self.start_time = time.time()

        if not filepath:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"taktik_iq_{timestamp_str}.raw"
            self.current_filepath = os.path.join(self.output_dir, filename)
        else:
            self.current_filepath = filepath

        self.meta_filepath = os.path.splitext(self.current_filepath)[0] + ".meta.json"

        try:
            self.current_file = open(self.current_filepath, "wb")
            self.is_recording = True
            print(f"[KAYIT] Sinyal dosyası açıldı: {self.current_filepath}", flush=True)
            return self.current_filepath
        except IOError as e:
            print(f"[KAYIT HATA] Dosya açılamadı: {e}", flush=True)
            self.is_recording = False
            return ""

    def write_iq_data(self, iq_samples: np.ndarray) -> int:
        """
        Gelen I/Q dizisini ikili (complex64) formatında dosyaya yazar.
        :return: Yazılan bayt miktarı
        """
        if not self.is_recording or self.current_file is None:
            return 0

        try:
            if iq_samples.dtype != np.complex64:
                raw_bytes = iq_samples.astype(np.complex64).tobytes()
            else:
                raw_bytes = iq_samples.tobytes()

            self.current_file.write(raw_bytes)
            n_bytes = len(raw_bytes)
            self.bytes_written += n_bytes
            self.total_samples_written += len(iq_samples)
            self.total_frames_written += 1
            return n_bytes
        except IOError as e:
            print(f"[KAYIT HATA] Yazma hatası: {e}", flush=True)
            return 0

    def stop_recording(self) -> Optional[Dict[str, Any]]:
        """
        Kaydı sonlandırır, dosyayı kapatır ve SigMF uyumlu JSON metaverisini kaydeder.
        :return: Kayıt özet istatistikleri
        """
        if not self.is_recording:
            return None

        self.is_recording = False
        duration = max(time.time() - self.start_time, 0.001)

        if self.current_file and not self.current_file.closed:
            self.current_file.flush()
            self.current_file.close()
            self.current_file = None

        # SigMF Uyumlu Metaveri Yapısı
        metadata = {
            "global": {
                "core:datatype": "cf32_le",
                "core:sample_rate": self.sample_rate,
                "core:version": "1.0.0",
                "core:description": "Antigravity Taktik SDR I/Q Sinyal Kaydı",
                "core:author": "Antigravity Terminal",
                "core:datetime": datetime.now().isoformat(),
            },
            "captures": [
                {
                    "core:sample_start": 0,
                    "core:frequency": self.center_freq_mhz * 1e6,
                    "core:datetime": datetime.now().isoformat(),
                }
            ],
            "stats": {
                "total_samples": self.total_samples_written,
                "total_frames": self.total_frames_written,
                "total_bytes": self.bytes_written,
                "duration_seconds": round(duration, 2),
                "file_path": self.current_filepath,
            },
        }

        try:
            with open(self.meta_filepath, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"[KAYIT] Metaveri dosyası kaydedildi: {self.meta_filepath}", flush=True)
        except IOError as e:
            print(f"[KAYIT UYARI] Metaveri yazılamadı: {e}", flush=True)

        print(
            f"[KAYIT] Kayıt tamamlandı: {os.path.basename(self.current_filepath)} "
            f"({self.total_samples_written} örnek, {self.bytes_written/1024/1024:.2f} MB, {duration:.1f} sn)",
            flush=True,
        )
        return metadata["stats"]

    def get_stats(self) -> Dict[str, Any]:
        """Anlık kayıt istatistiklerini döndürür."""
        elapsed = max(time.time() - self.start_time, 0.0) if self.is_recording else 0.0
        return {
            "is_recording": self.is_recording,
            "filepath": self.current_filepath,
            "samples": self.total_samples_written,
            "frames": self.total_frames_written,
            "bytes": self.bytes_written,
            "size_mb": self.bytes_written / (1024.0 * 1024.0),
            "elapsed_seconds": elapsed,
        }


class IQPlaybackThread(QThread):
    """
    Kaydedilmiş I/Q ikili dosyasını okuyup ZMQ PUB soketi üzerinden
    canlı donanım yayını gibi oynatan çoklu iş parçacığı (QThread).
    """

    playback_progress = pyqtSignal(int, int, float)  # (mevcut_kare, toplam_kare, ilerleme_yuzdesi)
    playback_finished = pyqtSignal()
    log_signal = pyqtSignal(str, str)  # (seviye, mesaj)

    def __init__(
        self,
        filepath: str,
        address: str = DEFAULT_ZMQ_ADDRESS,
        chunk_size: int = 1024,
        target_fps: float = 20.0,
        loop: bool = True,
    ):
        super().__init__()
        self.filepath = filepath
        self.address = address
        self.chunk_size = chunk_size
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.loop = loop
        self._running = False

    def run(self):
        """Oynatma döngüsünü icra eder."""
        if not os.path.exists(self.filepath):
            self.log_signal.emit("HATA", f"Oynatılacak dosya bulunamadı: {self.filepath}")
            self.playback_finished.emit()
            return

        try:
            # İkili I/Q verisini complex64 olarak oku
            raw_data = np.fromfile(self.filepath, dtype=np.complex64)
            total_samples = len(raw_data)
            total_frames = total_samples // self.chunk_size

            if total_frames == 0:
                self.log_signal.emit("UYARI", "Kayıt dosyası boş veya yeterli I/Q örneği yok.")
                self.playback_finished.emit()
                return

            self.log_signal.emit(
                "BİLGİ",
                f"I/Q Dosyası Yüklendi: {os.path.basename(self.filepath)} "
                f"({total_samples} örnek, {total_frames} kare, Boyut: {os.path.getsize(self.filepath)/1024/1024:.2f} MB)",
            )

            # ZMQ Yayıncı Kurulumu
            ctx = zmq.Context()
            pub = ZMQPublisher(address=self.address, bind_mode=True, context=ctx)
            time.sleep(0.1)

            self._running = True
            self.log_signal.emit("DURUM", f"I/Q Sinyal Oynatımı Başlatıldı (Hız: {self.target_fps:.1f} FPS, Döngü: {self.loop})")

            while self._running:
                for frame_idx in range(total_frames):
                    if not self._running:
                        break

                    loop_start = time.time()
                    start_sample = frame_idx * self.chunk_size
                    end_sample = start_sample + self.chunk_size
                    iq_chunk = raw_data[start_sample:end_sample]

                    # ZMQ üzerinden yayınla
                    pub.send_iq_data(iq_chunk, topic="IQ")

                    # İlerleme sinyalini ilet
                    progress_pct = ((frame_idx + 1) / total_frames) * 100.0
                    self.playback_progress.emit(frame_idx + 1, total_frames, progress_pct)

                    # FPS oranında bekleme
                    elapsed = time.time() - loop_start
                    sleep_time = max(0.0, self.frame_interval - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                if not self.loop:
                    break

            pub.close()
            ctx.term()
            self.log_signal.emit("BİLGİ", "I/Q Sinyal Oynatımı Tamamlandı.")

        except Exception as e:
            self.log_signal.emit("HATA", f"Oynatma sırasında hata: {e}")
        finally:
            self._running = False
            self.playback_finished.emit()

    def stop(self):
        """Oynatmayı güvenle durdurur."""
        self._running = False
        self.wait(1500)
