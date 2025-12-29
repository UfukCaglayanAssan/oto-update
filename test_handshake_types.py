#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handshake Test Scripti - Farklı handshake türlerini test eder
Reset sonrası bootloader'a farklı komutlar gönderip yanıtları kontrol eder
"""

import serial
import serial.tools.list_ports
import sys
import time

# UART ayarları
BAUD_RATE = 115200
TIMEOUT = 2

def open_serial_port(port_name=None, baud_rate=BAUD_RATE):
    """Serial port'u açar"""
    try:
        if port_name is None:
            common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyAMA0', '/dev/ttyS0', '/dev/ttyACM0', '/dev/ttyACM1']
            for port in common_ports:
                try:
                    ser = serial.Serial(port, baud_rate, timeout=TIMEOUT,
                                      rtscts=False, dsrdtr=False, xonxoff=False)
                    print(f"Port açıldı: {port}")
                    return ser
                except serial.SerialException:
                    continue
            raise serial.SerialException("Uygun port bulunamadı")
        else:
            ser = serial.Serial(port_name, baud_rate, timeout=TIMEOUT,
                              rtscts=False, dsrdtr=False, xonxoff=False)
            print(f"Port açıldı: {port_name}")
            return ser
    except serial.SerialException as e:
        print(f"Hata: Port açılamadı - {e}")
        sys.exit(1)

