#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UART Dinleme Scripti - Sadece gelen verileri yazdırır, paket göndermez
Reset sonrası bootloader'dan gelen verileri dinlemek için
"""

import serial
import serial.tools.list_ports
import sys
import time

# UART ayarları
BAUD_RATE = 115200  # İhtiyaca göre değiştirilebilir
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

def listen_uart(ser):
    """UART'tan gelen verileri dinler ve yazdırır"""
    print("\n" + "=" * 60)
    print("UART Dinleme Başlatıldı")
    print("=" * 60)
    print("\nKartı resetleyin (NRESET butonuna basın)")
    print("Reset sonrası gelen tüm veriler burada görünecek...")
    print("\nÇıkmak için Ctrl+C tuşlarına basın\n")
    print("-" * 60)
    
    # Buffer'ı temizle
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.1)
    
    packet_count = 0
    total_bytes = 0
    start_time = time.time()
    
    try:
        while True:
            if ser.in_waiting > 0:
                # Byte olarak oku
                data = ser.read(ser.in_waiting)
                total_bytes += len(data)
                packet_count += 1
                
                # Zaman damgası
                elapsed = time.time() - start_time
                timestamp = f"[{elapsed:6.2f}s]"
                
                # Veriyi yazdır
                print(f"\n{timestamp} Paket #{packet_count}")
                print(f"  Byte Sayısı: {len(data)}")
                print(f"  Hex: {data.hex()}")
                
                # ASCII olarak yazdır (yazdırılabilir karakterler)
                try:
                    ascii_str = ''.join([chr(b) if 32 <= b < 127 else '.' for b in data])
                    print(f"  ASCII: {ascii_str}")
                except:
                    print(f"  ASCII: (yazdırılamıyor)")
                
                # Her byte'ı ayrı ayrı göster (opsiyonel)
                if len(data) <= 16:  # Kısa paketler için
                    byte_list = ' '.join([f'{b:02X}' for b in data])
                    print(f"  Bytes: {byte_list}")
                
                print("-" * 60)
            
            # Kısa bir bekleme (CPU kullanımını azaltmak için)
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Dinleme durduruldu")
        print("=" * 60)
        print(f"Toplam paket sayısı: {packet_count}")
        print(f"Toplam byte sayısı: {total_bytes}")
        print(f"Toplam süre: {time.time() - start_time:.2f} saniye")
    except Exception as e:
        print(f"\nHata oluştu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ser.close()
        print("\nPort kapatıldı.")

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("UART Dinleme Aracı")
    print("Reset sonrası bootloader'dan gelen verileri dinler")
    print("=" * 60)
    print()
    
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
    
    print()
    
    # Serial port'u aç
    ser = open_serial_port(port_name, BAUD_RATE)
    
    # Port ayarlarını göster
    print(f"Baud Rate: {ser.baudrate}")
    print(f"Data Bits: {ser.bytesize}")
    print(f"Parity: {ser.parity}")
    print(f"Stop Bits: {ser.stopbits}")
    print(f"Port açık: {ser.is_open}")
    print()
    
    # UART'ı dinlemeye başla
    listen_uart(ser)

if __name__ == "__main__":
    main()


