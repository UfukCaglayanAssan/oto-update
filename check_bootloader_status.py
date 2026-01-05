#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bootloader durumunu kontrol eder - takılma durumunda kullanılır
"""

import serial
import serial.tools.list_ports
import sys
import time

BAUD_RATE = 115200
MAX_PKT_SIZE = 64

def open_serial_port(port_name):
    """Serial port'u acar"""
    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=BAUD_RATE,
            bytesize=8,
            parity=serial.PARITY_NONE,
            stopbits=1,
            timeout=1.0,
            write_timeout=2.0,
            rtscts=False,
            dsrdtr=False,
            xonxoff=False
        )
        ser.setDTR(False)
        ser.setRTS(False)
        print(f"Port acildi: {port_name}")
        return ser
    except Exception as e:
        print(f"Hata: Port acilamadi - {e}")
        return None

def check_bootloader_status(ser):
    """Bootloader'in durumunu kontrol eder"""
    print("\n" + "="*60)
    print("Bootloader Durum Kontrolu")
    print("="*60)
    
    # Buffer durumu
    print(f"\nBuffer Durumu:")
    print(f"  Input buffer: {ser.in_waiting} byte")
    print(f"  Output buffer: {ser.out_waiting} byte")
    
    # Buffer'da veri var mi?
    if ser.in_waiting > 0:
        print(f"\n  [!] Input buffer'da {ser.in_waiting} byte veri var!")
        print(f"  Veriyi okuyoruz...")
        data = ser.read(ser.in_waiting)
        print(f"  Veri (ilk 100 byte): {data.hex()[:200]}")
        
        # ASCII olarak dene
        try:
            ascii_text = data.decode('ascii', errors='ignore')
            if ascii_text.strip():
                print(f"  ASCII: {ascii_text[:100]}")
        except:
            pass
    
    # CMD_CONNECT gonder ve yanit bekle
    print(f"\nCMD_CONNECT gonderiliyor...")
    connect_packet = bytearray(64)
    connect_packet[0:4] = (0x000000AE).to_bytes(4, byteorder='little')  # CMD_CONNECT
    
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(connect_packet)
        ser.flush()
        print(f"  CMD_CONNECT gonderildi")
        
        # Yanit bekle (2 saniye)
        time.sleep(0.2)
        if ser.in_waiting >= 64:
            response = ser.read(64)
            print(f"  [OK] Yanit alindi!")
            print(f"  Yanit (ilk 16 byte): {response[:16].hex()}")
            
            # Paket numarasi
            packet_no = response[4] | (response[5] << 8)
            print(f"  Paket No: {packet_no}")
            
            # APROM size
            aprom_size = (response[8] | (response[9] << 8) | (response[10] << 16) | (response[11] << 24))
            print(f"  APROM Size: {aprom_size} byte (0x{aprom_size:08X})")
            
            return True
        else:
            print(f"  [!] Yanit yok (beklenen: 64 byte, mevcut: {ser.in_waiting} byte)")
            return False
    except Exception as e:
        print(f"  [X] Hata: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python3 check_bootloader_status.py <port>")
        print("Ornek: python3 check_bootloader_status.py /dev/ttyACM0")
        sys.exit(1)
    
    port_name = sys.argv[1]
    ser = open_serial_port(port_name)
    
    if ser:
        try:
            check_bootloader_status(ser)
        except KeyboardInterrupt:
            print("\nIptal edildi.")
        finally:
            ser.close()
            print("\nPort kapatildi.")




