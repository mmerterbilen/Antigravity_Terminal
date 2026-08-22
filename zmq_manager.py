#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - ZeroMQ Ara Katman (Middleware) Modülü
PUB/SUB mimarisi ile yüksek hızlı, asenkron ve bloklamasız veri iletimi.
I/Q karmaşık sayı dizilerinin ikili (binary) serileştirilmesini destekler.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import zmq


DEFAULT_ZMQ_ADDRESS = "tcp://127.0.0.1:5555"


class ZMQPublisher:
    """ZeroMQ Yayıncı (Publisher - PUB) Sınıfı."""

    def __init__(
        self,
        address: str = DEFAULT_ZMQ_ADDRESS,
        bind_mode: bool = True,
        context: Optional[zmq.Context] = None,
    ):
        self.address = address
        self.bind_mode = bind_mode
        self.context = context or zmq.Context.instance()
        self.socket: Optional[zmq.Socket] = None
        self._is_active = False
        self.setup_socket()

    def setup_socket(self):
        """PUB soketini oluşturur ve bağlar (veya bağlanır)."""
        if not self._is_active:
            self.socket = self.context.socket(zmq.PUB)
            self.socket.setsockopt(zmq.LINGER, 0)
            try:
                if self.bind_mode:
                    self.socket.bind(self.address)
                else:
                    self.socket.connect(self.address)
                self._is_active = True
            except zmq.ZMQError as e:
                print(f"[ZMQ PUB UYARI] Soket kurulumu ({self.address}): {e}")
                self._is_active = False

    def send_string(self, message: str, topic: str = "") -> bool:
        """Dize mesajını yayınlar."""
        if not self.socket or self.socket.closed or not self._is_active:
            return False
        try:
            full_msg = f"{topic} {message}" if topic else message
            self.socket.send_string(full_msg)
            return True
        except zmq.ZMQError as e:
            print(f"[ZMQ PUB HATA] Mesaj iletilemedi: {e}")
            return False

    def send_json(self, data: Dict[str, Any], topic: str = "") -> bool:
        """JSON verisini yayınlar."""
        return self.send_string(json.dumps(data), topic=topic)

    def send_iq_data(self, iq_samples: np.ndarray, topic: str = "IQ") -> bool:
        """
        Karmaşık I/Q numpy dizisini ikili (binary) biçimde yüksek hızla yayınlar.
        """
        if not self.socket or self.socket.closed or not self._is_active:
            return False
        try:
            # Complex64 (32-bit float I + 32-bit float Q) formatına dönüştür
            if iq_samples.dtype != np.complex64:
                iq_bytes = iq_samples.astype(np.complex64).tobytes()
            else:
                iq_bytes = iq_samples.tobytes()

            topic_bytes = topic.encode("utf-8")
            self.socket.send_multipart([topic_bytes, iq_bytes])
            return True
        except zmq.ZMQError as e:
            print(f"[ZMQ PUB HATA] I/Q verisi iletilemedi: {e}")
            return False

    def close(self):
        """Soketi kapatır."""
        if self.socket and not self.socket.closed:
            self.socket.close()
            self._is_active = False


