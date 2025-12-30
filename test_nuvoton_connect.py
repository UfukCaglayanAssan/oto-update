#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton CMD_CONNECT test scripti
Port'un çalışıp çalışmadığını test eder
"""

import serial
import serial.tools.list_ports
import sys
import time

BAUD_RATE = 115200
CMD_CONNECT = 0x000000AE

def uint32_to_bytes(value):
    """uint32_t değerini little-endian byte array'e çevirir"""
    return bytes([
        (value >> 0) & 0xFF,
        (value >> 8) & 0xFF,
        (value >> 16) & 0xFF,
        (value >> 24) & 0xFF
    ])

def main():
    print("=" * 60)
    print("Nuvoton CMD_CONNECT Test")
    print("=" * 60)
    
    # Port belirle
    if len(sys.argv) > 1:
        port_name = sys.argv[1]
    else:
        # Otomatik tespit
        ports = serial.tools.list_ports.comports()
        print("Mevcut Serial Portlar:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")
        
        if not ports:
            print("✗ Port bulunamadı!")
            return
        
        port_name = ports[0].device
        print(f"\nOtomatik seçilen port: {port_name}")
    
    print(f"\nPort açılıyor: {port_name}")
    
    try:
        # Port'u aç
        ser = serial.Serial(port_name, BAUD_RATE, timeout=2, write_timeout=5,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        
        print(f"✓ Port açıldı")
        print(f"  Baud Rate: {ser.baudrate}")
        print(f"  Port açık: {ser.is_open}")
        print(f"  Port yazılabilir: {ser.writable()}")
        print(f"  Port okunabilir: {ser.readable()}")
        
        # Buffer temizle
        print(f"\nBuffer temizleniyor...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.3)
        
        print(f"  Output buffer: {ser.out_waiting} byte")
        print(f"  Input buffer: {ser.in_waiting} byte")
        
        # CMD_CONNECT paketi oluştur (64 byte)
        packet = bytearray(64)
        packet[0:4] = uint32_to_bytes(CMD_CONNECT)
        # Geri kalanı 0x00
        
        print(f"\nCMD_CONNECT paketi hazırlanıyor...")
        print(f"  Paket boyutu: {len(packet)} byte")
        print(f"  Paket hex (ilk 16 byte): {packet[:16].hex()}")
        
        # Paketi gönder (küçük parçalar halinde)
        print(f"\nPaket gönderiliyor...")
        chunk_size = 16
        total_written = 0
        
        for i in range(0, len(packet), chunk_size):
            chunk = packet[i:i+chunk_size]
            try:
                bytes_written = ser.write(chunk)
                total_written += bytes_written
                ser.flush()
                time.sleep(0.001)
                print(f"  Chunk {i//chunk_size + 1}: {bytes_written} byte yazıldı")
            except serial.SerialTimeoutException as e:
                print(f"  ✗ Chunk {i//chunk_size + 1} timeout: {e}")
                return
            except Exception as e:
                print(f"  ✗ Chunk {i//chunk_size + 1} hatası: {e}")
                return
        
        print(f"✓ Toplam {total_written}/{len(packet)} byte yazıldı")
        
        # Flush bekle
        print(f"\nFlush bekleniyor...")
        start_time = time.time()
        while ser.out_waiting > 0:
            if time.time() - start_time > 2.0:
                print(f"  ⚠ Flush timeout, kalan: {ser.out_waiting} byte")
                break
            time.sleep(0.01)
        
        ser.flush()
        print(f"✓ Flush tamamlandı")
        
        # Yanıt bekle
        print(f"\nYanıt bekleniyor (1 saniye)...")
        time.sleep(0.1)
        
        if ser.in_waiting > 0:
            response = ser.read(min(ser.in_waiting, 64))
            print(f"✓✓✓ YANIT ALINDI! ✓✓✓")
            print(f"  Byte sayısı: {len(response)}")
            print(f"  Hex: {response.hex()}")
            print(f"  Hex (ilk 32 byte): {response[:32].hex()}")
        else:
            print(f"✗ Yanıt alınamadı")
            print(f"  Input buffer: {ser.in_waiting} byte")
        
        ser.close()
        print(f"\n✓ Test tamamlandı")
        
    except serial.SerialTimeoutException as e:
        print(f"\n✗ TIMEOUT: {e}")
        print(f"  → Port yazma işlemi zaman aşımına uğradı")
        print(f"  → Port başka program tarafından kullanılıyor olabilir")
        print(f"  → Port donmuş olabilir, yeniden bağlanmayı deneyin")
    except serial.SerialException as e:
        print(f"\n✗ SERIAL HATASI: {e}")
        print(f"  → Port açılamadı veya erişilemiyor")
    except Exception as e:
        print(f"\n✗ HATA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

