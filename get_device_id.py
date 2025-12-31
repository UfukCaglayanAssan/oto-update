#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton Cihaz ID'si Alma Scripti
Basit bir script - sadece cihaz ID'sini alir ve gosterir
"""

import serial
import serial.tools.list_ports
import time
import sys

# Nuvoton ISP Komutlari
CMD_CONNECT = 0x000000AE
CMD_GET_DEVICEID = 0x000000B1
MAX_PKT_SIZE = 64

def uint32_to_bytes(value):
    """uint32_t degerini little-endian byte array'e cevirir"""
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

def create_packet(cmd):
    """64 byte Nuvoton paketi olusturur"""
    packet = bytearray(MAX_PKT_SIZE)
    packet[0:4] = uint32_to_bytes(cmd)
    return packet

def send_packet(ser, packet):
    """64 byte paketi gonderir"""
    try:
        ser.reset_output_buffer()
        ser.write(packet)
        ser.flush()
        return True
    except Exception as e:
        print(f"  Hata: Paket gonderilemedi - {e}")
        return False

def receive_response(ser):
    """64 byte yanit paketi alir (timeout yok - yanit gelene kadar bekliyor)"""
    response = bytearray()
    
    while len(response) < MAX_PKT_SIZE:
        if ser.in_waiting > 0:
            data = ser.read(min(ser.in_waiting, MAX_PKT_SIZE - len(response)))
            response.extend(data)
        else:
            time.sleep(0.01)
    
    return bytes(response)

def open_serial_port(port_name=None):
    """Serial port acar"""
    if port_name:
        ports = [port_name]
    else:
        # Otomatik port tespiti
        available_ports = serial.tools.list_ports.comports()
        ports = [p.device for p in available_ports]
        
        # Yaygin portlari kontrol et
        common_ports = ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyUSB1', 
                       '/dev/ttyAMA0', 'COM1', 'COM2', 'COM3', 'COM4']
        ports = common_ports + ports
    
    for port in ports:
        try:
            ser = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=2.0,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False
            )
            
            time.sleep(0.1)  # Port'un hazir olmasi icin bekle
            
            if ser.is_open:
                print(f"Port acildi: {port}")
                return ser, port
        except Exception as e:
            continue
    
    return None, None

