#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Port durumu kontrol scripti
Port'un neden timeout verdiğini tespit eder
"""

import serial
import subprocess
import sys
import time
import os

def check_port_usage(port_name):
    """Port'u kullanan programları bulur"""
    print(f"\n{'='*60}")
    print(f"Port Kullanım Kontrolü: {port_name}")
    print(f"{'='*60}")
    
    try:
        # lsof komutu ile kontrol
        result = subprocess.run(['lsof', port_name], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout:
            print(f"⚠ Port kullanılıyor!")
            print(f"  {result.stdout}")
            return True
        else:
            print(f"✓ Port kullanılmıyor")
            return False
    except FileNotFoundError:
        print(f"⚠ lsof komutu bulunamadı, atlanıyor...")
        return False
    except Exception as e:
        print(f"⚠ Kontrol hatası: {e}")
        return False

def check_port_exists(port_name):
    """Port'un var olup olmadığını kontrol eder"""
    print(f"\n{'='*60}")
    print(f"Port Varlık Kontrolü: {port_name}")
    print(f"{'='*60}")
    
    if os.path.exists(port_name):
        print(f"✓ Port dosyası mevcut")
        
        # İzinleri kontrol et
        if os.access(port_name, os.R_OK):
            print(f"✓ Port okunabilir")
        else:
            print(f"✗ Port okunamıyor (izin yok)")
        
        if os.access(port_name, os.W_OK):
            print(f"✓ Port yazılabilir")
        else:
            print(f"✗ Port yazılamıyor (izin yok)")
        
        return True
    else:
        print(f"✗ Port dosyası mevcut değil!")
        return False

def test_port_basic(port_name):
    """Temel port testi"""
    print(f"\n{'='*60}")
    print(f"Temel Port Testi: {port_name}")
    print(f"{'='*60}")
    
    try:
        # Port'u aç
        print(f"Port açılıyor...")
        ser = serial.Serial(port_name, 115200, timeout=1, write_timeout=1,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        
        print(f"✓ Port açıldı")
        print(f"  Baud Rate: {ser.baudrate}")
        print(f"  Port açık: {ser.is_open}")
        print(f"  Port yazılabilir: {ser.writable()}")
        print(f"  Port okunabilir: {ser.readable()}")
        print(f"  Output buffer: {ser.out_waiting} byte")
        print(f"  Input buffer: {ser.in_waiting} byte")
        
        # Buffer temizle
        print(f"\nBuffer temizleniyor...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)
        
        # Tek byte yazma testi
        print(f"\nTek byte yazma testi...")
        test_byte = bytes([0x55])
        
        start_time = time.time()
        try:
            bytes_written = ser.write(test_byte)
            elapsed = time.time() - start_time
            print(f"  Yazma süresi: {elapsed:.3f} saniye")
            print(f"  Yazılan byte: {bytes_written}")
            
            if bytes_written == 0:
                print(f"  ✗ Hiç byte yazılamadı!")
            else:
                print(f"  ✓ {bytes_written} byte yazıldı")
            
            # Flush testi
            print(f"\nFlush testi...")
            start_time = time.time()
            ser.flush()
            elapsed = time.time() - start_time
            print(f"  Flush süresi: {elapsed:.3f} saniye")
            
            if elapsed > 0.5:
                print(f"  ⚠ Flush çok uzun sürdü (port donmuş olabilir)")
            else:
                print(f"  ✓ Flush başarılı")
            
        except serial.SerialTimeoutException as e:
            print(f"  ✗ TIMEOUT: {e}")
            print(f"  → Port yazma işlemi zaman aşımına uğradı")
            print(f"  → Port donmuş veya başka program kullanıyor")
        except Exception as e:
            print(f"  ✗ HATA: {e}")
        
        ser.close()
        print(f"\n✓ Test tamamlandı")
        
    except serial.SerialException as e:
        print(f"✗ Port açılamadı: {e}")
        return False
    except Exception as e:
        print(f"✗ HATA: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python3 port_check.py <port>")
        print("Örnek: python3 port_check.py /dev/ttyACM0")
        sys.exit(1)
    
    port_name = sys.argv[1]
    
    print("=" * 60)
    print("Port Durum Kontrolü")
    print("=" * 60)
    
    # 1. Port varlık kontrolü
    if not check_port_exists(port_name):
        print(f"\n✗ Port bulunamadı, çıkılıyor...")
        return
    
    # 2. Port kullanım kontrolü
    is_used = check_port_usage(port_name)
    if is_used:
        print(f"\n⚠ UYARI: Port başka bir program tarafından kullanılıyor!")
        print(f"  → O programı kapatın ve tekrar deneyin")
        print(f"  → Veya port'u yeniden bağlayın (USB çıkar-tak)")
    
    # 3. Temel port testi
    test_port_basic(port_name)
    
    print(f"\n{'='*60}")
    print(f"Kontrol Tamamlandı")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

