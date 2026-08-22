#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Bağımsız Mock DSP Düğümü (Data Generator)
Arayüzden (GUI) tamamen bağımsız çalışan, sentetik I/Q verisi üreten ve ZMQ üzerinden yayınlayan simülatör.
"""

import argparse
import signal
import sys
import time
import numpy as np
import zmq

from zmq_manager import ZMQPublisher, DEFAULT_ZMQ_ADDRESS


class MockDSPNode:
    """Sentetik I/Q Verisi Üretici ve Yayıncı Düğüm Sınıfı."""

    def __init__(
        self,
        address: str = DEFAULT_ZMQ_ADDRESS,
        sample_count: int = 1024,
        target_fps: float = 20.0,
        noise_level: float = 0.15,
    ):
        self.address = address
        self.sample_count = sample_count
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.noise_level = noise_level
        self.running = False

        # ZMQ Yayıncı
        self.publisher = ZMQPublisher(address=self.address, bind_mode=True)

        # Sinyal simülasyon parametreleri (Dinamik Taşıyıcı ve Modülasyon)
        self.phase = 0.0
        self.carrier_freq_offset = 0.15  # Normalize frekans offseti (-0.5 .. +0.5)

    def generate_synthetic_iq(self, frame_idx: int) -> np.ndarray:
        """
        Gürültü tabanı ve sentetik RF sinyalleri içeren karmaşık (complex64) I/Q verisi üretir.
        """
        N = self.sample_count

        # 1. Taban Gürültüsü (Gaussian White Noise)
        noise_i = np.random.normal(0, self.noise_level, N)
        noise_q = np.random.normal(0, self.noise_level, N)
        iq_noise = noise_i + 1j * noise_q

        # 2. Sentetik Taşıyıcı Sinyal (CW / Modüle Taşıyıcı)
        t = np.arange(N)
        # Frekansta yavaş kayma (drift) simülasyonu
        drift = 0.05 * np.sin(frame_idx * 0.05)
        current_freq = self.carrier_freq_offset + drift

        # Sinyal genliği ve faz ilerlemesi
        signal_amplitude = 0.75
        signal_phase = self.phase + 2.0 * np.pi * current_freq * t
        self.phase = (signal_phase[-1] + 2.0 * np.pi * current_freq) % (2.0 * np.pi)

        carrier = signal_amplitude * np.exp(1j * signal_phase)

        # 3. İkincil Darbeli Sinyal (Pulsed Signal Simülasyonu)
        pulse = np.zeros(N, dtype=np.complex64)
        if (frame_idx % 8) < 4:  # Periyodik yanıp sönen taktik sinyal
            secondary_freq = -0.28
            pulse = 0.45 * np.exp(1j * (2.0 * np.pi * secondary_freq * t))

        # 4. Toplam I/Q Sinyali
        iq_data = (iq_noise + carrier + pulse).astype(np.complex64)
        return iq_data

    def start(self):
        """Mock DSP veri yayın döngüsünü başlatır."""
        self.running = True
        print("=" * 65, flush=True)
        print(f"[SİSTEM] Mock DSP Düğümü Başlatıldı.", flush=True)
        print(f"[YAYIN] Adres: {self.address}", flush=True)
        print(f"[AYARLAR] Örnek Sayısı: {self.sample_count} I/Q | Hedef Hız: ~{self.target_fps:.1f} FPS", flush=True)
        print(f"[DURUM] Veri yayını yapılıyor... (Durdurmak için CTRL+C)", flush=True)
        print("=" * 65, flush=True)

        frame_count = 0
        last_log_time = time.time()
        frames_since_log = 0

        try:
            while self.running:
                loop_start = time.time()

                # I/Q verisi üret ve ZMQ üzerinden yayınla
                iq_samples = self.generate_synthetic_iq(frame_count)
                success = self.publisher.send_iq_data(iq_samples, topic="IQ")

                frame_count += 1
                frames_since_log += 1

                # Her saniyede bir telemetri günlüğü bas
                current_time = time.time()
                if current_time - last_log_time >= 1.0:
                    actual_fps = frames_since_log / (current_time - last_log_time)
                    data_size_kb = (iq_samples.nbytes) / 1024.0
                    print(
                        f"[DSP AKIŞI] Kare: {frame_count:06d} | "
                        f"Boyut: {data_size_kb:.2f} KB ({self.sample_count} I/Q) | "
                        f"Hız: {actual_fps:.1f} FPS | Durum: AKTİF",
                        flush=True,
                    )
                    last_log_time = current_time
                    frames_since_log = 0

                # FPS kontrolü için bekleme
                elapsed = time.time() - loop_start
                sleep_time = max(0.0, self.frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n[BİLGİ] Kullanıcı kesmesi (SIGINT) algılandı.", flush=True)
        finally:
            self.stop()

    def stop(self):
        """DSP düğümünü ve ZMQ soketini güvenle kapatır."""
        self.running = False
        if self.publisher:
            self.publisher.close()
        print("[SİSTEM] Mock DSP Düğümü sonlandırıldı. Soketler güvenle kapatıldı.", flush=True)


def handle_signal(sig, frame):
    print("\n[BİLGİ] Çıkış sinyali alındı. Kapatılıyor...", flush=True)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Antigravity Taktik SDR - Mock DSP Veri Üretici")
    parser.add_argument("--address", type=str, default=DEFAULT_ZMQ_ADDRESS, help="ZMQ PUB Adresi")
    parser.add_argument("--samples", type=int, default=1024, help="Kare başına I/Q örnek sayısı")
    parser.add_argument("--fps", type=float, default=20.0, help="Yayın hızı (Kare/Saniye)")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    node = MockDSPNode(
        address=args.address,
        sample_count=args.samples,
        target_fps=args.fps,
    )
    node.start()


if __name__ == "__main__":
    main()
