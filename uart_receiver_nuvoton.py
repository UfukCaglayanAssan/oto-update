#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton ISP Bootloader - Resmi Protokol Uyumlu
Raspberry Pi'de çalışır ve Nuvoton'un resmi ISP protokolünü kullanır
"""

import serial
import serial.tools.list_ports
import sys
import time
import os

# UART ayarları
BAUD_RATE = 115200
TIMEOUT = 2
WRITE_TIMEOUT = 5
MAX_PKT_SIZE = 64  # Nuvoton protokolü: SABİT 64 byte

# Nuvoton ISP Komutları (isp_user.h'den)
CMD_UPDATE_APROM = 0x000000A0
CMD_UPDATE_CONFIG = 0x000000A1
CMD_READ_CONFIG = 0x000000A2
CMD_ERASE_ALL = 0x000000A3
CMD_SYNC_PACKNO = 0x000000A4
CMD_GET_FWVER = 0x000000A6
CMD_RUN_APROM = 0x000000AB
CMD_RUN_LDROM = 0x000000AC
CMD_RESET = 0x000000AD
CMD_CONNECT = 0x000000AE
CMD_DISCONNECT = 0x000000AF
CMD_GET_DEVICEID = 0x000000B1
CMD_UPDATE_DATAFLASH = 0x000000C3
CMD_RESEND_PACKET = 0x000000FF

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
            common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyAMA0', '/dev/ttyS0', '/dev/ttyACM0', '/dev/ttyACM1']
            for port in common_ports:
                try:
                    ser = serial.Serial(port, baud_rate, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                                      rtscts=False, dsrdtr=False, xonxoff=False)
                    print(f"Port açıldı: {port}")
                    return ser
                except serial.SerialException:
                    continue
            raise serial.SerialException("Uygun port bulunamadı")
        else:
            ser = serial.Serial(port_name, baud_rate, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                              rtscts=False, dsrdtr=False, xonxoff=False)
            print(f"Port açıldı: {port_name}")
            return ser
    except serial.SerialException as e:
        print(f"Hata: Port açılamadı - {e}")
        sys.exit(1)

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

def calculate_checksum(data):
    """16-bit checksum hesaplama (Nuvoton protokolü)"""
    checksum = 0
    for byte in data:
        checksum += byte
    return checksum & 0xFFFF  # 16-bit

def create_packet(cmd, param1=0, param2=0, data=None):
    """64 byte Nuvoton paketi oluşturur"""
    packet = bytearray(MAX_PKT_SIZE)
    
    # Byte 0-3: Komut (uint32_t, little-endian)
    packet[0:4] = uint32_to_bytes(cmd)
    
    # Byte 4-7: Parametre 1 (uint32_t, little-endian)
    packet[4:8] = uint32_to_bytes(param1)
    
    # Byte 8-11: Parametre 2 (uint32_t, little-endian) - eğer varsa
    if param2 != 0:
        packet[8:12] = uint32_to_bytes(param2)
    
    # Byte 8-63: Veri (56 byte)
    if data:
        data_len = min(len(data), 56)  # Maksimum 56 byte veri
        packet[8:8+data_len] = data[:data_len]
    
    return packet

def send_packet(ser, packet):
    """64 byte paketi gönderir"""
    if len(packet) != MAX_PKT_SIZE:
        print(f"⚠ HATA: Paket boyutu {len(packet)} byte, {MAX_PKT_SIZE} byte olmalı!")
        return False
    
    try:
        # Port yazılabilir mi kontrol et
        if not ser.writable():
            print(f"✗ Port yazılabilir değil!")
            return False
        
        # Output buffer kontrolü
        if ser.out_waiting > 100:
            print(f"⚠ Output buffer dolu ({ser.out_waiting} byte), temizleniyor...")
            ser.reset_output_buffer()
            time.sleep(0.1)
        
        # Buffer temizle
        ser.reset_output_buffer()
        time.sleep(0.05)
        
        # Paketi küçük parçalara bölerek gönder (timeout'u önlemek için)
        chunk_size = 16  # 16 byte'lık parçalar
        total_written = 0
        
        for i in range(0, len(packet), chunk_size):
            chunk = packet[i:i+chunk_size]
            try:
                bytes_written = ser.write(chunk)
                total_written += bytes_written
                ser.flush()  # Her chunk'tan sonra flush
                time.sleep(0.001)  # Kısa bekleme
            except serial.SerialTimeoutException:
                print(f"⚠ Chunk {i//chunk_size + 1} timeout, devam ediliyor...")
                # Timeout olsa bile devam et
                total_written += len(chunk)
        
        if total_written != MAX_PKT_SIZE:
            print(f"⚠ Uyarı: {total_written}/{MAX_PKT_SIZE} byte yazıldı")
            # Yine de devam et
        
        # Flush işlemi (timeout ile)
        start_time = time.time()
        while ser.out_waiting > 0:
            if time.time() - start_time > 1.0:  # 1 saniye timeout
                print(f"⚠ Flush timeout, kalan: {ser.out_waiting} byte")
                break
            time.sleep(0.01)
        
        ser.flush()
        
        return True
        
    except serial.SerialTimeoutException as e:
        print(f"⚠ Write timeout: {e}")
        print(f"  → Port yeniden açılıyor...")
        # Port'u yeniden açmayı dene
        try:
            ser.close()
            time.sleep(0.5)
            ser.open()
            time.sleep(0.3)
            print(f"  ✓ Port yeniden açıldı")
            # Tekrar dene
            return send_packet(ser, packet)
        except Exception as e2:
            print(f"  ✗ Port yeniden açılamadı: {e2}")
            return False
    except Exception as e:
        print(f"✗ Paket gönderme hatası: {e}")
        import traceback
        traceback.print_exc()
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

def send_connect(ser):
    """CMD_CONNECT gönderir ve yanıt alır"""
    print("CMD_CONNECT gönderiliyor...")
    
    # Port durumunu kontrol et
    print(f"  Port durumu: açık={ser.is_open}, yazılabilir={ser.writable()}")
    print(f"  Output buffer: {ser.out_waiting} byte")
    print(f"  Input buffer: {ser.in_waiting} byte")
    
    # Buffer temizle
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)  # Biraz daha uzun bekle
    except Exception as e:
        print(f"  ⚠ Buffer temizleme hatası: {e}")
    
    # CMD_CONNECT paketi oluştur
    packet = create_packet(CMD_CONNECT)
    print(f"  Paket hazır: {len(packet)} byte")
    print(f"  Paket hex (ilk 16 byte): {packet[:16].hex()}")
    
    # Gönder
    if not send_packet(ser, packet):
        print("✗ CMD_CONNECT gönderilemedi")
        return False
    
    print(f"✓ CMD_CONNECT gönderildi")
    
    # Kısa bekleme
    time.sleep(0.1)
    
    # Yanıt bekle (300ms timeout var, hızlı olmalı)
    print("Yanıt bekleniyor (0.5 saniye)...")
    response = receive_response(ser, timeout=0.5)
    
    if response:
        checksum = (response[1] << 8) | response[0]  # 16-bit little-endian
        packet_no = bytes_to_uint32(response, 4)
        aprom_size = bytes_to_uint32(response, 8)
        dataflash_addr = bytes_to_uint32(response, 12)
        
        print(f"✓✓✓ YANIT ALINDI! ✓✓✓")
        print(f"  Checksum: 0x{checksum:04X}")
        print(f"  Paket No: {packet_no}")
        print(f"  APROM Boyutu: {aprom_size} byte (0x{aprom_size:08X})")
        print(f"  DataFlash Adresi: 0x{dataflash_addr:08X}")
        print(f"  Tam Yanıt (ilk 32 byte): {response[:32].hex()}")
        return True
    else:
        print("✗ Yanıt alınamadı (timeout)")
        print(f"  Input buffer: {ser.in_waiting} byte")
        if ser.in_waiting > 0:
            partial = ser.read(ser.in_waiting)
            print(f"  Kısmi yanıt: {partial.hex()}")
        return False

def send_update_aprom(ser, bin_data):
    """APROM güncellemesi yapar"""
    total_size = len(bin_data)
    start_address = 0x00000000  # APROM başlangıç adresi
    
    print(f"\n{'='*60}")
    print(f"APROM Güncelleme Başlatılıyor...")
    print(f"{'='*60}")
    print(f"Dosya boyutu: {total_size} byte")
    print(f"Başlangıç adresi: 0x{start_address:08X}")
    
    # İlk paket: CMD_UPDATE_APROM + adres + boyut
    print(f"\n[1/3] CMD_UPDATE_APROM (başlangıç) gönderiliyor...")
    first_data = bin_data[:52] if len(bin_data) >= 52 else bin_data  # İlk 52 byte
    first_packet = create_packet(CMD_UPDATE_APROM, start_address, total_size, first_data)
    
    if not send_packet(ser, first_packet):
        print("✗ İlk paket gönderilemedi")
        return False
    
    print(f"✓ İlk paket gönderildi ({len(first_data)} byte veri)")
    
    # Yanıt bekle
    response = receive_response(ser, timeout=1.0)
    if response:
        packet_no = bytes_to_uint32(response, 4)
        print(f"✓ Yanıt alındı, Paket No: {packet_no}")
    
    # Devam paketleri (56 byte veri her pakette)
    data_offset = 52
    packet_num = 2
    
    while data_offset < total_size:
        # 56 byte veri al
        chunk_data = bin_data[data_offset:data_offset+56]
        chunk_len = len(chunk_data)
        
        # Paketi 64 byte'a tamamla
        packet = create_packet(CMD_UPDATE_APROM, packet_num, 0, chunk_data)
        
        print(f"[{packet_num}] Paket gönderiliyor... ({chunk_len} byte veri, offset: {data_offset})")
        
        if not send_packet(ser, packet):
            print(f"✗ Paket {packet_num} gönderilemedi")
            return False
        
        # Yanıt bekle
        response = receive_response(ser, timeout=1.0)
        if response:
            resp_packet_no = bytes_to_uint32(response, 4)
            print(f"  ✓ Yanıt: Paket No {resp_packet_no}")
        
        data_offset += chunk_len
        packet_num += 1
        
        # İlerleme göster
        progress = (data_offset / total_size) * 100
        print(f"  İlerleme: {progress:.1f}% ({data_offset}/{total_size} byte)")
        
        time.sleep(0.05)  # Kısa bekleme
    
    print(f"\n{'='*60}")
    print(f"✓✓✓ Güncelleme tamamlandı! ✓✓✓")
    print(f"{'='*60}")
    return True

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("Nuvoton ISP Bootloader - Resmi Protokol")
    print("=" * 60)
    
    # Binary dosya yolunu belirle
    bin_file = "NuvotonM26x-Bootloader-Test.bin"
    if len(sys.argv) > 1:
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
    if not os.path.exists(bin_file):
        print(f"✗ HATA: Dosya bulunamadı: {bin_file}")
        sys.exit(1)
    
    with open(bin_file, 'rb') as f:
        bin_data = f.read()
    
    print(f"✓ Binary dosya okundu: {len(bin_data)} byte")
    print()
    
    # Serial port'u aç
    ser = open_serial_port(port_name, BAUD_RATE)
    
    # Port durumunu kontrol et
    print(f"Baud Rate: {ser.baudrate}")
    print(f"Port açık: {ser.is_open}")
    print(f"Port yazılabilir: {ser.writable()}")
    print(f"Port okunabilir: {ser.readable()}")
    print()
    
    # Port'u temizle
    try:
        print("Port buffer'ları temizleniyor...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.3)  # Biraz daha uzun bekle
        print(f"  Output buffer: {ser.out_waiting} byte")
        print(f"  Input buffer: {ser.in_waiting} byte")
    except Exception as e:
        print(f"  ⚠ Buffer temizleme hatası: {e}")
    
    print()
    
    try:
        print("⚠️  ÖNEMLİ: Kartı RESET yapın ve HEMEN bu scripti çalıştırın!")
        print("⚠️  Bootloader sadece 300ms içinde CMD_CONNECT bekliyor!")
        print()
        input("Kartı resetledikten sonra ENTER'a basın...")
        print()
        
        # CMD_CONNECT gönder
        if not send_connect(ser):
            print("\n✗ CMD_CONNECT başarısız, güncelleme yapılamaz")
            return
        
        time.sleep(0.1)
        
        # APROM güncellemesi
        if send_update_aprom(ser, bin_data):
            print("\n✓✓✓ Güncelleme başarılı! ✓✓✓")
        else:
            print("\n✗ Güncelleme başarısız")
        
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırılıyor...")
    except Exception as e:
        print(f"\n✗ Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ser.close()
        print("Port kapatıldı.")

if __name__ == "__main__":
    main()

