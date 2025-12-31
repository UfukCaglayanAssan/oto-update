#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton ISP Bootloader - Resmi Protokol Uyumlu
Raspberry Pi'de calisir ve Nuvoton'un resmi ISP protokolunu kullanir
"""

import serial
import serial.tools.list_ports
import sys
import time
import os

# UART ayarlari
BAUD_RATE = 115200
TIMEOUT = 2
WRITE_TIMEOUT = 5
MAX_PKT_SIZE = 64

# Nuvoton ISP Komutlari (isp_user.h'den)
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
    """Mevcut serial portlari listeler"""
    ports = serial.tools.list_ports.comports()
    print("Mevcut Serial Portlar:")
    for port in ports:
        print(f"  - {port.device}: {port.description}")
    return ports

def open_serial_port(port_name=None, baud_rate=BAUD_RATE):
    """Serial port'u acar"""
    try:
        if port_name is None:
            # Once PySerial ile portlari bul
            ports = serial.tools.list_ports.comports()
            if ports:
                print("Mevcut portlar:")
                for p in ports:
                    print(f"  - {p.device}: {p.description}")
                # Ilk bulunan portu dene
                port_name = ports[0].device
                print(f"Otomatik secilen port: {port_name}")
            else:
                # PySerial port bulamazsa standart portlari dene
                common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyAMA0', '/dev/ttyS0']
                for port in common_ports:
                    try:
                        ser = serial.Serial(port, baud_rate, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                                          rtscts=False, dsrdtr=False, xonxoff=False)
                        print(f"Port acildi: {port}")
                        return ser
                    except (serial.SerialException, FileNotFoundError):
                        continue
                raise serial.SerialException("Uygun port bulunamadi")

        # Belirtilen portu ac
        ser = serial.Serial(port_name, baud_rate, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        print(f"Port acildi: {port_name}")
        return ser

    except FileNotFoundError as e:
        print(f"[X] Hata: Port bulunamadi - {e}")
        print()

        # Mevcut portlari goster
        ports = serial.tools.list_ports.comports()
        if ports:
            print("Mevcut portlar:")
            for p in ports:
                print(f"  [OK] {p.device}: {p.description}")
            print()
            print(f"ONERILEN: {ports[0].device} portunu kullanin!")
            print()
            print(f"Kullanim:")
            print(f"  python3 uart_receiver_nuvoton.py {ports[0].device} NuvotonM26x-Bootloader-Test.bin")
        else:
            print("Kontrol edin:")
            print("  1. USB-UART donusturucu bagli mi?")
            print("  2. USB kablosu calisiyor mu?")
            print("  3. Port adi dogru mu?")
            print()
            print("Mevcut portlari gormek icin:")
            print("  python3 quick_port_check.py")
            print("  veya")
            print("  ls -l /dev/tty* | grep -E 'ACM|USB'")
        sys.exit(1)
    except serial.SerialException as e:
        print(f"[X] Hata: Port acilamadi - {e}")
        print()

        # Port kullanimini kontrol et
        import subprocess
        try:
            result = subprocess.run(['lsof', port_name], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                print("  Port baska bir program tarafindan kullaniliyor:")
                print(result.stdout)
                print()
                print("Cozum:")
                print("  1. Diger programi kapatin (uart_listener.py gibi)")
                print("  2. Veya farkli bir port kullanin")
        except:
            pass

        print("Kontrol edin:")
        print("  1. Port baska bir program tarafindan kullaniliyor olabilir")
        print("     → lsof | grep ttyACM0  ile kontrol edin")
        print("  2. Port izinleri yeterli mi? (sudo gerekebilir)")
        print("  3. USB-UART donusturucu driver'i yuklu mu?")
        print()

        # Mevcut portlari goster
        ports = serial.tools.list_ports.comports()
        if ports:
            print("Mevcut portlar:")
            for p in ports:
                print(f"  - {p.device}: {p.description}")
        sys.exit(1)

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

def calculate_checksum(data):
    """16-bit checksum hesaplama (Nuvoton protokolu)"""
    checksum = 0
    for byte in data:
        checksum += byte
    return checksum & 0xFFFF  # 16-bit

def create_packet(cmd, param1=0, param2=0, data=None, is_first_packet=False):
    """
    64 byte Nuvoton paketi olusturur

    ISP_UART protokolune gore:
    - Byte 0-3: CMD
    - Byte 4-7: Padding (pu8Src += 8 ile atlanir)
    - Byte 8+: Data veya parametreler
    """
    packet = bytearray(MAX_PKT_SIZE)

    # Byte 0-3: Komut (uint32_t, little-endian)
    packet[0:4] = uint32_to_bytes(cmd)

    # CMD_SYNC_PACKNO icin ozel format: Byte 8-11'de paket numarasi
    if cmd == CMD_SYNC_PACKNO:
        packet[8:12] = uint32_to_bytes(param1)  # Paket numarasi
        return packet

    # Ilk paket icin ozel format (CMD_UPDATE_APROM):
    # ISP_UART kodunda: pu8Src += 8 yapiliyor, sonra:
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
            data_len = min(len(data), 48)  # Ilk pakette maksimum 48 byte veri
            packet[16:16+data_len] = data[:data_len]
    else:
        # Devam paketleri icin:
        # Byte 0-3: CMD
        # Byte 4-7: Ignore edilir (bootloader kullanmiyor)
        # Byte 8-63: Veri (56 byte) - pu8Src += 8 yapildiktan sonra byte 8'den basliyor
        if data:
            data_len = min(len(data), 56)  # Devam paketlerinde maksimum 56 byte veri
            packet[8:8+data_len] = data[:data_len]

    return packet

def send_packet(ser, packet, retry=False):
    """64 byte paketi gonderir"""
    if len(packet) != MAX_PKT_SIZE:
        print(f"  HATA: Paket boyutu {len(packet)} byte, {MAX_PKT_SIZE} byte olmali!")
        return False

    try:
        # Port yazilabilir mi kontrol et
        if not ser.writable():
            print(f"[X] Port yazilabilir degil!")
            return False

        # Output buffer kontrolu
        if ser.out_waiting > 100:
            print(f"  Output buffer dolu ({ser.out_waiting} byte), temizleniyor...")
            ser.reset_output_buffer()
            time.sleep(0.1)

        # Buffer temizle
        ser.reset_output_buffer()
        time.sleep(0.05)

        # Paketi byte-byte gonder (timeout'u onlemek icin)
        total_written = 0

        # Once test byte gonder
        try:
            test_byte = bytes([packet[0]])
            test_written = ser.write(test_byte)
            if test_written == 0:
                raise serial.SerialTimeoutException("Test byte yazilamadi")
            ser.flush()
            time.sleep(0.01)
        except serial.SerialTimeoutException:
            print(f"  Test byte timeout, port yeniden aciliyor...")
            ser.close()
            time.sleep(1.0)
            ser.open()
            time.sleep(0.5)

        # Paketi chunk'lar halinde gonder (daha hizli ve guvenilir)
        chunk_size = 16  # 16 byte chunk'lar
        try:
            for i in range(0, len(packet), chunk_size):
                chunk = packet[i:i+chunk_size]
                bytes_written = ser.write(chunk)
                if bytes_written > 0:
                    total_written += bytes_written
                ser.flush()  # Her chunk'tan sonra flush
                time.sleep(0.001)  # Kisa bekleme
        except (serial.SerialTimeoutException, serial.SerialException, OSError) as e:
            # I/O hatasi - port donmus olabilir
            print(f"  Chunk gonderme hatasi: {e}")
            # Port'u yeniden acmayi dene
            try:
                ser.close()
                time.sleep(0.5)
                ser.open()
                time.sleep(0.3)
            except:
                pass
            # Kalan byte'lari gondermeyi dene
            remaining = packet[total_written:]
            if remaining:
                try:
                    ser.write(remaining)
                    total_written += len(remaining)
                except:
                    pass

        if total_written != MAX_PKT_SIZE:
            print(f"  Uyari: {total_written}/{MAX_PKT_SIZE} byte yazildi")
            # Yine de devam et

        # Flush islemi (timeout ile)
        start_time = time.time()
        while ser.out_waiting > 0:
            if time.time() - start_time > 1.0:  # 1 saniye timeout
                print(f"  Flush timeout, kalan: {ser.out_waiting} byte")
                break
            time.sleep(0.01)

        ser.flush()

        return True

    except (serial.SerialTimeoutException, serial.SerialException, OSError) as e:
        print(f"  Port hatasi: {e}")
        print(f"  → Port yeniden aciliyor...")
        # Port'u yeniden acmayi dene
        try:
            ser.close()
            time.sleep(0.5)
            ser.open()
            time.sleep(0.3)
            print(f"  [OK] Port yeniden acildi")
            # Tekrar dene (sadece 1 kez)
            if not retry:
                return send_packet(ser, packet, retry=True)
            else:
                return False
        except Exception as e2:
            print(f"  [X] Port yeniden acilamadi: {e2}")
            return False
    except Exception as e:
        print(f"[X] Paket gonderme hatasi: {e}")
        return False

def receive_response(ser, timeout=1.0):
    """64 byte yanit paketi alir"""
    start_time = time.time()
    response = bytearray()
    
    # DEBUG: Baslangic durumu
    initial_waiting = ser.in_waiting
    if initial_waiting > 0:
        print(f"  [DEBUG] receive_response: Baslangicta {initial_waiting} byte bekliyor")

    while len(response) < MAX_PKT_SIZE:
        if time.time() - start_time > timeout:
            # DEBUG: Timeout durumu
            print(f"  [DEBUG] receive_response: Timeout! Alinan: {len(response)}/{MAX_PKT_SIZE} byte")
            if len(response) > 0:
                print(f"  [DEBUG] Kismi yanit: {response.hex()[:64]}")
            return None

        if ser.in_waiting > 0:
            data = ser.read(min(ser.in_waiting, MAX_PKT_SIZE - len(response)))
            response.extend(data)
            # DEBUG: Her okuma sonrasi
            if len(response) > 0 and len(response) % 16 == 0:
                print(f"  [DEBUG] receive_response: {len(response)}/{MAX_PKT_SIZE} byte alindi")

        time.sleep(0.01)
    
    # DEBUG: Tam yanit alindi
    if len(response) == MAX_PKT_SIZE:
        print(f"  [DEBUG] receive_response: Tam yanit alindi: {response[:16].hex()}")
    
    return bytes(response)

def send_connect(ser):
    """CMD_CONNECT gonderir ve yanit alir"""
    print("CMD_CONNECT gonderiliyor...")

    # Buffer temizle (cok hizli, timeout'u onlemek icin)
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.01)  # Cok kisa bekleme
    except Exception as e:
        print(f"    Buffer temizleme hatasi: {e}")

    # CMD_CONNECT paketi olustur
    # ISP_UART: CMD_CONNECT icin ozel format yok, sadece komut gonderilir
    packet = create_packet(CMD_CONNECT)
    
    # DEBUG: Paket formatini kontrol et
    print(f"  [DEBUG] CMD_CONNECT paketi (ilk 16 byte): {packet[:16].hex()}")
    cmd_value = bytes_to_uint32(packet, 0)
    print(f"  [DEBUG] CMD degeri: 0x{cmd_value:08X} (beklenen: 0x{CMD_CONNECT:08X})")
    if cmd_value != CMD_CONNECT:
        print(f"  [HATA] CMD degeri yanlis!")

    # HEMEN gonder (reset sonrasi 300ms icinde olmali)
    if not send_packet(ser, packet):
        print("[X] CMD_CONNECT gonderilemedi")
        return False

    print(f"[OK] CMD_CONNECT gonderildi")

    # Cok kisa bekleme (bootloader'in islemesi icin)
    time.sleep(0.05)

    # Yanit bekle (bootloader hizli yanit verir)
    print("Yanit bekleniyor (0.3 saniye)...")
    response = receive_response(ser, timeout=0.3)

    if response:
        # Yanitin bootloader'dan mi yoksa application'dan mi geldigini kontrol et
        # Bootloader yaniti: Ilk 4 byte checksum+packet_no, sonra APROM size
        # Application yaniti: ASCII metin

        # Ilk byte'lari kontrol et (bootloader binary, application ASCII)
        first_bytes = response[:4]
        is_ascii = all(32 <= b <= 126 for b in first_bytes[:4])  # Printable ASCII

        if is_ascii:
            # Application'dan gelen yanit
            ascii_text = response[:64].decode('ascii', errors='ignore')
            print(f"  UYARI: Application yaniti alindi (bootloader degil)!")
            print(f"  Yanit: {ascii_text[:50]}...")
            print(f"  → Bootloader modunda degil, application calisiyor")
            print(f"  → Reset sonrasi cok gec gonderilmis olabilir (300ms icinde olmali)")
            return False

        # Bootloader yaniti
        checksum = (response[1] << 8) | response[0]  # 16-bit little-endian
        
        # DEBUG: Tam yaniti goster (parse etmeden once)
        print(f"  [DEBUG] Tam Yanit (ilk 16 byte): {response[:16].hex()}")
        
        # Paket numarasi: Byte 4-5'i oku (16-bit little-endian)
        # ISP_UART: outpw(pu8Response + 4, u32PackNo) -> Byte 4-7'ye yaziyor
        # Ama byte 4-5'te gercek deger var (little-endian)
        packet_no_raw = bytes_to_uint32(response, 4)
        packet_no = response[4] | (response[5] << 8)  # 16-bit little-endian
        print(f"  [DEBUG] Byte 4-7 (Paket No): {response[4:8].hex()} -> Raw: {packet_no_raw}, Normalized: {packet_no}")
        
        # APROM boyutu: Byte 8-11'i oku (32-bit little-endian)
        aprom_size = bytes_to_uint32(response, 8)
        print(f"  [DEBUG] Byte 8-11 (APROM Size): {response[8:12].hex()} -> {aprom_size} (0x{aprom_size:08X})")
        
        # DataFlash adresi: Byte 12-15'i oku (32-bit little-endian)
        dataflash_addr = bytes_to_uint32(response, 12)
        print(f"  [DEBUG] Byte 12-15 (DataFlash): {response[12:16].hex()} -> 0x{dataflash_addr:08X}")

        # Config verileri (Byte 16-31) - ReadData ile doldurulmus olabilir
        config_data = response[16:32] if len(response) >= 32 else None

        print(f"[OK][OK][OK] BOOTLOADER YANITI ALINDI! [OK][OK][OK]")
        print(f"  Checksum: 0x{checksum:04X}")
        print(f"  Paket No: {packet_no}")
        print(f"  APROM Boyutu: {aprom_size} byte (0x{aprom_size:08X})")
        print(f"  DataFlash Adresi: 0x{dataflash_addr:08X}")

        # KRITIK: Paket numarasi senkronizasyonu (ISP_UART kodunda var!)
        # ISP_UART: if(u32Lcmd == CMD_SYNC_PACKNO) { u32PackNo = inpw(pu8Src); }
        print(f"\n  [KRITIK] Paket numarasi senkronize ediliyor...")
        sync_packet = create_packet(CMD_SYNC_PACKNO, 1)  # Byte 8-11'de paket numarasi = 1
        if send_packet(ser, sync_packet):
            time.sleep(0.2)  # Daha uzun bekleme
            # Input buffer'da veri var mi kontrol et
            if ser.in_waiting > 0:
                print(f"  Input buffer: {ser.in_waiting} byte bekliyor")
            sync_response = receive_response(ser, timeout=0.5)  # Timeout artirildi
            if sync_response:
                sync_packet_no = bytes_to_uint32(sync_response, 4)
                print(f"  [OK] Paket numarasi senkronize edildi: {sync_packet_no}")
            else:
                print(f"    Paket numarasi senkronizasyon yaniti alinamadi (devam ediliyor)")
                if ser.in_waiting > 0:
                    partial = ser.read(ser.in_waiting)
                    print(f"    Kismi yanit: {partial.hex()[:50]}")
        else:
            print(f"    CMD_SYNC_PACKNO gonderilemedi (devam ediliyor)")

        # Cihaz ID'sini almak icin CMD_GET_DEVICEID gonder
        print(f"\n  Cihaz ID'si aliniyor...")
        device_id_packet = create_packet(CMD_GET_DEVICEID)
        if send_packet(ser, device_id_packet):
            time.sleep(0.3)  # Daha uzun bekleme
            # Input buffer'da veri var mi kontrol et
            if ser.in_waiting > 0:
                print(f"  Input buffer: {ser.in_waiting} byte bekliyor")
            device_response = receive_response(ser, timeout=1.0)  # Timeout artirildi
            if device_response and len(device_response) >= 64:
                device_id = bytes_to_uint32(device_response, 8)
                checksum_dev = (device_response[1] << 8) | device_response[0]
                print(f"  [OK][OK][OK] CIHAZ ID YAKALANDI! [OK][OK][OK]")
                print(f"  Cihaz ID: 0x{device_id:08X}")
                print(f"  Checksum: 0x{checksum_dev:04X}")
                print(f"  Tam Yanit (ilk 16 byte): {device_response[:16].hex()}")
            else:
                print(f"    Cihaz ID yaniti alinamadi")
                if device_response:
                    print(f"  Kismi yanit: {device_response.hex()[:50]} (boyut: {len(device_response)})")
                else:
                    print(f"  Input buffer: {ser.in_waiting} byte")
                    # Buffer'da kalan veriyi oku
                    if ser.in_waiting > 0:
                        partial = ser.read(ser.in_waiting)
                        print(f"  Buffer'daki veri: {partial.hex()[:50]}")
        else:
            print(f"    CMD_GET_DEVICEID gonderilemedi")

        return True
    else:
        print("[X] Yanit alinamadi (timeout)")
        print(f"  Input buffer: {ser.in_waiting} byte")
        if ser.in_waiting > 0:
            partial = ser.read(ser.in_waiting)
            ascii_text = partial.decode('ascii', errors='ignore')
            print(f"  Kismi yanit (ASCII): {ascii_text[:50]}")
            print(f"  Kismi yanit (Hex): {partial.hex()[:50]}")
        return False

def send_update_aprom(ser, bin_data, erase_before_update=True):
    """APROM guncellemesi yapar"""
    total_size = len(bin_data)
    start_address = 0x00000000  # APROM baslangic adresi

    print(f"\n{'='*60}")
    print(f"APROM Guncelleme Baslatiliyor...")
    print(f"{'='*60}")
    print(f"Dosya boyutu: {total_size} byte")
    print(f"Baslangic adresi: 0x{start_address:08X}")

    # ONEMLI: Guncelleme oncesi tam silme (opsiyonel ama onerilen)
    if erase_before_update:
        print(f"\n[0/3] CMD_ERASE_ALL gonderiliyor (tum APROM silinecek)...")
        erase_packet = create_packet(CMD_ERASE_ALL)
        if send_packet(ser, erase_packet):
            print(f"[OK] CMD_ERASE_ALL gonderildi")
            # Silme islemi zaman alir
            time.sleep(2.0)  # Flash silme icin yeterli sure
            # Input buffer'da veri var mi kontrol et
            if ser.in_waiting > 0:
                print(f"  Input buffer: {ser.in_waiting} byte bekliyor")
            erase_response = receive_response(ser, timeout=2.0)  # Timeout artirildi
            if erase_response:
                # DEBUG
                print(f"  [DEBUG] CMD_ERASE_ALL yaniti (ilk 16 byte): {erase_response[:16].hex()}")
                
                # Paket numarasi: Byte 4-5'i oku (16-bit little-endian)
                erase_packet_no_raw = bytes_to_uint32(erase_response, 4)
                erase_packet_no = erase_response[4] | (erase_response[5] << 8)  # 16-bit little-endian
                print(f"  [DEBUG] Byte 4-7 (Paket No): {erase_response[4:8].hex()} -> Raw: {erase_packet_no_raw}, Normalized: {erase_packet_no}")
                
                print(f"[OK] Silme tamamlandi, Paket No: {erase_packet_no}")
            else:
                print(f"[!] Silme yaniti alinamadi (devam ediliyor)")
                if ser.in_waiting > 0:
                    partial = ser.read(ser.in_waiting)
                    print(f"  Kismi yanit: {partial.hex()[:50]}")
        else:
            print(f"[!] CMD_ERASE_ALL gonderilemedi (devam ediliyor)")

    # Ilk paket: CMD_UPDATE_APROM + adres + boyut
    print(f"\n[1/3] CMD_UPDATE_APROM (baslangic) gonderiliyor...")
    first_data = bin_data[:48] if len(bin_data) >= 48 else bin_data  # Ilk 48 byte (byte 16-63)
    first_packet = create_packet(CMD_UPDATE_APROM, start_address, total_size, first_data, is_first_packet=True)

    if not send_packet(ser, first_packet):
        print("[X] Ilk paket gonderilemedi")
        return False

    print(f"[OK] Ilk paket gonderildi ({len(first_data)} byte veri)")

    # Yanit bekle (daha uzun timeout - flash yazma zaman alir)
    # Ilk paket sonrasi flash yazma yapiliyor, bu zaman alabilir
    time.sleep(0.5)  # Flash yazma icin ekstra bekleme
    response = receive_response(ser, timeout=3.0)  # Timeout artirildi
    if response:
        # DEBUG
        print(f"  [DEBUG] Ilk CMD_UPDATE_APROM yaniti (ilk 16 byte): {response[:16].hex()}")
        
        # Paket numarasi: Byte 4-5'i oku (16-bit little-endian)
        packet_no_raw = bytes_to_uint32(response, 4)
        packet_no = response[4] | (response[5] << 8)  # 16-bit little-endian
        print(f"  [DEBUG] Byte 4-7 (Paket No): {response[4:8].hex()} -> Raw: {packet_no_raw}, Normalized: {packet_no}")
        
        print(f"[OK] Yanit alindi, Paket No: {packet_no}")
        # NOT: Bootloader paket numarasini her yanitta 2 artiriyor
        # CMD_ERASE_ALL sonrasi: 6
        # Ilk CMD_UPDATE_APROM sonrasi: 8 (beklenen)
        # Ilk yanit paket numarasini kullanarak devam paketleri icin beklenen degeri hesapla
        first_response_packet_no = packet_no
        # Sonraki paket icin beklenen deger: ilk yanit + 2
        expected_packet_no = first_response_packet_no + 2
        print(f"  Sonraki paket icin beklenen: {expected_packet_no}")
    else:
        print(f"[!] Ilk paket yaniti alinamadi (devam ediliyor)")
        # Ilk yanit alinamadi, varsayilan deger kullan
        expected_packet_no = 10  # CMD_ERASE_ALL=6, ilk UPDATE=8, ilk devam=10
        first_response_packet_no = None

    # Devam paketleri (56 byte veri her pakette)
    data_offset = 48  # Ilk pakette 48 byte gonderildi
    packet_num = 2

    while data_offset < total_size:
        # 56 byte veri al
        chunk_data = bin_data[data_offset:data_offset+56]
        chunk_len = len(chunk_data)

        # Paketi 64 byte'a tamamla
        packet = create_packet(CMD_UPDATE_APROM, packet_num, 0, chunk_data)

        print(f"[{packet_num}] Paket gonderiliyor... ({chunk_len} byte veri, offset: {data_offset})")

        if not send_packet(ser, packet):
            print(f"[X] Paket {packet_num} gonderilemedi")
            return False

        # Yanit bekle (daha uzun timeout - flash yazma zaman alir)
        response = receive_response(ser, timeout=3.0)  # Timeout artirildi
        if response:
            # Paket numarasi: Byte 4-5'i oku (16-bit little-endian)
            resp_packet_no_raw = bytes_to_uint32(response, 4)
            resp_packet_no = response[4] | (response[5] << 8)  # 16-bit little-endian
            checksum_resp = (response[1] << 8) | response[0]

            # Paket numarasi kontrolu
            if expected_packet_no is not None:
                if resp_packet_no == expected_packet_no:
                    print(f"  [OK] Yanit: Paket No {resp_packet_no} (Checksum: 0x{checksum_resp:04X})")
                else:
                    # Paket numarasi uyumsuzlugu
                    diff = resp_packet_no - expected_packet_no
                    if abs(diff) <= 4:
                        print(f"  [!] Yanit: Paket No {resp_packet_no} (Beklenen: {expected_packet_no}, Fark: {diff:+d})")
                        # Bootloader'in gercek paket numarasini kullan ve takibi buna gore ayarla
                        expected_packet_no = resp_packet_no
                    else:
                        print(f"  [!] Yanit: Paket No {resp_packet_no} (Beklenen: {expected_packet_no}, Checksum: 0x{checksum_resp:04X})")
                
                # Bootloader her yanitta paket numarasini 2 artiriyor
                expected_packet_no += 2
            else:
                # Paket numarasi takibi yapilmiyor, sadece goster
                print(f"  [OK] Yanit: Paket No {resp_packet_no} (Checksum: 0x{checksum_resp:04X})")
        else:
            # Yanit alinamadi (timeout) - flash yazma devam ediyor olabilir
            print(f"  [!] Yanit alinamadi (timeout) - flash yazma devam ediyor olabilir")
            # Timeout olsa bile devam et (bootloader flash yaziyor olabilir)

        data_offset += chunk_len
        packet_num += 1

        # Ilerleme goster
        progress = (data_offset / total_size) * 100
        print(f"  Ilerleme: {progress:.1f}% ({data_offset}/{total_size} byte)")

        time.sleep(0.05)  # Kisa bekleme

    print(f"\n{'='*60}")
    print(f"[OK][OK][OK] Guncelleme tamamlandi! [OK][OK][OK]")
    print(f"{'='*60}")

    # Guncelleme sonrasi APROM'a gecis ve reset
    print(f"\n[SON] CMD_RUN_APROM gonderiliyor (reset icin)...")
    run_aprom_packet = create_packet(CMD_RUN_APROM)

    if send_packet(ser, run_aprom_packet):
        print(f"[OK] CMD_RUN_APROM gonderildi")
        print(f"  → Bootloader reset atacak ve yeni firmware calisacak")
        print(f"  → Reset sonrasi LED yanip sonmeli")

        # Reset'in gerceklesmesi icin bekle
        time.sleep(1.0)

        # Reset sonrasi UART'tan mesaj gelip gelmedigini kontrol et
        print(f"\nReset sonrasi kontrol ediliyor...")
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"[OK] Reset sonrasi mesaj alindi: {response[:50].decode('ascii', errors='ignore')}")
        else:
            print(f"  Reset sonrasi mesaj gelmedi (normal olabilir)")
    else:
        print(f"  CMD_RUN_APROM gonderilemedi (manuel reset gerekebilir)")
        print(f"  → Karti manuel olarak reset yapin")

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

    # Mevcut portlari goster
    find_serial_ports()
    print()

    if port_name:
        print(f"Belirtilen port: {port_name}")
    else:
        print("Port belirtilmedi, otomatik tespit edilecek...")

    print(f"Binary dosya: {bin_file}")
    print()

    # Binary dosyayi oku
    if not os.path.exists(bin_file):
        print(f"[X] HATA: Dosya bulunamadi: {bin_file}")
        sys.exit(1)

    with open(bin_file, 'rb') as f:
        bin_data = f.read()

    print(f"[OK] Binary dosya okundu: {len(bin_data)} byte")
    print()

    # Serial port'u ac
    ser = open_serial_port(port_name, BAUD_RATE)

    # Port durumunu kontrol et
    print(f"Baud Rate: {ser.baudrate}")
    print(f"Port acik: {ser.is_open}")
    print(f"Port yazilabilir: {ser.writable()}")
    print(f"Port okunabilir: {ser.readable()}")
    print()

    # Port'u temizle
    try:
        print("Port buffer'lari temizleniyor...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.3)  # Biraz daha uzun bekle
        print(f"  Output buffer: {ser.out_waiting} byte")
        print(f"  Input buffer: {ser.in_waiting} byte")
    except Exception as e:
        print(f"    Buffer temizleme hatasi: {e}")

    print()

    try:
        print("  ONEMLI: Bootloader sadece reset sonrasi 300ms icinde aktif!")
        print("  Script surekli CMD_CONNECT gonderecek, reset yapinca yakalayacak...")
        print()
        print("Karti RESET yapin (istediginiz zaman)")
        print("Script otomatik olarak bootloader'i yakalayacak...")
        print()
        print("Cikmak icin Ctrl+C tuslarina basin\n")

        # Surekli CMD_CONNECT gonder (reset sonrasi yakalamak icin)
        max_attempts = 1000  # Maksimum deneme sayisi
        attempt = 0
        connected = False

        # CMD_CONNECT paketi hazirla
        connect_packet = create_packet(CMD_CONNECT)

        print("[>] Surekli CMD_CONNECT gonderiliyor...")
        print("   (Reset yapinca bootloader yakalanacak)\n")

        while attempt < max_attempts and not connected:
            try:
                # Port durumunu kontrol et
                if not ser.is_open:
                    print(f"  Port kapali, yeniden aciliyor...")
                    try:
                        ser.open()
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"  [X] Port acilamadi: {e}")
                        time.sleep(1.0)
                        continue

                # Buffer temizle
                try:
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                except:
                    # Buffer temizleme hatasi, port'u yeniden ac
                    try:
                        ser.close()
                        time.sleep(0.5)
                        ser.open()
                        time.sleep(0.3)
                    except:
                        pass

                # CMD_CONNECT gonder
                if send_packet(ser, connect_packet):
                    # Kisa bekleme (bootloader yaniti icin)
                    time.sleep(0.01)

                    # Yanit var mi kontrol et
                    if ser.in_waiting >= 4:  # En az 4 byte yanit bekliyoruz
                        response = receive_response(ser, timeout=0.1)

                        if response and len(response) >= 64:
                            # Yanitin bootloader'dan mi geldigini kontrol et
                            first_bytes = response[:4]
                            is_ascii = all(32 <= b <= 126 for b in first_bytes[:4])

                        if not is_ascii:
                            # Bootloader yaniti!
                            checksum = (response[1] << 8) | response[0]
                            packet_no = bytes_to_uint32(response, 4)
                            aprom_size = bytes_to_uint32(response, 8)
                            dataflash_addr = bytes_to_uint32(response, 12)

                            print(f"\n[OK][OK][OK] BOOTLOADER YAKALANDI! [OK][OK][OK]")
                            print(f"  Checksum: 0x{checksum:04X}")
                            print(f"  Paket No: {packet_no}")
                            print(f"  APROM Boyutu: {aprom_size} byte (0x{aprom_size:08X})")
                            print(f"  DataFlash Adresi: 0x{dataflash_addr:08X}")

                            # KRITIK: Paket numarasi senkronizasyonu
                            print(f"\n  [KRITIK] Paket numarasi senkronize ediliyor...")
                            sync_packet = create_packet(CMD_SYNC_PACKNO, 1)  # Byte 8-11'de paket numarasi = 1
                            if send_packet(ser, sync_packet):
                                time.sleep(0.1)
                                sync_response = receive_response(ser, timeout=0.3)
                                if sync_response:
                                    sync_packet_no = bytes_to_uint32(sync_response, 4)
                                    print(f"  [OK] Paket numarasi senkronize edildi: {sync_packet_no}")
                                else:
                                    print(f"  [!] Paket numarasi senkronizasyon yaniti alinamadi (devam ediliyor)")
                            else:
                                print(f"  [!] CMD_SYNC_PACKNO gonderilemedi (devam ediliyor)")

                            # Cihaz ID'sini almak icin CMD_GET_DEVICEID gonder
                            print(f"\n  Cihaz ID'si aliniyor...")
                            device_id_packet = create_packet(CMD_GET_DEVICEID)
                            if send_packet(ser, device_id_packet):
                                time.sleep(0.15)
                                device_response = receive_response(ser, timeout=0.5)
                                if device_response and len(device_response) >= 64:
                                    device_id = bytes_to_uint32(device_response, 8)
                                    checksum_dev = (device_response[1] << 8) | device_response[0]
                                    print(f"  [OK][OK][OK] CIHAZ ID YAKALANDI! [OK][OK][OK]")
                                    print(f"  Cihaz ID: 0x{device_id:08X}")
                                    print(f"  Checksum: 0x{checksum_dev:04X}")
                                else:
                                    print(f"  [!] Cihaz ID yaniti alinamadi")
                                    if device_response:
                                        print(f"  Kismi yanit: {device_response.hex()[:50]}")
                            else:
                                print(f"  [!] CMD_GET_DEVICEID gonderilemedi")

                            print()  # Bos satir

                            connected = True
                            break

                attempt += 1

                # Her 100 denemede bir durum goster
                if attempt % 100 == 0:
                    print(f"  Deneme: {attempt}... (Reset yapin)")

                # Kisa bekleme (CPU kullanimini azaltmak icin)
                time.sleep(0.01)

            except (serial.SerialException, OSError) as e:
                # Port I/O hatasi - port'u yeniden ac
                print(f"  Port I/O hatasi: {e}, yeniden aciliyor...")
                try:
                    ser.close()
                    time.sleep(0.5)
                    ser.open()
                    time.sleep(0.3)
                    print(f"  [OK] Port yeniden acildi")
                except Exception as e2:
                    print(f"  [X] Port acilamadi: {e2}")
                    time.sleep(1.0)
                attempt += 1
                continue

            except KeyboardInterrupt:
                print("\n\nProgram sonlandiriliyor...")
                return
            except Exception as e:
                # Hatalari gormezden gel, devam et
                pass

        if not connected:
            print(f"\n[X] Bootloader yakalanamadi ({max_attempts} deneme)")
            print("  → Reset yapildi mi kontrol edin")
            return

        time.sleep(0.1)

        # APROM guncellemesi
        if send_update_aprom(ser, bin_data):
            print("\n[OK][OK][OK] Guncelleme basarili! [OK][OK][OK]")
        else:
            print("\n[X] Guncelleme basarisiz")

    except KeyboardInterrupt:
        print("\n\nProgram sonlandiriliyor...")
    except Exception as e:
        print(f"\n[X] Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ser.close()
        print("Port kapatildi.")

if __name__ == "__main__":
    main()