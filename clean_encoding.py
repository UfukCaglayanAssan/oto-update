#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dosyadaki görünmeyen karakterleri temizler"""

filename = 'uart_receiver_nuvoton.py'

# Dosyayı binary modda oku
with open(filename, 'rb') as f:
    data = f.read()

# Görünmeyen karakterleri temizle
# Non-breaking space (U+00A0) -> normal space
cleaned = data.replace(b'\xc2\xa0', b' ')  # UTF-8 non-breaking space
cleaned = cleaned.replace(b'\xa0', b' ')    # Latin-1 non-breaking space

# Dosyayı yaz
with open(filename, 'wb') as f:
    f.write(cleaned)

print(f"✓ {filename} temizlendi")