def get_device_id(ser):
    """Cihaz ID'sini alir - otomatik bootloader yakalama ile"""
    print("\n" + "="*60)
    print("Cihaz ID'si Aliniyor...")
    print("="*60)
    print("\nONEMLI: Bootloader sadece reset sonrasi 300ms icinde aktif!")
    print("Script surekli CMD_CONNECT gonderecek, reset yapinca yakalayacak...")
    print("\nKarti RESET yapin (istediginiz zaman)")
    print("Script otomatik olarak bootloader'i yakalayacak...")
    print("Cikmak icin Ctrl+C tuslarina basin\n")
    
    # 1. Surekli CMD_CONNECT gonder (bootloader yakalama)
    connect_packet = create_packet(CMD_CONNECT)
    max_attempts = 5000
    attempt = 0
    connected = False
    
    print("[>] Surekli CMD_CONNECT gonderiliyor...")
    print("   (Reset yapinca bootloader yakalanacak)\n")
    
    while attempt < max_attempts and not connected:
        attempt += 1
        
        # Her 100 denemede bir bilgi ver
        if attempt % 100 == 0:
            print(f"  Deneme: {attempt}... (Reset yapin)")
        
        # Buffer temizle
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        except:
            pass
        
        # CMD_CONNECT gonder
        if send_packet(ser, connect_packet):
            # Kisa bekleme (bootloader'in yanit vermesi icin)
            time.sleep(0.005)  # 5ms
            
            # Yanit var mi kontrol et
            if ser.in_waiting >= 4:
                # En az 4 byte var, yanit gelmis olabilir
                time.sleep(0.05)  # Biraz daha bekle
                
                if ser.in_waiting >= 64:
                    # Tam yanit gelmis
                    connect_response = receive_response(ser)
                    
                    if connect_response and len(connect_response) >= 64:
                        # Yanitin bootloader'dan mi geldigini kontrol et
                        cmd_value = bytes_to_uint32(connect_response, 0)
                        
                        # Bootloader yaniti: Byte 0-3'te checksum var (genellikle 0x00AE veya benzeri)
                        # Application yaniti: ASCII metin
                        first_bytes = connect_response[:4]
                        is_ascii = all(32 <= b <= 126 for b in first_bytes[:4])
                        
                        if not is_ascii:
                            # Bootloader yaniti!
                            checksum = (connect_response[1] << 8) | connect_response[0]
                            packet_no = connect_response[4] | (connect_response[5] << 8)
                            
                            print(f"\n[OK][OK][OK] BOOTLOADER YAKALANDI! [OK][OK][OK]")
                            print(f"  Checksum: 0x{checksum:04X}")
                            print(f"  Paket No: {packet_no}")
                            connected = True
                            break
        
        # Cok kisa bekleme (hizli polling)
        time.sleep(0.005)  # 5ms
    
    if not connected:
        print(f"\n[X] Bootloader yakalanamadi ({max_attempts} deneme)")
        print("    - Karti reset yaptiniz mi?")
        print("    - Bootloader modunda mi?")
        print("    - Port dogru mu?")
        return None
    
    # 2. CMD_GET_DEVICEID gonder
    print("\n[2/2] CMD_GET_DEVICEID gonderiliyor...")
    device_packet = create_packet(CMD_GET_DEVICEID)
    
    if not send_packet(ser, device_packet):
        print("[X] CMD_GET_DEVICEID gonderilemedi")
        return None
    
    time.sleep(0.1)
    device_response = receive_response(ser)
    
    if not device_response or len(device_response) < 64:
        print("[X] CMD_GET_DEVICEID yaniti alinamadi")
        return None
    
    # Cihaz ID'sini parse et
    device_id = bytes_to_uint32(device_response, 8)  # Byte 8-11
    checksum = (device_response[1] << 8) | device_response[0]
    
    print("[OK] Cihaz ID yaniti alindi")
    print(f"\n{'='*60}")
    print(f"CIHAZ ID: 0x{device_id:08X}")
    print(f"Checksum: 0x{checksum:04X}")
    print(f"{'='*60}")
    
    return device_id

def main():
    """Ana fonksiyon"""
    print("="*60)
    print("Nuvoton Cihaz ID'si Alma Scripti")
    print("="*60)
    
    # Port secimi
    if len(sys.argv) > 1:
        port_name = sys.argv[1]
    else:
        port_name = None
        print("\nMevcut Serial Portlar:")
        ports = serial.tools.list_ports.comports()
        for p in ports:
            print(f"  - {p.device}: {p.description}")
        print("\nPort belirtilmedi, otomatik tespit edilecek...")
    
    # Port ac
    ser, port = open_serial_port(port_name)
    if not ser:
        print("[X] Port acilamadi!")
        print("\nKullanim:")
        print(f"  python3 {sys.argv[0]} <port>")
        print(f"  python3 {sys.argv[0]} /dev/ttyACM0")
        return
    
    try:
        # Buffer temizle
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.1)
        
        print(f"\nPort: {port}")
        print(f"Baud Rate: 115200")
        
        # Cihaz ID'sini al (otomatik bootloader yakalama ile)
        device_id = get_device_id(ser)
        
        if device_id:
            print(f"\n[OK] Cihaz ID'si basariyla alindi!")
            print(f"     Cihaz ID: 0x{device_id:08X}")
        else:
            print(f"\n[X] Cihaz ID'si alinamadi!")
            print(f"    - Karti reset yaptiniz mi?")
            print(f"    - Bootloader modunda mi?")
            print(f"    - Port dogru mu? ({port})")
    
    except KeyboardInterrupt:
        print("\n\nIptal edildi.")
    except Exception as e:
        print(f"\n[X] Hata: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("\nPort kapatildi.")

if __name__ == "__main__":
    main()