class ZMQSubscriber:
    """ZeroMQ Abone (Subscriber - SUB) Sınıfı."""

    def __init__(
        self,
        address: str = DEFAULT_ZMQ_ADDRESS,
        topics: Optional[List[str]] = None,
        context: Optional[zmq.Context] = None,
    ):
        self.address = address
        self.context = context or zmq.Context.instance()
        self.socket: Optional[zmq.Socket] = None
        self._is_connected = False
        self.connect()

        # Konulara abone ol (varsayılan: tüm mesajlar)
        if topics:
            for t in topics:
                self.subscribe(t)
        else:
            self.subscribe("")

    def connect(self):
        """SUB soketini oluşturur ve belirtilen adrese bağlanır."""
        if not self._is_connected:
            self.socket = self.context.socket(zmq.SUB)
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.connect(self.address)
            self._is_connected = True

    def subscribe(self, topic: str = ""):
        """Belirtilen konuya abone olur."""
        if self.socket and not self.socket.closed:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def unsubscribe(self, topic: str = ""):
        """Aboneliği sonlandırır."""
        if self.socket and not self.socket.closed:
            self.socket.setsockopt_string(zmq.UNSUBSCRIBE, topic)

    def receive_string(self, flags: int = zmq.NOBLOCK) -> Optional[str]:
        """Bloklamasız veya bloklamalı dize mesajı alır."""
        if not self.socket or self.socket.closed:
            return None
        try:
            return self.socket.recv_string(flags=flags)
        except zmq.Again:
            return None
        except zmq.ZMQError as e:
            print(f"[ZMQ SUB HATA] Mesaj alınamadı: {e}")
            return None

    def receive_json(self, flags: int = zmq.NOBLOCK) -> Optional[Dict[str, Any]]:
        """Bloklamasız JSON mesajı alır."""
        msg = self.receive_string(flags=flags)
        if msg is None:
            return None
        try:
            return json.loads(msg)
        except json.JSONDecodeError:
            return None

    def receive_iq_data(self, flags: int = zmq.NOBLOCK) -> Optional[Tuple[str, np.ndarray]]:
        """
        Bloklamasız ikili I/Q numpy dizisini alır.
        Dönüş: (konu_adı, np.ndarray(dtype=complex64)) veya None
        """
        if not self.socket or self.socket.closed:
            return None
        try:
            frames = self.socket.recv_multipart(flags=flags)
            if len(frames) >= 2:
                topic = frames[0].decode("utf-8", errors="ignore")
                raw_bytes = frames[1]
                iq_array = np.frombuffer(raw_bytes, dtype=np.complex64)
                return topic, iq_array
            elif len(frames) == 1:
                iq_array = np.frombuffer(frames[0], dtype=np.complex64)
                return "", iq_array
            return None
        except zmq.Again:
            return None
        except zmq.ZMQError as e:
            print(f"[ZMQ SUB HATA] I/Q verisi okunamadı: {e}")
            return None

    def close(self):
        """Soketi kapatır."""
        if self.socket and not self.socket.closed:
            self.socket.close()
            self._is_connected = False


def execute_ping_test(
    publisher: Optional[ZMQPublisher] = None,
    subscriber: Optional[ZMQSubscriber] = None,
    address: str = DEFAULT_ZMQ_ADDRESS,
    timeout_ms: int = 1500,
) -> Tuple[bool, str]:
    """
    ZeroMQ PUB/SUB köprüsü üzerinde PING/PONG bağlantı testi icra eder.
    """
    should_cleanup = False
    if publisher is None or subscriber is None:
        ctx = zmq.Context.instance()
        pub = ZMQPublisher(address=address, bind_mode=True, context=ctx)
        sub = ZMQSubscriber(address=address, context=ctx)
        should_cleanup = True
    else:
        pub = publisher
        sub = subscriber

    try:
        time.sleep(0.1)

        # Eski kuyrukları temizle
        while sub.receive_string(flags=zmq.NOBLOCK) is not None:
            pass

        test_payload = "PING"
        sent_success = pub.send_string(test_payload)
        if not sent_success:
            return False, "HATA: PING mesajı sokete gönderilemedi."

        start_time = time.time()
        received_msg = None
        while (time.time() - start_time) * 1000.0 < timeout_ms:
            msg = sub.receive_string(flags=zmq.NOBLOCK)
            if msg is not None:
                # Eşleşme kontrolü (konulu veya konusuz)
                if "PING" in msg:
                    received_msg = "PING"
                    break
            time.sleep(0.01)

        if received_msg == "PING":
            elapsed = (time.time() - start_time) * 1000.0
            log_msg = f"[ZMQ TEST] Gönderilen: '{test_payload}' | Alınan: '{received_msg}' | Gecikme: {elapsed:.2f}ms | Durum: BAŞARILI"
            print(log_msg)
            return True, log_msg
        else:
            log_msg = f"[ZMQ TEST HATA] Zaman aşımı veya beklenmeyen yanıt: '{received_msg}'"
            print(log_msg)
            return False, log_msg

    finally:
        if should_cleanup:
            pub.close()
            sub.close()
