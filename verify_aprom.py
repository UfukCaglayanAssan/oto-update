#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APROM Doğrulama Scripti
Yazılan firmware'in doğru yazıldığını kontrol eder
"""

import serial
import serial.tools.list_ports
import sys
import time
import os

BAUD_RATE = 115200
TIMEOUT = 2
WRITE_TIMEOUT = 5
MAX_PKT_SIZE = 64

# Nuvoton ISP Komutları
CMD_CONNECT = 0x000000AE
CMD_READ_CONFIG = 0x000000A2

def uint32_to_bytes(value):
    """uint32_t değerini little-endian byte array'e çevirir"""
    return bytes([
        (value >> 0) & 0xFF,
        (value >> 8) & 0xFF,
        (value >> 16) & 0xFF,
        (value >> 24) & 0xFF
    ])

def bytes_to_uint32(data, offset=0):
    """Byte array'den little-endian uint32_t okur"""
    return (data[offset + 0] << 0) | \
           (data[offset + 1] << 8) | \
           (data[offset + 2] << 16) | \
           (data[offset + 3] << 24)

def create_packet(cmd, param1=0, param2=0, data=None):
    """64 byte Nuvoton paketi oluşturur"""
    packet = bytearray(MAX_PKT_SIZE)
    packet[0:4] = uint32_to_bytes(cmd)
    if data:
        data_len = min(len(data), 56)
        packet[8:8+data_len] = data[:data_len]
    return packet

def send_packet(ser, packet):
    """64 byte paketi gönderir"""
    if len(packet) != MAX_PKT_SIZE:
        return False
    
    try:
        if not ser.is_open or not ser.writable():
            return False
        
        ser.reset_output_buffer()
        time.sleep(0.01)
        
        total_written = 0
        for i, byte_val in enumerate(packet):
            try:
                bytes_written = ser.write(bytes([byte_val]))
                if bytes_written > 0:
                    total_written += bytes_written
                if (i + 1) % 8 == 0:
                    ser.flush()
                    time.sleep(0.001)
            except:
                total_written += 1
        
        start_time = time.time()
        while ser.out_waiting > 0:
            if time.time() - start_time > 0.5:
                break
            time.sleep(0.01)
        ser.flush()
        
        return True
    except:
        return False

def receive_response(ser, timeout=1.0):
    """64 byte yanıt paketi alır"""
    start_time = time.time()
    response = bytearray()
    
    while len(response) < MAX_PKT_SIZE:
        if time.time() - start_time > timeout:
            return None
        if ser.in_waiting > 0:
            data = ser.read(min(ser.in_waiting, MAX_PKT_SIZE - len(response)))
            response.extend(data)
        time.sleep(0.01)
    
    return bytes(response)

def read_aprom_verify(ser, bin_file, start_addr=0x00000000, size=None):
    """APROM'u okuyup firmware ile karşılaştırır"""
    print("=" * 60)
    print("APROM Doğrulama")
    print("=" * 60)
    
    # Binary dosyayı oku
    if not os.path.exists(bin_file):
        print(f"✗ HATA: Dosya bulunamadı: {bin_file}")
        return False
    
    with open(bin_file, 'rb') as f:
        expected_data = f.read()
    
    if size is None:
        size = len(expected_data)
    else:
        size = min(size, len(expected_data))
    
    print(f"Beklenen firmware boyutu: {len(expected_data)} byte")
    print(f"Kontrol edilecek boyut: {size} byte")
    print(f"Başlangıç adresi: 0x{start_addr:08X}")
    print()
    
    # CMD_READ_CONFIG ile APROM'u okumak için özel komut gerekir
    # Nuvoton ISP protokolünde direkt APROM okuma komutu yok
    # Bu yüzden ISP Tool kullanılmalı
    
    print("⚠ NOT: Nuvoton ISP protokolünde direkt APROM okuma komutu yok!")
    print("⚠ ISP Tool ile APROM'u okuyup kontrol etmeniz gerekiyor.")
    print()
    print("Öneriler:")
    print("1. ISP Tool'u açın")
    print("2. APROM'u okuyun (Read tab)")
    print("3. Okunan veriyi kaydedin")
    print("4. Binary dosya ile karşılaştırın")
    print()
    print("Veya:")
    print("1. Reset sonrası UART mesajlarını kontrol edin")
    print("2. Yeni firmware'den mesaj geliyor mu bakın")
    
    return False

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python3 verify_aprom.py <port> [bin_file]")
        sys.exit(1)
    
    port_name = sys.argv[1]
    bin_file = sys.argv[2] if len(sys.argv) > 2 else "NuvotonM26x-Bootloader-Test.bin"
    
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        print(f"✓ Port açıldı: {port_name}")
    except Exception as e:
        print(f"✗ Port açılamadı: {e}")
        sys.exit(1)
    
    try:
        read_aprom_verify(ser, bin_file)
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırılıyor...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()

