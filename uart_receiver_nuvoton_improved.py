#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton ISP Bootloader - İyileştirilmiş Versiyon
Gerçek dünya uygulaması için optimize edilmiş
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
MAX_PKT_SIZE = 64
CONNECT_TIMEOUT_MS = 300  # Bootloader 300ms bekliyor
MAX_RETRY_COUNT = 3  # Maksimum retry sayısı

# Nuvoton ISP Komutları
CMD_UPDATE_APROM = 0x000000A0
CMD_CONNECT = 0x000000AE
CMD_GET_DEVICEID = 0x000000B1
CMD_RUN_APROM = 0x000000AB
CMD_RESEND_PACKET = 0x000000FF

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

def calculate_checksum(data, start_offset=0, end_offset=None):
    """16-bit checksum hesaplama (Nuvoton protokolü)"""
    if end_offset is None:
        end_offset = len(data)
    checksum = 0
    for i in range(start_offset, end_offset):
        checksum += data[i]
    return checksum & 0xFFFF  # 16-bit

def create_packet(cmd, param1=0, param2=0, data=None, is_first_packet=False, seq_no=0):
    """
    64 byte Nuvoton paketi oluşturur
    
    ISP_UART protokolüne göre:
    - Gönderilen paketlerde checksum YOK (sadece yanıtlarda var)
    - Byte 0-3: CMD
    - Byte 4-7: Padding (pu8Src += 8 ile atlanır)
    - Byte 8+: Data
    """
    packet = bytearray(MAX_PKT_SIZE)
    
    # Byte 0-3: Komut (uint32_t, little-endian)
    packet[0:4] = uint32_to_bytes(cmd)
    
    # İlk paket için özel format (CMD_UPDATE_APROM):
    if is_first_packet and param2 != 0:
        # Byte 8-11: Address
        packet[8:12] = uint32_to_bytes(param1)
        # Byte 12-15: TotalLen
        packet[12:16] = uint32_to_bytes(param2)
        # Byte 16-63: Veri (48 byte)
        if data:
            data_len = min(len(data), 48)
            packet[16:16+data_len] = data[:data_len]
    else:
        # Devam paketleri için:
        # Byte 8-63: Veri (56 byte)
        if data:
            data_len = min(len(data), 56)
            packet[8:8+data_len] = data[:data_len]
    
    return packet

def send_packet_fast(ser, packet, retry_count=0):
    """
    Paketi hızlı ve güvenilir şekilde gönderir
    - Minimum loglama
    - Chunk'lar halinde gönderim
    - Retry limiti ile güvenli
    """
    if len(packet) != MAX_PKT_SIZE:
        return False
    
    if retry_count >= MAX_RETRY_COUNT:
        return False
    
    try:
        if not ser.is_open or not ser.writable():
            return False
        
        # Buffer temizle (hızlı)
        try:
            ser.reset_output_buffer()
        except:
            pass
        
        # Paketi chunk'lar halinde gönder (16 byte)
        chunk_size = 16
        try:
            for i in range(0, len(packet), chunk_size):
                chunk = packet[i:i+chunk_size]
                ser.write(chunk)
            ser.flush()
            return True
        except (serial.SerialTimeoutException, serial.SerialException, OSError):
            # Port hatası - yeniden aç ve tekrar dene
            if retry_count < MAX_RETRY_COUNT:
                try:
                    ser.close()
                    time.sleep(0.1)
                    ser.open()
                    time.sleep(0.1)
                    return send_packet_fast(ser, packet, retry_count + 1)
                except:
                    return False
            return False
            
    except Exception:
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
        time.sleep(0.001)  # Minimum bekleme
    
    return bytes(response)

