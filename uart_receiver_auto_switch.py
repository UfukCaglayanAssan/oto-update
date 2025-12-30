#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton ISP Bootloader - Otomatik Geçiş
Application başladıktan sonra bootloader'a geçiş yapar
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

# Bootloader'a geçiş komutu (application kodunda tanımlı olmalı)
CMD_SWITCH_TO_BOOTLOADER = 0x42

# Nuvoton ISP Komutları
CMD_CONNECT = 0x000000AE
CMD_UPDATE_APROM = 0x000000A0

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
    packet[4:8] = uint32_to_bytes(param1)
    if param2 != 0:
        packet[8:12] = uint32_to_bytes(param2)
    if data:
        data_len = min(len(data), 56)
        packet[8:8+data_len] = data[:data_len]
    return packet

def send_packet(ser, packet):
    """64 byte paketi gönderir"""
    if len(packet) != MAX_PKT_SIZE:
        return False
    
    try:
        if not ser.writable():
            return False
        
        if ser.out_waiting > 100:
            ser.reset_output_buffer()
            time.sleep(0.1)
        
        ser.reset_output_buffer()
        time.sleep(0.05)
        
        # Byte-byte gönder
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
            if time.time() - start_time > 1.0:
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

def wait_for_application(ser, timeout=5.0):
    """Application başladığını bekler (UART mesajı gelene kadar)"""
    print("Application başlamasını bekliyoruz...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            # Application mesajı geldi
            print(f"✓ Application başladı (mesaj: {data[:50].decode('ascii', errors='ignore')})")
            time.sleep(0.5)  # Application'ın tam başlaması için bekle
            return True
        time.sleep(0.1)
    
    print("⚠ Application mesajı gelmedi, devam ediliyor...")
    return False

def send_bootloader_switch(ser):
    """Application'a bootloader'a geçiş komutu gönderir"""
    print("Application'a bootloader'a geçiş komutu gönderiliyor...")
    
    # Özel komut gönder (application kodunda tanımlı olmalı)
    switch_cmd = bytes([CMD_SWITCH_TO_BOOTLOADER])
    
    try:
        ser.reset_output_buffer()
        bytes_written = ser.write(switch_cmd)
        ser.flush()
        
        if bytes_written > 0:
            print(f"✓ Geçiş komutu gönderildi")
            time.sleep(0.5)  # Application'ın bootloader'a geçmesi için bekle
            return True
        else:
            print("✗ Geçiş komutu gönderilemedi")
            return False
    except Exception as e:
        print(f"✗ Hata: {e}")
        return False

def send_connect(ser):
    """CMD_CONNECT gönderir ve yanıt alır"""
    print("CMD_CONNECT gönderiliyor...")
    
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.01)
    except:
        pass
    
    packet = create_packet(CMD_CONNECT)
    
    if not send_packet(ser, packet):
        return False
    
    print(f"✓ CMD_CONNECT gönderildi")
    time.sleep(0.05)
    
    print("Yanıt bekleniyor (0.3 saniye)...")
    response = receive_response(ser, timeout=0.3)
    
    if response:
        first_bytes = response[:4]
        is_ascii = all(32 <= b <= 126 for b in first_bytes[:4])
        
        if is_ascii:
            print(f"⚠ Application yanıtı (bootloader değil)")
            return False
        
        checksum = (response[1] << 8) | response[0]
        packet_no = bytes_to_uint32(response, 4)
        aprom_size = bytes_to_uint32(response, 8)
        dataflash_addr = bytes_to_uint32(response, 12)
        
        print(f"✓✓✓ BOOTLOADER YANITI ALINDI! ✓✓✓")
        print(f"  APROM Boyutu: {aprom_size} byte")
        return True
    else:
        return False

def main():
    print("=" * 60)
    print("Nuvoton ISP Bootloader - Otomatik Geçiş")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Kullanım: python3 uart_receiver_auto_switch.py <port> <bin_file>")
        sys.exit(1)
    
    port_name = sys.argv[1]
    bin_file = sys.argv[2] if len(sys.argv) > 2 else "NuvotonM26x-Bootloader-Test.bin"
    
    # Binary dosyayı oku
    if not os.path.exists(bin_file):
        print(f"✗ HATA: Dosya bulunamadı: {bin_file}")
        sys.exit(1)
    
    with open(bin_file, 'rb') as f:
        bin_data = f.read()
    
    print(f"✓ Binary dosya okundu: {len(bin_data)} byte")
    
    # Port'u aç
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        print(f"✓ Port açıldı: {port_name}")
    except Exception as e:
        print(f"✗ Port açılamadı: {e}")
        sys.exit(1)
    
    try:
        # 1. Application başlamasını bekle
        wait_for_application(ser, timeout=10.0)
        
        # 2. Application'a bootloader'a geçiş komutu gönder
        if not send_bootloader_switch(ser):
            print("✗ Bootloader'a geçiş başarısız")
            return
        
        # 3. Bootloader'ı yakala
        print("\nBootloader'ı yakalamaya çalışıyoruz...")
        for i in range(10):
            if send_connect(ser):
                print("✓✓✓ Bootloader yakalandı! ✓✓✓\n")
                break
            time.sleep(0.1)
        else:
            print("✗ Bootloader yakalanamadı")
            return
        
        # 4. Güncelleme yap (mevcut kodunuzu kullanın)
        print("Güncelleme başlatılıyor...")
        # ... güncelleme kodunuz ...
        
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırılıyor...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()

