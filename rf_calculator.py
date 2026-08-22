#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - RF Link Bütçesi ve Kapsama Hesaplayıcı Motoru
Friis İletim Denklemi ve Serbest Uzay Yayılım Kaybı (FSPL) hesaplamaları.
"""

import math
from typing import Dict, Tuple, Union
import numpy as np

# Işık hızı (m/s)
SPEED_OF_LIGHT = 299792458.0


def calculate_fspl(frequency_mhz: float, distance_km: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Serbest Uzay Yol Kaybını (Free Space Path Loss - FSPL) dB cinsinden hesaplar.
    
    Formül:
    FSPL (dB) = 20 * log10(d_km) + 20 * log10(f_mhz) + 32.4478
    
    :param frequency_mhz: Sinyal frekansı (MHz)
    :param distance_km: İletim mesafesi (km) (sayı veya numpy dizisi)
    :return: FSPL değeri (dB)
    """
    # 20*log10(4*pi/c) + 20*log10(10^3) + 20*log10(10^6) = 32.44778...
    constant_factor = 20.0 * math.log10(4.0 * math.pi / SPEED_OF_LIGHT) + 180.0  # 32.44778122
    
    if isinstance(distance_km, (int, float)):
        if distance_km <= 0 or frequency_mhz <= 0:
            return 0.0
        return 20.0 * math.log10(distance_km) + 20.0 * math.log10(frequency_mhz) + constant_factor
    else:
        # NumPy dizisi için güvenli log10
        safe_dist = np.maximum(distance_km, 1e-6)
        safe_freq = max(frequency_mhz, 1e-6)
        return 20.0 * np.log10(safe_dist) + 20.0 * np.log10(safe_freq) + constant_factor


def calculate_rx_power(
    tx_power_dbm: float,
    tx_gain_dbi: float,
    rx_gain_dbi: float,
    frequency_mhz: float,
    distance_km: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """
    Friis İletim Denklemine göre Alınan Gücü (Received Power - Prx) dBm cinsinden hesaplar.
    
    Formül:
    Prx (dBm) = Ptx (dBm) + Gtx (dBi) + Grx (dBi) - FSPL (dB)
    
    :param tx_power_dbm: Verici çıkış gücü (dBm)
    :param tx_gain_dbi: Verici anten kazancı (dBi)
    :param rx_gain_dbi: Alıcı anten kazancı (dBi)
    :param frequency_mhz: Frekans (MHz)
    :param distance_km: Mesafe (km)
    :return: Alınan Güç (dBm)
    """
    fspl = calculate_fspl(frequency_mhz, distance_km)
    return tx_power_dbm + tx_gain_dbi + rx_gain_dbi - fspl


def compute_link_budget(
    frequency_mhz: float,
    tx_power_dbm: float,
    tx_gain_dbi: float,
    rx_gain_dbi: float,
    target_distance_km: float,
    num_points: int = 300,
) -> Dict[str, Union[float, np.ndarray, str]]:
    """
    Belirtilen RF parametrelerine göre kapsamlı Link Bütçesi ve mesafe eğrisini hesaplar.
    
    :return: Sonuç sözlüğü (mesafe dizisi, alınan güç dizisi, hedef nokta değerleri ve sinyal kalitesi)
    """
    target_dist = max(target_distance_km, 0.01)
    
    # 0.05 km'den hedef mesafenin 1.5 katına kadar log/lineer mesafe dizisi
    max_range = max(target_dist * 1.3, 1.0)
    min_range = max(max_range / 500.0, 0.01)
    distances = np.linspace(min_range, max_range, num_points)
    
    rx_powers = calculate_rx_power(
        tx_power_dbm=tx_power_dbm,
        tx_gain_dbi=tx_gain_dbi,
        rx_gain_dbi=rx_gain_dbi,
        frequency_mhz=frequency_mhz,
        distance_km=distances,
    )
    
    fspl_curve = calculate_fspl(frequency_mhz, distances)
    
    # Hedef mesafedeki tekil sonuçlar
    target_fspl = float(calculate_fspl(frequency_mhz, target_dist))
    target_rx_power = float(
        calculate_rx_power(
            tx_power_dbm=tx_power_dbm,
            tx_gain_dbi=tx_gain_dbi,
            rx_gain_dbi=rx_gain_dbi,
            frequency_mhz=frequency_mhz,
            distance_km=target_dist,
        )
    )
    
    # EIRP (Eşdeğer İzotropik Işıma Gücü)
    eirp_dbm = tx_power_dbm + tx_gain_dbi
    
    # Sinyal Kalite Değerlendirmesi
    if target_rx_power >= -70.0:
        quality_text = "MÜKEMMEL (Güçlü Sinyal)"
        quality_color = "#00ff66"
    elif target_rx_power >= -85.0:
        quality_text = "İYİ (Kararlı Bağlantı)"
        quality_color = "#58a6ff"
    elif target_rx_power >= -100.0:
        quality_text = "ORTA / ZAYIF (Eşik Değerine Yakın)"
        quality_color = "#ffaa00"
    else:
        quality_text = "KRİTİK / KOPUK (Hassasiyet Altında)"
        quality_color = "#ff4d4f"
        
    return {
        "distances": distances,
        "rx_powers": rx_powers,
        "fspl_curve": fspl_curve,
        "target_distance_km": target_dist,
        "target_fspl": target_fspl,
        "target_rx_power": target_rx_power,
        "eirp_dbm": eirp_dbm,
        "quality_text": quality_text,
        "quality_color": quality_color,
    }