def send_connect_fast(ser):
    """
    CMD_CONNECT'i hızlı ve sürekli gönderir
    - Minimum loglama (sadece başarıda)
    - 300ms penceresini yakalamak için optimize edilmiş
    """
    connect_packet = create_packet(CMD_CONNECT)
    
    # Sürekli gönder (300ms penceresini yakalamak için)
    start_time = time.time()
    max_duration = 5.0  # Maksimum 5 saniye dene
    
    while (time.time() - start_time) < max_duration:
        # Paketi gönder
        if send_packet_fast(ser, connect_packet):
            # Kısa bekleme (minimum)
            time.sleep(0.005)  # 5ms
            
            # Yanıt var mı kontrol et
            if ser.in_waiting >= 4:
                response = receive_response(ser, timeout=0.1)
                if response and len(response) >= 64:
                    # ASCII kontrolü (application mesajı mı?)
                    first_bytes = response[:4]
                    is_ascii = all(32 <= b <= 126 for b in first_bytes)
                    
                    if not is_ascii:
                        # Bootloader yanıtı!
                        checksum = (response[1] << 8) | response[0]
                        packet_no = bytes_to_uint32(response, 4)
                        aprom_size = bytes_to_uint32(response, 8)
                        dataflash_addr = bytes_to_uint32(response, 12)
                        
                        print(f"\n✓✓✓ BOOTLOADER YAKALANDI! ✓✓✓")
                        print(f"  Checksum: 0x{checksum:04X}")
                        print(f"  Paket No: {packet_no}")
                        print(f"  APROM Boyutu: {aprom_size} byte (0x{aprom_size:08X})")
                        print(f"  DataFlash Adresi: 0x{dataflash_addr:08X}")
                        return True
        else:
            # Port hatası - kısa bekleme
            time.sleep(0.01)
    
    return False

