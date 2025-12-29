#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timing Varyasyonları Testi
Reset sonrası farklı zamanlarda handshake gönderir
"""

import serial
import time
import sys

BAUD_RATE = 115200
TIMEOUT = 1

def open_serial_port(port_name):
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=TIMEOUT,
                           rtscts=False, dsrdtr=False, xonxoff=False)
        return ser
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
    
    print("=" * 60)
    print("Timing Varyasyonları Testi")
    print("=" * 60)
    print(f"\nPort: {port}")
    print("\nReset yapın, sonra testler başlayacak...")
    print("3 saniye sonra başlıyor...")
    for i in range(3, 0, -1):
        print(f"  {i}...", end='\r')
        time.sleep(1)
    print("\n\nTestler başlıyor...\n")
    
    ser = open_serial_port(port)
    handshake = bytes([0x55, 0x5A])
    
    # Farklı timing'ler
    delays = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0]
    
    for delay in delays:
        print(f"\n{'='*60}")
        print(f"Test: Reset sonrası {delay} saniye bekleyip gönderiyor...")
        print(f"{'='*60}")
        
        # Buffer temizle
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Belirtilen süre bekle
        time.sleep(delay)
        
        # Handshake gönder
        ser.write(handshake)
        ser.flush()
        print(f"✓ Handshake gönderildi: {handshake.hex()}")
        
        # Yanıt bekle
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"\n✓✓✓ YANIT ALINDI! ✓✓✓")
            print(f"  Timing: {delay} saniye")
            print(f"  Yanıt: {response.hex()}")
            print(f"  Byte Sayısı: {len(response)}")
            ser.close()
            return
        else:
            print(f"✗ Yanıt yok")
    
    print("\n" + "=" * 60)
    print("Hiçbir timing çalışmadı")
    print("=" * 60)
    print("\nMuhtemelen:")
    print("1. Bootloader güncelleme modunda değil")
    print("2. DIP switch ayarları yanlış")
    print("3. Özel bir aktivasyon gerekiyor")
    print("4. Farklı bir protokol kullanılıyor")
    
    ser.close()

if __name__ == "__main__":
    main()

