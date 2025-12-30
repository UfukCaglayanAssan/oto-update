#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serial Port Kontrol Scripti
Mevcut portları listeler ve test eder
"""

import serial.tools.list_ports
import sys
import os

def check_ports():
    """Mevcut serial portları bulur ve listeler"""
    print("=" * 60)
    print("Serial Port Kontrol")
    print("=" * 60)
    print()
    
    # Tüm portları listele
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("✗ Hiç serial port bulunamadı!")
        print()
        print("Kontrol edin:")
        print("  1. USB-UART dönüştürücü bağlı mı?")
        print("  2. USB kablosu çalışıyor mu?")
        print("  3. Driver yüklü mü?")
        return
    
    print(f"✓ {len(ports)} port bulundu:")
    print()
    
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device}")
        print(f"   Açıklama: {port.description}")
        print(f"   Üretici: {port.manufacturer or 'Bilinmiyor'}")
        print(f"   VID:PID: {port.vid:04X}:{port.pid:04X}" if port.vid and port.pid else "   VID:PID: Bilinmiyor")
        print()
    
    # /dev/tty* dosyalarını kontrol et
    print("=" * 60)
    print("Sistem Portları (/dev/tty*)")
    print("=" * 60)
    print()
    
    common_ports = [
        '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2',
        '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2',
        '/dev/ttyAMA0', '/dev/ttyS0', '/dev/ttyS1'
    ]
    
    found_ports = []
    for port_path in common_ports:
        if os.path.exists(port_path):
            found_ports.append(port_path)
            print(f"✓ {port_path} - MEVCUT")
        else:
            print(f"✗ {port_path} - YOK")
    
    print()
    
    if found_ports:
        print("=" * 60)
        print("ÖNERİLEN PORT:")
        print("=" * 60)
        print(f"  {found_ports[0]}")
        print()
        print("Kullanım:")
        print(f"  python3 uart_receiver_nuvoton.py {found_ports[0]} NuvotonM26x-Bootloader-Test.bin")
    else:
        print("⚠️  Hiçbir standart port bulunamadı!")
        print()
        print("Kontrol edin:")
        print("  1. USB-UART dönüştürücü bağlı mı?")
        print("  2. lsusb komutu ile USB cihazları kontrol edin:")
        print("     lsusb")
        print("  3. dmesg ile son USB bağlantılarını kontrol edin:")
        print("     dmesg | tail -20")

if __name__ == "__main__":
    check_ports()