def send_update_aprom_improved(ser, bin_data, start_address=0x00000000):
    """
    APROM güncelleme - iyileştirilmiş versiyon
    - CMD_RESEND_PACKET desteği
    - Paket numarası kontrolü
    - Retry mekanizması
    """
    total_size = len(bin_data)
    
    print(f"\n{'='*60}")
    print(f"APROM Güncelleme Başlatılıyor...")
    print(f"{'='*60}")
    print(f"Dosya boyutu: {total_size} byte")
    print(f"Başlangıç adresi: 0x{start_address:08X}\n")
    
    # İlk paket: CMD_UPDATE_APROM + adres + boyut
    first_data = bin_data[:48] if len(bin_data) >= 48 else bin_data
    first_packet = create_packet(CMD_UPDATE_APROM, start_address, total_size, first_data, is_first_packet=True)
    
    if not send_packet_fast(ser, first_packet):
        print("✗ İlk paket gönderilemedi")
        return False
    
    # Yanıt bekle
    response = receive_response(ser, timeout=1.0)
    if not response:
        print("✗ İlk paket yanıtı alınamadı")
        return False
    
    resp_packet_no = bytes_to_uint32(response, 4)
    print(f"✓ İlk paket gönderildi, Yanıt Paket No: {resp_packet_no}")
    
    # Devam paketleri
    data_offset = 48
    packet_num = 2
    expected_packet_no = 2
    
    while data_offset < total_size:
        chunk_data = bin_data[data_offset:data_offset+56]
        chunk_len = len(chunk_data)
        
        packet = create_packet(CMD_UPDATE_APROM, 0, 0, chunk_data)
        
        # Paketi gönder (retry ile)
        success = False
        for retry in range(MAX_RETRY_COUNT):
            if send_packet_fast(ser, packet):
                # Yanıt bekle
                response = receive_response(ser, timeout=1.0)
                if response:
                    resp_packet_no = bytes_to_uint32(response, 4)
                    resp_cmd = bytes_to_uint32(response, 0)  # İlk 4 byte komut olabilir
                    
                    # CMD_RESEND_PACKET kontrolü
                    if resp_cmd == CMD_RESEND_PACKET:
                        print(f"  ⚠ Paket {packet_num} yeniden gönderiliyor...")
                        time.sleep(0.1)
                        continue  # Aynı paketi tekrar gönder
                    
                    # Paket numarası kontrolü
                    if resp_packet_no == expected_packet_no:
                        success = True
                        break
                    else:
                        print(f"  ⚠ Paket No uyumsuz: {resp_packet_no} (Beklenen: {expected_packet_no})")
                        time.sleep(0.1)
                        continue
                else:
                    time.sleep(0.1)
                    continue
            else:
                time.sleep(0.1)
                continue
        
        if not success:
            print(f"✗ Paket {packet_num} gönderilemedi (max retry)")
            return False
        
        data_offset += chunk_len
        packet_num += 1
        expected_packet_no += 1
        
        # İlerleme göster (her 10 pakette bir)
        if packet_num % 10 == 0:
            progress = (data_offset / total_size) * 100
            print(f"  İlerleme: {progress:.1f}% ({data_offset}/{total_size} byte)")
        
        time.sleep(0.02)  # Minimum bekleme
    
    print(f"\n{'='*60}")
    print(f"✓✓✓ Güncelleme tamamlandı! ✓✓✓")
    print(f"{'='*60}")
    return True

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python3 uart_receiver_nuvoton_improved.py <port> <bin_file>")
        print("Örnek: python3 uart_receiver_nuvoton_improved.py /dev/ttyACM0 firmware.bin")
        sys.exit(1)
    
    port_name = sys.argv[1]
    bin_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not bin_file:
        print("✗ Binary dosya belirtilmedi!")
        sys.exit(1)
    
    if not os.path.exists(bin_file):
        print(f"✗ Dosya bulunamadı: {bin_file}")
        sys.exit(1)
    
    # Binary dosyayı oku
    with open(bin_file, 'rb') as f:
        bin_data = f.read()
    
    print("=" * 60)
    print("Nuvoton ISP Bootloader - İyileştirilmiş Versiyon")
    print("=" * 60)
    print(f"Port: {port_name}")
    print(f"Binary dosya: {bin_file}")
    print(f"Dosya boyutu: {len(bin_data)} byte")
    print()
    
    # Port'u aç
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        print(f"✓ Port açıldı: {port_name}")
    except Exception as e:
        print(f"✗ Port açılamadı: {e}")
        sys.exit(1)
    
    try:
        # Buffer'ları temizle
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.1)
        
        print("\n⚠️  ÖNEMLİ: Kartı RESET yapın!")
        print("   Bootloader 300ms içinde CMD_CONNECT bekliyor...")
        print("   Reset yaptıktan sonra ENTER'a basın...")
        input()
        
        # Hızlı CMD_CONNECT gönder
        if not send_connect_fast(ser):
            print("\n✗ Bootloader yakalanamadı!")
            print("   - Reset yaptınız mı?")
            print("   - 300ms içinde gönderildi mi?")
            return
        
        # Cihaz ID al
        print("\nCihaz ID alınıyor...")
        device_id_packet = create_packet(CMD_GET_DEVICEID)
        if send_packet_fast(ser, device_id_packet):
            time.sleep(0.1)
            device_response = receive_response(ser, timeout=0.5)
            if device_response and len(device_response) >= 64:
                device_id = bytes_to_uint32(device_response, 8)
                print(f"✓ Cihaz ID: 0x{device_id:08X}")
        
        # APROM güncelle
        if not send_update_aprom_improved(ser, bin_data):
            print("\n✗ Güncelleme başarısız!")
            return
        
        # CMD_RUN_APROM gönder
        print("\n[SON] CMD_RUN_APROM gönderiliyor (reset için)...")
        run_packet = create_packet(CMD_RUN_APROM)
        if send_packet_fast(ser, run_packet):
            print("✓ CMD_RUN_APROM gönderildi")
            print("  → Bootloader reset atacak ve yeni firmware çalışacak")
            time.sleep(1.0)
        
        print("\n✓✓✓ İşlem tamamlandı! ✓✓✓")
        
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırılıyor...")
    except Exception as e:
        print(f"\n✗ Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ser.close()

if __name__ == "__main__":
    main()

