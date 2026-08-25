#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Bağımsız Gelişmiş Mock DSP Düğümü (Advanced Signal Generator)
Sürekli Fazlı (Continuous-Phase) Frekans Taramalı Taşıyıcı (Chirp/Sweeper), Sabit CW İşareti,
Taktik Darbeli Sinyal ve Gauss Taban Gürültüsü Simülasyonu.
"""

import argparse
import signal
import sys
import time
import numpy as np
import zmq

from zmq_manager import ZMQPublisher, ZMQSubscriber, DEFAULT_ZMQ_ADDRESS


class AdvancedMockDSPNode:
    """Gelişmiş Sentetik I/Q RF Sinyal Üretici ve Yayıncı Düğüm Sınıfı."""

    def __init__(
        self,
        address: str = DEFAULT_ZMQ_ADDRESS,
        ew_control_address: str = "tcp://127.0.0.1:5556",
        sample_count: int = 1024,
        target_fps: float = 20.0,
        noise_level: float = 0.08,
    ):
        self.address = address
        self.ew_control_address = ew_control_address
        self.sample_count = sample_count
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.noise_level = noise_level
        self.running = False

        # Elektronik Harp (EW) Durum Değişkenleri
        self.jammer_active = False
        self.jammer_power = 0

        # ZMQ Yayıncı (I/Q Data PUB)
        self.publisher = ZMQPublisher(address=self.address, bind_mode=True)

        # ZMQ Abone (EW Control SUB)
        self.ew_subscriber = ZMQSubscriber(address=self.ew_control_address, topics=[""])

        # Sürekli Faz Akümülatörleri (Süreksizlik ve Sahte Spektral Sızıntıları Önler)
        self.sweep_phase = 0.0
        self.cw_phase = 0.0
        self.pulse_phase = 0.0

        # Frekans Tarama Parametreleri
        self.sweep_speed = 0.025  # Tarama döngü hızı
        self.sweep_width = 0.38   # Normalized frekans tarama genişliği (-0.38 .. +0.38)

    def check_ew_control_messages(self):
        """Arayüzden (UI) gelen Elektronik Harp (EW) kontrol komutlarını bloklamasız dinler."""
        if not self.ew_subscriber:
            return
        while True:
            msg = self.ew_subscriber.receive_json(flags=zmq.NOBLOCK)
            if msg is None:
                break
            if isinstance(msg, dict) and "jammer_active" in msg and "jammer_power" in msg:
                self.jammer_active = bool(msg["jammer_active"])
                self.jammer_power = int(msg["jammer_power"])

                status_str = "AKTİF" if self.jammer_active else "PASİF"
                print(
                    f"[ELEKTRONİK HARP] ZMQ Komutu Alındı -> Jammer: {status_str} | Güç: %{self.jammer_power}",
                    flush=True,
                )

    def generate_modulated_iq(self, frame_idx: int) -> np.ndarray:
        """
        Frekans taramalı (sweeping chirp), sabit CW ve darbeli taktik sinyaller içeren
        yüksek çözünürlüklü karmaşık (complex64) I/Q verisi üretir.
        """
        N = self.sample_count
        t_indices = np.arange(N)

        # 1. Taban Gürültüsü (Additive White Gaussian Noise - AWGN)
        noise_i = np.random.normal(0, self.noise_level, N)
        noise_q = np.random.normal(0, self.noise_level, N)
        noise = (noise_i + 1j * noise_q).astype(np.complex64)

        # 2. Dinamik Frekans Taramalı Taşıyıcı (Sweeping Frequency Carrier / Chirp)
        # Spektrum analizöründe gezinen sivri tepe ve şelalede belirgin çapraz/kademeli iz oluşturur
        current_sweep_freq = self.sweep_width * np.sin(frame_idx * self.sweep_speed)
        sweep_phase_delta = 2.0 * np.pi * current_sweep_freq
        sweep_phases = self.sweep_phase + sweep_phase_delta * t_indices
        self.sweep_phase = (sweep_phases[-1] + sweep_phase_delta) % (2.0 * np.pi)

        sweep_amplitude = 1.2
        sweep_signal = sweep_amplitude * np.exp(1j * sweep_phases)

        # 3. Sabit Referans Taşıyıcı (Fixed CW Beacon at f = -0.22)
        # Şelale ekranında dikey sabit bir referans çizgisi oluşturur
        cw_freq = -0.22
        cw_phase_delta = 2.0 * np.pi * cw_freq
        cw_phases = self.cw_phase + cw_phase_delta * t_indices
        self.cw_phase = (cw_phases[-1] + cw_phase_delta) % (2.0 * np.pi)

        cw_amplitude = 0.65
        cw_signal = cw_amplitude * np.exp(1j * cw_phases)

        # 4. Taktik Darbeli / Modüle Sinyal (Pulsed Burst Signal at f = +0.26)
        # 12 karenin 6'sında aktif olan yanıp sönen taktik veri paketi
        pulse_signal = np.zeros(N, dtype=np.complex64)
        if (frame_idx % 12) < 6:
            pulse_freq = 0.26
            pulse_phase_delta = 2.0 * np.pi * pulse_freq
            pulse_phases = self.pulse_phase + pulse_phase_delta * t_indices
            self.pulse_phase = (pulse_phases[-1] + pulse_phase_delta) % (2.0 * np.pi)
            pulse_signal = 0.85 * np.exp(1j * pulse_phases)

        # 5. Elektronik Harp (EW) / Baraj Karıştırıcı Gürültü Enjeksiyonu (Barrage Jamming)
        # Jammer aktif olduğunda, jammer_power (0-100) ile orantılı yüksek genlikli geniş bant Gauss gürültüsü basılır
        jammer_noise = np.zeros(N, dtype=np.complex64)
        if self.jammer_active and self.jammer_power > 0:
            power_ratio = float(self.jammer_power) / 100.0
            # Jammer gürültü standart sapması (sigma) %0-%100 arasında 0.0'dan 6.0'a yumuşak ölçeklenir
            jam_sigma = power_ratio * 6.0
            jam_i = np.random.normal(0, jam_sigma, N)
            jam_q = np.random.normal(0, jam_sigma, N)
            jammer_noise = (jam_i + 1j * jam_q).astype(np.complex64)

        # Toplam Modüle Edilmiş + Karıştırılmış I/Q Sinyali
        iq_total = (noise + sweep_signal + cw_signal + pulse_signal + jammer_noise).astype(np.complex64)
        return iq_total

    def start(self):
        """Mock DSP veri yayın döngüsünü başlatır."""
        self.running = True
        print("=" * 70, flush=True)
        print("[SİSTEM] Gelişmiş Mock DSP Modülasyon Düğümü Başlatıldı.", flush=True)
        print(f"[YAYIN] Soket Adresi: {self.address}", flush=True)
        print(f"[MODÜLASYON] 1. Frekans Taramalı Taşıyıcı (Sweeping Chirp: ±{self.sweep_width*100:.0f}% Bant)", flush=True)
        print(f"[MODÜLASYON] 2. Sabit CW Referans Taşıyıcı (Ofset: -0.22 Fs)", flush=True)
        print(f"[MODÜLASYON] 3. Taktik Darbeli Veri Paketi (Ofset: +0.26 Fs, 50% Doluluk)", flush=True)
        print(f"[AYARLAR] Örnek: {self.sample_count} I/Q | Hedef Hız: ~{self.target_fps:.1f} FPS", flush=True)
        print("[DURUM] Yüksek hızlı I/Q akışı aktif... (Durdurmak için CTRL+C)", flush=True)
        print("=" * 70, flush=True)

        frame_count = 0
        last_log_time = time.time()
        frames_since_log = 0

        try:
            while self.running:
                loop_start = time.time()

                # Gelen Elektronik Harp (EW) kontrol komutlarını kontrol et
                self.check_ew_control_messages()

                # Gelişmiş modülasyonlu I/Q verisi üret ve yayınla
                iq_samples = self.generate_modulated_iq(frame_count)
                self.publisher.send_iq_data(iq_samples, topic="IQ")

                frame_count += 1
                frames_since_log += 1

                # Her saniyede bir telemetri günlüğü bas
                current_time = time.time()
                if current_time - last_log_time >= 1.0:
                    actual_fps = frames_since_log / (current_time - last_log_time)
                    data_size_kb = (iq_samples.nbytes) / 1024.0
                    sweep_freq_rel = self.sweep_width * np.sin(frame_count * self.sweep_speed)
                    ew_info = f" | Jammer: AKTİF (%{self.jammer_power})" if self.jammer_active else ""
                    print(
                        f"[DSP MODÜLASYON] Kare: {frame_count:06d} | "
                        f"Boyut: {data_size_kb:.2f} KB | "
                        f"Hız: {actual_fps:.1f} FPS | "
                        f"Anlık Tarama Ofseti: {sweep_freq_rel:+.3f} Fs{ew_info} | Durum: AKTİF",
                        flush=True,
                    )
                    last_log_time = current_time
                    frames_since_log = 0

                # FPS kontrolü için hassas bekleme
                elapsed = time.time() - loop_start
                sleep_time = max(0.0, self.frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n[BİLGİ] Kullanıcı kesmesi (SIGINT) algılandı.", flush=True)
        finally:
            self.stop()

    def stop(self):
        """DSP düğümünü ve ZMQ soketlerini güvenle kapatır."""
        self.running = False
        if self.publisher:
            self.publisher.close()
        if self.ew_subscriber:
            self.ew_subscriber.close()
        print("[SİSTEM] Mock DSP Düğümü sonlandırıldı. Soketler güvenle kapatıldı.", flush=True)


# Geriye dönük uyumluluk için takma ad (alias)
MockDSPNode = AdvancedMockDSPNode


def handle_signal(sig, frame):
    print("\n[BİLGİ] Çıkış sinyali alındı. Kapatılıyor...", flush=True)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Antigravity Taktik SDR - Gelişmiş Mock DSP Modülasyon Motoru")
    parser.add_argument("--address", type=str, default=DEFAULT_ZMQ_ADDRESS, help="ZMQ PUB Adresi")
    parser.add_argument("--ew-address", type=str, default="tcp://127.0.0.1:5556", help="ZMQ EW Kontrol SUB Adresi")
    parser.add_argument("--samples", type=int, default=1024, help="Kare başına I/Q örnek sayısı")
    parser.add_argument("--fps", type=float, default=20.0, help="Yayın hızı (Kare/Saniye)")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    node = AdvancedMockDSPNode(
        address=args.address,
        ew_control_address=args.ew_address,
        sample_count=args.samples,
        target_fps=args.fps,
    )
    node.start()


if __name__ == "__main__":
    main()