def test_handshake(ser, handshake_name, handshake_data, wait_time=0.3):
    """Tek bir handshake türünü test eder"""
    print(f"\n{'='*60}")
    print(f"Test: {handshake_name}")
    print(f"Gönderilen: {handshake_data.hex()} ({len(handshake_data)} byte)")
    print(f"{'='*60}")
    
    # Buffer temizle (hızlı)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.05)  # Çok kısa bekleme
    
    try:
        # Handshake gönder
        bytes_written = ser.write(handshake_data)
        ser.flush()
        print(f"✓ {bytes_written} byte gönderildi")
        
        # Yanıt bekle (kısa süre)
        print(f"Yanıt bekleniyor ({wait_time} saniye)...")
        time.sleep(wait_time)
        
        # Yanıt kontrolü
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"\n✓✓✓ YANIT ALINDI! ✓✓✓")
            print(f"  Byte Sayısı: {len(response)}")
            print(f"  Hex: {response.hex()}")
            
            # ASCII göster
            try:
                ascii_str = ''.join([chr(b) if 32 <= b < 127 else '.' for b in response])
                print(f"  ASCII: {ascii_str}")
            except:
                pass
            
            # Her byte'ı göster
            byte_list = ' '.join([f'{b:02X}' for b in response])
            print(f"  Bytes: {byte_list}")
            
            return True, response
        else:
            print(f"\n✗ YANIT YOK")
            return False, None
            
    except Exception as e:
        print(f"\n✗ HATA: {e}")
        return False, None

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("Handshake Test Aracı")
    print("Farklı handshake türlerini test eder")
    print("=" * 60)
    print()
    
    # Port seçimi
    port_name = None
    if len(sys.argv) > 1:
        port_name = sys.argv[1]
        print(f"Belirtilen port: {port_name}")
    else:
        ports = serial.tools.list_ports.comports()
        print("Mevcut portlar:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")
        print("\nPort belirtilmedi, otomatik tespit edilecek...")
    
    print()
    
    # Port'u aç
    ser = open_serial_port(port_name, BAUD_RATE)
    print(f"Baud Rate: {ser.baudrate}")
    print()
    
    print("\n" + "=" * 60)
    print("HAZIR!")
    print("=" * 60)
    print("\n⚠️ ÖNEMLİ: Reset sonrası bootloader sadece 1-2 saniye modda kalır!")
    print("\nKartı resetleyin (NRESET butonuna basın)")
    print("Reset sonrası HEMEN testler başlayacak...")
    print("\n3 saniye sonra testler başlayacak...")
    print("(Reset butonuna basmaya hazır olun!)")
    for i in range(3, 0, -1):
        print(f"  {i}...", end='\r')
        time.sleep(1)
    print("\n\n⚡ RESET BUTONUNA BASIN VE HEMEN BIRAKIN! ⚡")
    time.sleep(0.5)  # Reset için kısa bekleme
    print("Testler başlıyor...\n")
    
    # Test edilecek handshake türleri
    handshake_tests = [
        # (İsim, Handshake verisi)
        ("Standart Handshake (0x55 0x5A)", bytes([0x55, 0x5A])),
        ("Bootloader Enter (0x55)", bytes([0x55])),
        ("Start Update (0x5A)", bytes([0x5A])),
        ("ACK (0xAA)", bytes([0xAA])),
        ("Alternatif 1 (0xAA 0x55)", bytes([0xAA, 0x55])),
        ("Alternatif 2 (0x5A 0x55)", bytes([0x5A, 0x55])),
        ("Nuvoton ISP Enter (0x7F)", bytes([0x7F])),
        ("ISP Command (0x01)", bytes([0x01])),
        ("ISP Command (0x02)", bytes([0x02])),
        ("ISP Command (0x03)", bytes([0x03])),
        ("ISP Sync (0x55 0xAA)", bytes([0x55, 0xAA])),
        ("ISP Sync (0xAA 0x55)", bytes([0xAA, 0x55])),
        ("ISP Sync (0x5A 0xA5)", bytes([0x5A, 0xA5])),
        ("ISP Sync (0xA5 0x5A)", bytes([0xA5, 0x5A])),
        ("UART Sync (0x55 0x55)", bytes([0x55, 0x55])),
        ("UART Sync (0xAA 0xAA)", bytes([0xAA, 0xAA])),
        ("Bootloader Request (0x42)", bytes([0x42])),  # 'B' for Bootloader
        ("Bootloader Request (0x42 0x4C)", bytes([0x42, 0x4C])),  # 'BL'
        ("Enter ISP (0x49 0x53 0x50)", bytes([0x49, 0x53, 0x50])),  # 'ISP'
        ("Enter Bootloader (0x42 0x4F 0x4F 0x54)", bytes([0x42, 0x4F, 0x4F, 0x54])),  # 'BOOT'
    ]
    
    # Sonuçları sakla
    results = []
    successful_tests = []
    
    # Her handshake'i test et (HIZLI - reset sonrası 1-2 saniye içinde)
    start_test_time = time.time()
    for i, (name, data) in enumerate(handshake_tests, 1):
        elapsed = time.time() - start_test_time
        if elapsed > 2.0:  # 2 saniyeyi geçtiyse uyar
            print(f"\n⚠️ UYARI: {elapsed:.2f} saniye geçti, bootloader modundan çıkmış olabilir!")
            print("   Yeni bir reset yapın ve tekrar deneyin.")
            break
        
        print(f"\n[{i}/{len(handshake_tests)}] Test ediliyor... (Geçen süre: {elapsed:.2f}s)")
        success, response = test_handshake(ser, name, data, wait_time=0.2)  # Çok kısa bekleme
        
        results.append({
            'name': name,
            'data': data,
            'success': success,
            'response': response
        })
        
        if success:
            successful_tests.append((name, response))
        
        # Testler arası çok kısa bekleme (hız için)
        time.sleep(0.05)  # 50ms
    
    # Özet
    print("\n" + "=" * 60)
    print("TEST ÖZETİ")
    print("=" * 60)
    print(f"Toplam test: {len(handshake_tests)}")
    print(f"Başarılı: {len(successful_tests)}")
    print(f"Başarısız: {len(handshake_tests) - len(successful_tests)}")
    
    if successful_tests:
        print("\n✓✓✓ BAŞARILI TESTLER ✓✓✓")
        print("-" * 60)
        for name, response in successful_tests:
            print(f"\n{name}")
            print(f"  Yanıt: {response.hex()}")
            print(f"  Byte Sayısı: {len(response)}")
    else:
        print("\n✗ Hiçbir handshake yanıt vermedi")
        print("  → Bootloader modunda olmayabilir")
        print("  → Farklı bir protokol kullanıyor olabilir")
        print("  → Reset sonrası daha hızlı deneyin")
    
    # Detaylı sonuçlar
    print("\n" + "=" * 60)
    print("DETAYLI SONUÇLAR")
    print("=" * 60)
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"\n{status} {result['name']}")
        print(f"   Gönderilen: {result['data'].hex()}")
        if result['success']:
            print(f"   Yanıt: {result['response'].hex()}")
        else:
            print(f"   Yanıt: YOK")
    
    ser.close()
    print("\nPort kapatıldı.")

if __name__ == "__main__":
    main()

