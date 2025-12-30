#!/usr/bin/env python3
import serial.tools.list_ports
import os

print("=== PORT KONTROL ===")
print()

# PySerial ile portları bul
ports = serial.tools.list_ports.comports()
if ports:
    print("PySerial ile bulunan portlar:")
    for p in ports:
        print(f"  ✓ {p.device} - {p.description}")
else:
    print("✗ PySerial ile port bulunamadı")

print()

# /dev/tty* dosyalarını kontrol et
print("Sistem portları (/dev/tty*):")
common = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyAMA0']
found = []
for p in common:
    if os.path.exists(p):
        found.append(p)
        print(f"  ✓ {p} - MEVCUT")
    else:
        print(f"  ✗ {p} - YOK")

print()
if found:
    print(f"ÖNERİLEN: {found[0]}")
else:
    print("⚠️  Port bulunamadı!")
    print("Kontrol:")
    print("  1. USB kablosu bağlı mı?")
    print("  2. lsusb komutu ile USB cihazları kontrol edin")

