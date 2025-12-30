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
CMD_SYNC_PACKNO = 0x000000A4  # Paket numarası senkronizasyonu
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
            # Önce PySerial ile portları bul
            ports = serial.tools.list_ports.comports()
            if ports:
                print("Mevcut portlar:")
                for p in ports:
                    print(f"  - {p.device}: {p.description}")
                # İlk bulunan portu dene
                port_name = ports[0].device
                print(f"Otomatik seçilen port: {port_name}")
            else:
                # PySerial port bulamazsa standart portları dene
                common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyAMA0', '/dev/ttyS0']
                for port in common_ports:
                    try:
                        ser = serial.Serial(port, baud_rate, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                                          rtscts=False, dsrdtr=False, xonxoff=False)
                        print(f"Port açıldı: {port}")
                        return ser
                    except (serial.SerialException, FileNotFoundError):
                        continue
                raise serial.SerialException("Uygun port bulunamadı")
        
        # Belirtilen portu aç
        ser = serial.Serial(port_name, baud_rate, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        print(f"Port açıldı: {port_name}")
        return ser
        
    except FileNotFoundError as e:
        print(f"✗ Hata: Port bulunamadı - {e}")
        print()
        
        # Mevcut portları göster
        ports = serial.tools.list_ports.comports()
        if ports:
            print("Mevcut portlar:")
            for p in ports:
                print(f"  ✓ {p.device}: {p.description}")
            print()
            print(f"ÖNERİLEN: {ports[0].device} portunu kullanın!")
            print()
            print(f"Kullanım:")
            print(f"  python3 uart_receiver_nuvoton.py {ports[0].device} NuvotonM26x-Bootloader-Test.bin")
        else:
            print("Kontrol edin:")
            print("  1. USB-UART dönüştürücü bağlı mı?")
            print("  2. USB kablosu çalışıyor mu?")
            print("  3. Port adı doğru mu?")
            print()
            print("Mevcut portları görmek için:")
            print("  python3 quick_port_check.py")
            print("  veya")
            print("  ls -l /dev/tty* | grep -E 'ACM|USB'")
        sys.exit(1)
    except serial.SerialException as e:
        print(f"✗ Hata: Port açılamadı - {e}")
        print()
        
        # Port kullanımını kontrol et
        import subprocess
        try:
            result = subprocess.run(['lsof', port_name], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                print("⚠️  Port başka bir program tarafından kullanılıyor:")
                print(result.stdout)
                print()
                print("Çözüm:")
                print("  1. Diğer programı kapatın (uart_listener.py gibi)")
                print("  2. Veya farklı bir port kullanın")
        except:
            pass
        
        print("Kontrol edin:")
        print("  1. Port başka bir program tarafından kullanılıyor olabilir")
        print("     → lsof | grep ttyACM0  ile kontrol edin")
        print("  2. Port izinleri yeterli mi? (sudo gerekebilir)")
        print("  3. USB-UART dönüştürücü driver'ı yüklü mü?")
        print()
        
        # Mevcut portları göster
        ports = serial.tools.list_ports.comports()
        if ports:
            print("Mevcut portlar:")
            for p in ports:
                print(f"  - {p.device}: {p.description}")
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

def create_packet(cmd, param1=0, param2=0, data=None, is_first_packet=False):
    """
    64 byte Nuvoton paketi oluşturur
    
    ISP_UART protokolüne göre:
    - Byte 0-3: CMD
    - Byte 4-7: Padding (pu8Src += 8 ile atlanır)
    - Byte 8+: Data veya parametreler
    """
    packet = bytearray(MAX_PKT_SIZE)
    
    # Byte 0-3: Komut (uint32_t, little-endian)
    packet[0:4] = uint32_to_bytes(cmd)
    
    # CMD_SYNC_PACKNO için özel format: Byte 8-11'de paket numarası
    if cmd == CMD_SYNC_PACKNO:
        packet[8:12] = uint32_to_bytes(param1)  # Paket numarası
        return packet
    
    # İlk paket için özel format (CMD_UPDATE_APROM):
    # ISP_UART kodunda: pu8Src += 8 yapılıyor, sonra:
    # Byte 8-11: Address (inpw(pu8Src))
    # Byte 12-15: TotalLen (inpw(pu8Src + 4))
    # Byte 16-63: Data (48 byte)
    if is_first_packet and param2 != 0:
        # Byte 8-11: Address
        packet[8:12] = uint32_to_bytes(param1)
        # Byte 12-15: TotalLen
        packet[12:16] = uint32_to_bytes(param2)
        # Byte 16-63: Veri (48 byte)
        if data:
            data_len = min(len(data), 48)  # İlk pakette maksimum 48 byte veri
            packet[16:16+data_len] = data[:data_len]
    else:
        # Devam paketleri için:
        # Byte 0-3: CMD
        # Byte 4-7: İgnore edilir (bootloader kullanmıyor)
        # Byte 8-63: Veri (56 byte) - pu8Src += 8 yapıldıktan sonra byte 8'den başlıyor
        if data:
            data_len = min(len(data), 56)  # Devam paketlerinde maksimum 56 byte veri
            packet[8:8+data_len] = data[:data_len]
    
    return packet

def send_packet(ser, packet, retry=False):
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
        
        # Paketi byte-byte gönder (timeout'u önlemek için)
        total_written = 0
        
        # Önce test byte gönder
        try:
            test_byte = bytes([packet[0]])
            test_written = ser.write(test_byte)
            if test_written == 0:
                raise serial.SerialTimeoutException("Test byte yazılamadı")
            ser.flush()
            time.sleep(0.01)
        except serial.SerialTimeoutException:
            print(f"⚠ Test byte timeout, port yeniden açılıyor...")
            ser.close()
            time.sleep(1.0)
            ser.open()
            time.sleep(0.5)
        
        # Paketi chunk'lar halinde gönder (daha hızlı ve güvenilir)
        chunk_size = 16  # 16 byte chunk'lar
        try:
            for i in range(0, len(packet), chunk_size):
                chunk = packet[i:i+chunk_size]
                bytes_written = ser.write(chunk)
                if bytes_written > 0:
                    total_written += bytes_written
                ser.flush()  # Her chunk'tan sonra flush
                time.sleep(0.001)  # Kısa bekleme
        except (serial.SerialTimeoutException, serial.SerialException, OSError) as e:
            # I/O hatası - port donmuş olabilir
            print(f"⚠ Chunk gönderme hatası: {e}")
            # Port'u yeniden açmayı dene
            try:
                ser.close()
                time.sleep(0.5)
                ser.open()
                time.sleep(0.3)
            except:
                pass
            # Kalan byte'ları göndermeyi dene
            remaining = packet[total_written:]
            if remaining:
                try:
                    ser.write(remaining)
                    total_written += len(remaining)
                except:
                    pass
        
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
        
    except (serial.SerialTimeoutException, serial.SerialException, OSError) as e:
        print(f"⚠ Port hatası: {e}")
        print(f"  → Port yeniden açılıyor...")
        # Port'u yeniden açmayı dene
        try:
            ser.close()
            time.sleep(0.5)
            ser.open()
            time.sleep(0.3)
            print(f"  ✓ Port yeniden açıldı")
            # Tekrar dene (sadece 1 kez)
            if not retry:
                return send_packet(ser, packet, retry=True)
            else:
                return False
        except Exception as e2:
            print(f"  ✗ Port yeniden açılamadı: {e2}")
            return False
    except Exception as e:
        print(f"✗ Paket gönderme hatası: {e}")
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
    
    # Buffer temizle (çok hızlı, timeout'u önlemek için)
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.01)  # Çok kısa bekleme
    except Exception as e:
        print(f"  ⚠ Buffer temizleme hatası: {e}")
    
    # CMD_CONNECT paketi oluştur
    packet = create_packet(CMD_CONNECT)
    
    # HEMEN gönder (reset sonrası 300ms içinde olmalı)
    if not send_packet(ser, packet):
        print("✗ CMD_CONNECT gönderilemedi")
        return False
    
    print(f"✓ CMD_CONNECT gönderildi")
    
    # Çok kısa bekleme (bootloader'ın işlemesi için)
    time.sleep(0.05)
    
    # Yanıt bekle (bootloader hızlı yanıt verir)
    print("Yanıt bekleniyor (0.3 saniye)...")
    response = receive_response(ser, timeout=0.3)
    
    if response:
        # Yanıtın bootloader'dan mı yoksa application'dan mı geldiğini kontrol et
        # Bootloader yanıtı: İlk 4 byte checksum+packet_no, sonra APROM size
        # Application yanıtı: ASCII metin
        
        # İlk byte'ları kontrol et (bootloader binary, application ASCII)
        first_bytes = response[:4]
        is_ascii = all(32 <= b <= 126 for b in first_bytes[:4])  # Printable ASCII
        
        if is_ascii:
            # Application'dan gelen yanıt
            ascii_text = response[:64].decode('ascii', errors='ignore')
            print(f"⚠ UYARI: Application yanıtı alındı (bootloader değil)!")
            print(f"  Yanıt: {ascii_text[:50]}...")
            print(f"  → Bootloader modunda değil, application çalışıyor")
            print(f"  → Reset sonrası çok geç gönderilmiş olabilir (300ms içinde olmalı)")
            return False
        
        # Bootloader yanıtı
        checksum = (response[1] << 8) | response[0]  # 16-bit little-endian
        packet_no = bytes_to_uint32(response, 4)
        aprom_size = bytes_to_uint32(response, 8)
        dataflash_addr = bytes_to_uint32(response, 12)
        
        # Config verileri (Byte 16-31) - ReadData ile doldurulmuş olabilir
        config_data = response[16:32] if len(response) >= 32 else None
        
        print(f"✓✓✓ BOOTLOADER YANITI ALINDI! ✓✓✓")
        print(f"  Checksum: 0x{checksum:04X}")
        print(f"  Paket No: {packet_no}")
        print(f"  APROM Boyutu: {aprom_size} byte (0x{aprom_size:08X})")
        print(f"  DataFlash Adresi: 0x{dataflash_addr:08X}")
        
        # Tam yanıtı göster (debug için)
        print(f"  Tam Yanıt (ilk 32 byte): {response[:32].hex()}")
        
        # KRİTİK: Paket numarası senkronizasyonu (ÖNEMLİ!)
        print(f"\n  [KRİTİK] Paket numarası senkronize ediliyor...")
        sync_packet = create_packet(CMD_SYNC_PACKNO, 1)  # Paket numarasını 1 yap
        if send_packet(ser, sync_packet):
            time.sleep(0.1)
            sync_response = receive_response(ser, timeout=0.3)
            if sync_response:
                sync_packet_no = bytes_to_uint32(sync_response, 4)
                print(f"  ✓ Paket numarası senkronize edildi: {sync_packet_no}")
            else:
                print(f"  ⚠ Paket numarası senkronizasyon yanıtı alınamadı (devam ediliyor)")
        else:
            print(f"  ⚠ CMD_SYNC_PACKNO gönderilemedi (devam ediliyor)")
        
        # Cihaz ID'sini almak için CMD_GET_DEVICEID gönder
        print(f"\n  Cihaz ID'si alınıyor...")
        device_id_packet = create_packet(CMD_GET_DEVICEID)
        if send_packet(ser, device_id_packet):
            time.sleep(0.15)  # Biraz daha uzun bekle
            device_response = receive_response(ser, timeout=0.5)
            if device_response and len(device_response) >= 64:
                device_id = bytes_to_uint32(device_response, 8)
                checksum_dev = (device_response[1] << 8) | device_response[0]
                print(f"  ✓✓✓ CİHAZ ID YAKALANDI! ✓✓✓")
                print(f"  Cihaz ID: 0x{device_id:08X}")
                print(f"  Checksum: 0x{checksum_dev:04X}")
                print(f"  Tam Yanıt (ilk 16 byte): {device_response[:16].hex()}")
            else:
                print(f"  ⚠ Cihaz ID yanıtı alınamadı")
                if device_response:
                    print(f"  Kısmi yanıt: {device_response.hex()[:50]}")
                else:
                    print(f"  Input buffer: {ser.in_waiting} byte")
        else:
            print(f"  ⚠ CMD_GET_DEVICEID gönderilemedi")
        
        return True
    else:
        print("✗ Yanıt alınamadı (timeout)")
        print(f"  Input buffer: {ser.in_waiting} byte")
        if ser.in_waiting > 0:
            partial = ser.read(ser.in_waiting)
            ascii_text = partial.decode('ascii', errors='ignore')
            print(f"  Kısmi yanıt (ASCII): {ascii_text[:50]}")
            print(f"  Kısmi yanıt (Hex): {partial.hex()[:50]}")
        return False

def send_update_aprom(ser, bin_data, erase_before_update=False):
    """
    APROM güncellemesi yapar
    
    Args:
        ser: Serial port
        bin_data: Binary firmware verisi
        erase_before_update: Güncelleme öncesi tam silme yap (CMD_ERASE_ALL)
    """
    total_size = len(bin_data)
    start_address = 0x00000000  # APROM başlangıç adresi
    
    print(f"\n{'='*60}")
    print(f"APROM Güncelleme Başlatılıyor...")
    print(f"{'='*60}")
    print(f"Dosya boyutu: {total_size} byte")
    print(f"Başlangıç adresi: 0x{start_address:08X}")
    
    # Güncelleme öncesi tam silme (opsiyonel ama önerilen)
    if erase_before_update:
        print(f"\n[ÖNEMLİ] Güncelleme öncesi tam silme yapılıyor...")
        print(f"  ⚠️  UYARI: Bu işlem tüm APROM'u silecek!")
        erase_packet = create_packet(CMD_ERASE_ALL)
        if send_packet(ser, erase_packet):
            print(f"  ✓ CMD_ERASE_ALL gönderildi")
            # Silme işlemi için bekle (Flash silme zaman alır)
            time.sleep(1.0)  # 1 saniye bekle
            erase_response = receive_response(ser, timeout=2.0)
            if erase_response:
                erase_packet_no = bytes_to_uint32(erase_response, 4)
                print(f"  ✓ Silme tamamlandı, Yanıt Paket No: {erase_packet_no}")
            else:
                print(f"  ⚠ Silme yanıtı alınamadı (devam ediliyor)")
        else:
            print(f"  ⚠ CMD_ERASE_ALL gönderilemedi (devam ediliyor)")
        print()
    
    # İlk paket: CMD_UPDATE_APROM + adres + boyut
    print(f"\n[1/3] CMD_UPDATE_APROM (başlangıç) gönderiliyor...")
    first_data = bin_data[:48] if len(bin_data) >= 48 else bin_data  # İlk 48 byte (byte 16-63)
    first_packet = create_packet(CMD_UPDATE_APROM, start_address, total_size, first_data, is_first_packet=True)
    
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
    data_offset = 48  # İlk pakette 48 byte gönderildi
    packet_num = 2
    expected_packet_no = 2  # Beklenen yanıt paket numarası
    
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
            checksum_resp = (response[1] << 8) | response[0]
            
            # Paket numarası kontrolü
            if resp_packet_no == expected_packet_no:
                print(f"  ✓ Yanıt: Paket No {resp_packet_no} (Checksum: 0x{checksum_resp:04X})")
            else:
                print(f"  ⚠ Yanıt: Paket No {resp_packet_no} (Beklenen: {expected_packet_no}, Checksum: 0x{checksum_resp:04X})")
            
            expected_packet_no += 1
        
        data_offset += chunk_len
        packet_num += 1
        
        # İlerleme göster
        progress = (data_offset / total_size) * 100
        print(f"  İlerleme: {progress:.1f}% ({data_offset}/{total_size} byte)")
        
        time.sleep(0.05)  # Kısa bekleme
    
    print(f"\n{'='*60}")
    print(f"✓✓✓ Güncelleme tamamlandı! ✓✓✓")
    print(f"{'='*60}")
    
    # Güncelleme sonrası APROM'a geçiş ve reset
    print(f"\n[SON] CMD_RUN_APROM gönderiliyor (reset için)...")
    print(f"  → Bu komut bootloader'ı resetleyecek ve APROM'a (0x00000000) atlayacak")
    print(f"  → Yeni firmware çalışmaya başlayacak")
    
    run_aprom_packet = create_packet(CMD_RUN_APROM)
    
    if send_packet(ser, run_aprom_packet):
        print(f"✓ CMD_RUN_APROM gönderildi")
        
        # Reset'in gerçekleşmesi için bekle
        # CMD_RUN_APROM gönderildikten sonra bootloader reset atar
        # Port kapanabilir, bu normaldir
        time.sleep(0.5)
        
        # Port hala açık mı kontrol et
        if ser.is_open:
            # Reset sonrası UART'tan mesaj gelip gelmediğini kontrol et
            print(f"\nReset sonrası kontrol ediliyor...")
            time.sleep(1.0)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                ascii_text = response.decode('ascii', errors='ignore')
                print(f"✓ Reset sonrası mesaj alındı:")
                print(f"  {ascii_text[:100]}")
                
                # Yeni firmware'den mesaj geliyor mu kontrol et
                if "CPU @" in ascii_text or "Bootloader" not in ascii_text:
                    print(f"  → Yeni firmware çalışıyor gibi görünüyor!")
                else:
                    print(f"  ⚠ Bootloader mesajı geliyor (firmware çalışmıyor olabilir)")
            else:
                print(f"⚠ Reset sonrası mesaj gelmedi")
                print(f"  → Port kapalı olabilir (normal)")
                print(f"  → Veya firmware çalışmıyor olabilir")
        else:
            print(f"⚠ Port kapandı (reset atıldı, normal)")
            print(f"  → Yeni firmware çalışıyor olmalı")
    else:
        print(f"⚠ CMD_RUN_APROM gönderilemedi")
        print(f"  → Kartı manuel olarak reset yapın")
        print(f"  → Reset sonrası yeni firmware çalışmalı")
    
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
        print("⚠️  ÖNEMLİ: Bootloader sadece reset sonrası 300ms içinde aktif!")
        print("⚠️  Script sürekli CMD_CONNECT gönderecek, reset yapınca yakalayacak...")
        print()
        print("Kartı RESET yapın (istediğiniz zaman)")
        print("Script otomatik olarak bootloader'ı yakalayacak...")
        print()
        print("Çıkmak için Ctrl+C tuşlarına basın\n")
        
        # Sürekli CMD_CONNECT gönder (reset sonrası yakalamak için)
        max_attempts = 1000  # Maksimum deneme sayısı
        attempt = 0
        connected = False
        
        # CMD_CONNECT paketi hazırla
        connect_packet = create_packet(CMD_CONNECT)
        
        print("🔄 Sürekli CMD_CONNECT gönderiliyor...")
        print("   (Reset yapınca bootloader yakalanacak)\n")
        
        while attempt < max_attempts and not connected:
            try:
                # Port durumunu kontrol et
                if not ser.is_open:
                    print(f"⚠ Port kapalı, yeniden açılıyor...")
                    try:
                        ser.open()
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"  ✗ Port açılamadı: {e}")
                        time.sleep(1.0)
                        continue
                
                # Buffer temizle
                try:
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                except:
                    # Buffer temizleme hatası, port'u yeniden aç
                    try:
                        ser.close()
                        time.sleep(0.5)
                        ser.open()
                        time.sleep(0.3)
                    except:
                        pass
                
                # CMD_CONNECT gönder
                if send_packet(ser, connect_packet):
                    # Kısa bekleme (bootloader yanıtı için)
                    time.sleep(0.01)
                    
                    # Yanıt var mı kontrol et
                    if ser.in_waiting >= 4:  # En az 4 byte yanıt bekliyoruz
                        response = receive_response(ser, timeout=0.1)
                        
                        if response and len(response) >= 64:
                            # Yanıtın bootloader'dan mı geldiğini kontrol et
                            first_bytes = response[:4]
                            is_ascii = all(32 <= b <= 126 for b in first_bytes[:4])
                            
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
                                
                                # Cihaz ID'sini almak için CMD_GET_DEVICEID gönder
                                print(f"\n  Cihaz ID'si alınıyor...")
                                device_id_packet = create_packet(CMD_GET_DEVICEID)
                                if send_packet(ser, device_id_packet):
                                    time.sleep(0.15)
                                    device_response = receive_response(ser, timeout=0.5)
                                    if device_response and len(device_response) >= 64:
                                        device_id = bytes_to_uint32(device_response, 8)
                                        checksum_dev = (device_response[1] << 8) | device_response[0]
                                        print(f"  ✓✓✓ CİHAZ ID YAKALANDI! ✓✓✓")
                                        print(f"  Cihaz ID: 0x{device_id:08X}")
                                        print(f"  Checksum: 0x{checksum_dev:04X}")
                                    else:
                                        print(f"  ⚠ Cihaz ID yanıtı alınamadı")
                                        if device_response:
                                            print(f"  Kısmi yanıt: {device_response.hex()[:50]}")
                                else:
                                    print(f"  ⚠ CMD_GET_DEVICEID gönderilemedi")
                                
                                print()  # Boş satır
                                
                                connected = True
                                break
                
                attempt += 1
                
                # Her 100 denemede bir durum göster
                if attempt % 100 == 0:
                    print(f"  Deneme: {attempt}... (Reset yapın)")
                
                # Kısa bekleme (CPU kullanımını azaltmak için)
                time.sleep(0.01)
                
            except (serial.SerialException, OSError) as e:
                # Port I/O hatası - port'u yeniden aç
                print(f"⚠ Port I/O hatası: {e}, yeniden açılıyor...")
                try:
                    ser.close()
                    time.sleep(0.5)
                    ser.open()
                    time.sleep(0.3)
                    print(f"  ✓ Port yeniden açıldı")
                except Exception as e2:
                    print(f"  ✗ Port açılamadı: {e2}")
                    time.sleep(1.0)
                attempt += 1
                continue
                
            except KeyboardInterrupt:
                print("\n\nProgram sonlandırılıyor...")
                return
            except Exception as e:
                # Hataları görmezden gel, devam et
                pass
        
        if not connected:
            print(f"\n✗ Bootloader yakalanamadı ({max_attempts} deneme)")
            print("  → Reset yapıldı mı kontrol edin")
            return
        
        time.sleep(0.1)
        
        # APROM güncellemesi
        # APROM güncellemesi yap
        # erase_before_update=True: Güncelleme öncesi tam silme (önerilen ama dikkatli kullanın!)
        if send_update_aprom(ser, bin_data, erase_before_update=False):
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

