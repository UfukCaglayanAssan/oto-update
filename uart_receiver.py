#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton işlemci ile UART üzerinden haberleşme scripti
Raspberry Pi'de çalışır ve bootloader güncellemesi yapar
"""

import serial
import serial.tools.list_ports
import sys
import time
import os

# UART ayarları
BAUD_RATE = 115200  # İhtiyaca göre değiştirilebilir (9600, 19200, 38400, 57600, 115200)
TIMEOUT = 1  # Okuma timeout'u (saniye)
WAIT_TIME = 10  # Script başladıktan sonra bekleme süresi (saniye)
PACKET_SIZE = 256  # Her paketteki byte sayısı (ayarlanabilir: 64, 128, 256, 512)

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

def calculate_checksum(data):
    """Basit checksum hesaplama (byte toplamı)"""
    return sum(data) & 0xFF

def read_bin_file(file_path):
    """Binary dosyayı okur"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
        
        with open(file_path, 'rb') as f:
            data = f.read()
        
        print(f"Binary dosya okundu: {file_path}")
        print(f"Dosya boyutu: {len(data)} byte")
        return data
    except Exception as e:
        print(f"Hata: Binary dosya okunamadı - {e}")
        sys.exit(1)

def send_packet(ser, packet_data, packet_number, total_packets):
    """Tek bir paketi UART üzerinden gönderir"""
    try:
        # Paket başlığı oluştur (isteğe göre özelleştirilebilir)
        # Format: [START_BYTE, PACKET_NUM_H, PACKET_NUM_L, DATA_SIZE_H, DATA_SIZE_L, DATA..., CHECKSUM]
        START_BYTE = 0xAA  # Paket başlangıç byte'ı
        packet_size = len(packet_data)
        
        # Paket numarasını 2 byte olarak ayır
        packet_num_high = (packet_number >> 8) & 0xFF
        packet_num_low = packet_number & 0xFF
        
        # Paket boyutunu 2 byte olarak ayır (256 ve üzeri değerler için)
        packet_size_high = (packet_size >> 8) & 0xFF
        packet_size_low = packet_size & 0xFF
        
        # Paket oluştur: [START, PACKET_NUM_H, PACKET_NUM_L, SIZE_H, SIZE_L, DATA...]
        packet = bytearray([START_BYTE, packet_num_high, packet_num_low, packet_size_high, packet_size_low])
        packet.extend(packet_data)
        
        # Checksum ekle
        checksum = calculate_checksum(packet)
        packet.append(checksum)
        
        # Paketi gönder
        ser.write(packet)
        ser.flush()  # Tüm verinin gönderildiğinden emin ol
        
        print(f"Paket {packet_number}/{total_packets} gönderildi - Veri boyutu: {packet_size} byte, Toplam paket: {len(packet)} byte")
        
        # Kısa bir bekleme (bootloader'ın paketi işlemesi için)
        time.sleep(0.01)
        
        return True
    except Exception as e:
        print(f"Hata: Paket gönderilemedi - {e}")
        return False

def send_bootloader_file(ser, bin_data):
    """Binary dosyayı paket paket UART üzerinden gönderir"""
    print("\n" + "=" * 50)
    print("Bootloader Güncelleme Başlatılıyor...")
    print("=" * 50)
    
    total_size = len(bin_data)
    total_packets = (total_size + PACKET_SIZE - 1) // PACKET_SIZE  # Yuvarlama yukarı
    
    print(f"Toplam dosya boyutu: {total_size} byte")
    print(f"Paket boyutu: {PACKET_SIZE} byte")
    print(f"Toplam paket sayısı: {total_packets}")
    print()
    print("Gönderim başlıyor...\n")
    
    # Paketleri gönder
    sent_bytes = 0
    for packet_num in range(total_packets):
        start_idx = packet_num * PACKET_SIZE
        end_idx = min(start_idx + PACKET_SIZE, total_size)
        packet_data = bin_data[start_idx:end_idx]
        
        if not send_packet(ser, packet_data, packet_num + 1, total_packets):
            print(f"Paket {packet_num + 1} gönderilemedi, işlem durduruluyor.")
            return False
        
        sent_bytes += len(packet_data)
        progress = (sent_bytes / total_size) * 100
        print(f"İlerleme: {progress:.1f}% ({sent_bytes}/{total_size} byte)")
    
    print("\n" + "=" * 50)
    print("Tüm paketler başarıyla gönderildi!")
    print("=" * 50)
    return True

def read_uart_data(ser):
    """UART'tan veri okur ve yazdırır (arka planda çalışır)"""
    try:
        while True:
            if ser.in_waiting > 0:
                # Byte olarak oku
                data = ser.read(ser.in_waiting)
                
                # Hem hex hem de ASCII formatında göster
                print(f"\n[Gelen Veri] Hex: {data.hex()}")
                print(f"[Gelen Veri] ASCII: {data.decode('utf-8', errors='replace')}")
                print(f"[Gelen Veri] Byte Sayısı: {len(data)}")
            
            time.sleep(0.01)  # CPU kullanımını azaltmak için kısa bekleme
            
    except Exception as e:
        pass  # Sessizce çık (ana thread'den kontrol edilir)

def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("Nuvoton Bootloader Güncelleme")
    print("=" * 50)
    
    # Binary dosya yolunu belirle
    bin_file = "NuvotonM26x-Bootloader-Test.bin"
    if len(sys.argv) > 1:
        # İlk argüman port veya dosya yolu olabilir
        if os.path.exists(sys.argv[1]) and sys.argv[1].endswith('.bin'):
            bin_file = sys.argv[1]
            port_name = sys.argv[2] if len(sys.argv) > 2 else None
        else:
            port_name = sys.argv[1]
            bin_file = sys.argv[2] if len(sys.argv) > 2 else bin_file
    else:
        port_name = None
    
    # Mevcut portları göster
    find_serial_ports()
    print()
    
    if port_name:
        print(f"Belirtilen port: {port_name}")
    else:
        print("Port belirtilmedi, otomatik tespit edilecek...")
    
    print(f"Binary dosya: {bin_file}")
    print()
    
    # Binary dosyayı oku
    bin_data = read_bin_file(bin_file)
    print()
    
    # Serial port'u aç
    ser = open_serial_port(port_name, BAUD_RATE)
    
    # Port ayarlarını göster
    print(f"Baud Rate: {ser.baudrate}")
    print(f"Data Bits: {ser.bytesize}")
    print(f"Parity: {ser.parity}")
    print(f"Stop Bits: {ser.stopbits}")
    print()
    
    try:
        # Bootloader dosyasını gönder
        success = send_bootloader_file(ser, bin_data)
        
        if success:
            print("\nGüncelleme tamamlandı. Karşı taraftan gelen yanıtlar dinleniyor...")
            print("Çıkmak için Ctrl+C tuşlarına basın\n")
            print("-" * 50)
            
            # Gelen verileri dinle
            while True:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    print(f"\n[Gelen Veri] Hex: {data.hex()}")
                    print(f"[Gelen Veri] ASCII: {data.decode('utf-8', errors='replace')}")
                    print(f"[Gelen Veri] Byte Sayısı: {len(data)}")
                    print("-" * 50)
                time.sleep(0.1)
        else:
            print("\nGüncelleme başarısız oldu.")
            
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırılıyor...")
    except Exception as e:
        print(f"\nHata oluştu: {e}")
    finally:
        ser.close()
        print("Port kapatıldı.")

if __name__ == "__main__":
    main()

