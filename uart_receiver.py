#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton işlemci ile UART üzerinden haberleşme scripti
Raspberry Pi'de çalışır ve gelen verileri print ile yazdırır
"""

import serial
import serial.tools.list_ports
import sys
import time

# UART ayarları
BAUD_RATE = 115200  # İhtiyaca göre değiştirilebilir (9600, 19200, 38400, 57600, 115200)
TIMEOUT = 1  # Okuma timeout'u (saniye)

def find_serial_ports():
    """Mevcut serial portları listeler"""
    ports = serial.tools.list_ports.comports()
    print("Mevcut Serial Portlar:")
    for port in ports:
        print(f"  - {port.device}: {port.description}")
    return ports

def open_serial_port(port_name=None, baud_rate=BAUD_RATE):
    """Serial port'u açar"""
    try:
        if port_name is None:
            # Raspberry Pi'de genellikle kullanılan portlar
            common_ports = ['/dev/ttyUSB0', '/dev/ttyAMA0', '/dev/ttyS0', '/dev/ttyACM0']
            for port in common_ports:
                try:
                    ser = serial.Serial(port, baud_rate, timeout=TIMEOUT)
                    print(f"Port açıldı: {port}")
                    return ser
                except serial.SerialException:
                    continue
            raise serial.SerialException("Uygun port bulunamadı")
        else:
            ser = serial.Serial(port_name, baud_rate, timeout=TIMEOUT)
            print(f"Port açıldı: {port_name}")
            return ser
    except serial.SerialException as e:
        print(f"Hata: Port açılamadı - {e}")
        sys.exit(1)

def read_uart_data(ser):
    """UART'tan veri okur ve yazdırır"""
    print("\nUART veri okuma başlatıldı...")
    print("Çıkmak için Ctrl+C tuşlarına basın\n")
    print("-" * 50)
    
    try:
        while True:
            if ser.in_waiting > 0:
                # Byte olarak oku
                data = ser.read(ser.in_waiting)
                
                # Hem hex hem de ASCII formatında göster
                print(f"Gelen Veri (Hex): {data.hex()}")
                print(f"Gelen Veri (ASCII): {data.decode('utf-8', errors='replace')}")
                print(f"Byte Sayısı: {len(data)}")
                print("-" * 50)
            
            time.sleep(0.01)  # CPU kullanımını azaltmak için kısa bekleme
            
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırılıyor...")
    except Exception as e:
        print(f"\nHata oluştu: {e}")
    finally:
        ser.close()
        print("Port kapatıldı.")

def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("Nuvoton UART Veri Alıcı")
    print("=" * 50)
    
    # Mevcut portları göster
    find_serial_ports()
    print()
    
    # Port adını komut satırından al (opsiyonel)
    port_name = None
    if len(sys.argv) > 1:
        port_name = sys.argv[1]
        print(f"Belirtilen port: {port_name}")
    else:
        print("Port belirtilmedi, otomatik tespit edilecek...")
    
    # Serial port'u aç
    ser = open_serial_port(port_name, BAUD_RATE)
    
    # Port ayarlarını göster
    print(f"Baud Rate: {ser.baudrate}")
    print(f"Data Bits: {ser.bytesize}")
    print(f"Parity: {ser.parity}")
    print(f"Stop Bits: {ser.stopbits}")
    print()
    
    # Veri okumaya başla
    read_uart_data(ser)

if __name__ == "__main__":
    main()

