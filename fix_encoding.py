#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dosyadaki görünmeyen karakterleri temizler"""

import sys

if len(sys.argv) < 2:
    print("Kullanım: python3 fix_encoding.py <dosya>")
    sys.exit(1)

filename = sys.argv[1]

# Dosyayı oku
with open(filename, 'rb') as f:
    data = f.read()

# Görünmeyen karakterleri temizle (non-breaking space vb.)
# Sadece normal ASCII ve UTF-8 karakterleri koru
cleaned = data.replace(b'\xc2\xa0', b' ')  # Non-breaking space
cleaned = cleaned.replace(b'\xa0', b' ')   # Non-breaking space (latin-1)

# Dosyayı yaz
with open(filename, 'wb') as f:
    f.write(cleaned)

print(f"✓ {filename} temizlendi")

