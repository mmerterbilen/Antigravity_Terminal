#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Masaüstü Başlatıcı Oluşturucu
(Desktop Launcher Generator)
"""

import os
import sys


def create_desktop_launcher() -> str:
    """Kullanıcının masaüstüne Antigravity_Terminal.bat başlatıcısı oluşturur."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    desktop_dir = os.path.expanduser("~\\Desktop")
    bat_path = os.path.join(desktop_dir, "Antigravity_Terminal.bat")

    bat_content = f"""@echo off
cd /d "{project_dir}"
call .\\venv\\Scripts\\python main_ui.py
"""

    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    success_msg = "[BİLGİ] Masaüstü kısayolu başarıyla oluşturuldu! Artık Antigravity_Terminal.bat dosyasına çift tıklayarak sistemi başlatabilirsiniz."
    print(success_msg)
    return bat_path


if __name__ == "__main__":
    create_desktop_launcher()
