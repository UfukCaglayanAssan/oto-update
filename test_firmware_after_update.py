#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset Sonrası Firmware Test Scripti
Güncelleme sonrası yeni firmware'in çalışıp çalışmadığını kontrol eder
"""

import serial
import serial.tools.list_ports
import sys
import time

BAUD_RATE = 115200
TIMEOUT = 2

def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Reset Sonrası Firmware Test Scripti")
        print("=" * 60)
        print()
        print("Kullanım:")
        print("  python3 test_firmware_after_update.py <port>")
        print()
        print("Örnek:")
        print("  python3 test_firmware_after_update.py /dev/ttyACM0")
        print()
        print("Bu script:")
        print("  1. Port'u açar")
        print("  2. Reset sonrası UART mesajlarını dinler")
        print("  3. Yeni firmware'den mesaj gelip gelmediğini kontrol eder")
        print()
        sys.exit(1)
    
    port_name = sys.argv[1]
    
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=TIMEOUT,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        print("=" * 60)
        print("Reset Sonrası Firmware Test")
        print("=" * 60)
        print(f"Port: {port_name}")
        print(f"Baud Rate: {BAUD_RATE}")
        print()
        print("⚠ ÖNEMLİ: Kartı RESET yapın (NRESET butonuna basın)")
        print("Reset sonrası gelen tüm mesajlar burada görünecek...")
        print()
        print("Çıkmak için Ctrl+C tuşlarına basın")
        print("-" * 60)
        
        # Buffer'ları temizle
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.1)
        
        message_count = 0
        start_time = time.time()
        
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                message_count += 1
                elapsed = time.time() - start_time
                
                # Hex göster
                hex_str = ' '.join([f'{b:02X}' for b in data])
                
                # ASCII göster (printable karakterler)
                ascii_str = ''.join([chr(b) if 32 <= b < 127 else '.' for b in data])
                
                print(f"[{elapsed:.2f}s] Mesaj #{message_count}")
                print(f"  Byte Sayısı: {len(data)}")
                print(f"  Hex: {hex_str[:100]}{'...' if len(hex_str) > 100 else ''}")
                print(f"  ASCII: {ascii_str[:100]}{'...' if len(ascii_str) > 100 else ''}")
                print()
                
                # Eğer "CPU @ 64000000Hz" gibi bir mesaj gelirse, eski firmware çalışıyor
                if b"CPU @ 64000000Hz" in data or b"Bootloader NOT Used" in data:
                    print("⚠ UYARI: Eski firmware mesajları görünüyor!")
                    print("   → Yeni firmware çalışmıyor olabilir")
                    print("   → Flash yazma başarısız olmuş olabilir")
                    print()
                
                # Eğer LED yanıp sönüyorsa, firmware çalışıyor demektir
                # Ama bunu UART'tan anlayamayız, kullanıcı manuel kontrol etmeli
                
            else:
                time.sleep(0.1)
                
                # 10 saniye sonra özet göster
                elapsed = time.time() - start_time
                if elapsed > 10.0 and message_count == 0:
                    print(f"[{elapsed:.1f}s] Henüz mesaj gelmedi...")
                    print("   → Kartı reset yapın")
                    print("   → Veya yeni firmware UART mesajı göndermiyor olabilir")
                    print()
                    start_time = time.time()  # Reset timer
                    
    except KeyboardInterrupt:
        print()
        print("-" * 60)
        print("Test sonlandırıldı")
        print(f"Toplam mesaj sayısı: {message_count}")
        print()
        print("SONUÇ:")
        if message_count == 0:
            print("  ⚠ Hiç mesaj gelmedi")
            print("  → Yeni firmware UART mesajı göndermiyor olabilir")
            print("  → Veya firmware çalışmıyor")
        else:
            print(f"  ✓ {message_count} mesaj alındı")
            print("  → Firmware çalışıyor gibi görünüyor")
            print("  → LED'in yanıp söndüğünü manuel kontrol edin")
        print()
    except Exception as e:
        print(f"✗ Hata: {e}")
    finally:
        if ser.is_open:
            ser.close()
            print("Port kapatıldı")

if __name__ == "__main__":
    main()
