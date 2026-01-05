#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dosyadaki tüm encoding sorunlarını düzeltir"""

filename = 'uart_receiver_nuvoton.py'

# Dosyayı binary modda oku
with open(filename, 'rb') as f:
    data = f.read()

# Görünmeyen karakterleri temizle
cleaned = data.replace(b'\xc2\xa0', b' ')  # UTF-8 non-breaking space
cleaned = cleaned.replace(b'\xa0', b' ')     # Latin-1 non-breaking space

# Emoji karakterlerini temizle (UTF-8)
# ⚠️ = U+26A0 U+FE0F
cleaned = cleaned.replace(b'\xe2\x9a\xa0\xef\xb8\x8f', b'[!]')  # ⚠️
cleaned = cleaned.replace(b'\xe2\x9a\xa0', b'[!]')  # ⚠
# 🔄 = U+1F504
cleaned = cleaned.replace(b'\xf0\x9f\x94\x84', b'[>]')  # 🔄
# ✓ = U+2713
cleaned = cleaned.replace(b'\xe2\x9c\x93', b'[OK]')  # ✓
# ✗ = U+2717
cleaned = cleaned.replace(b'\xe2\x9c\x97', b'[X]')  # ✗

# Dosyayı UTF-8 olarak yaz
try:
    # Önce UTF-8 olarak decode et, sonra encode et
    text = cleaned.decode('utf-8', errors='ignore')
    # Türkçe karakterleri ASCII'ye çevir
    replacements = {
        'ç': 'c', 'Ç': 'C',
        'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'İ': 'I',
        'ö': 'o', 'Ö': 'O',
        'ş': 's', 'Ş': 'S',
        'ü': 'u', 'Ü': 'U',
        '⚠️': '[!]', '⚠': '[!]',
        '🔄': '[>]',
        '✓': '[OK]', '✗': '[X]'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # UTF-8 olarak yaz
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"✓ {filename} temizlendi ve UTF-8 olarak kaydedildi")
except Exception as e:
    print(f"Hata: {e}")
    # Fallback: binary olarak yaz
    with open(filename, 'wb') as f:
        f.write(cleaned)
    print(f"✓ {filename} temizlendi (binary mod)")




