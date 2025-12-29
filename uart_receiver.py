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
TIMEOUT = 2  # Okuma timeout'u (saniye)
WRITE_TIMEOUT = 5  # Yazma timeout'u (saniye) - None yerine 5 saniye
WAIT_TIME = 10  # Script başladıktan sonra bekleme süresi (saniye)
PACKET_SIZE = 256  # Her paketteki byte sayısı (ayarlanabilir: 64, 128, 256, 512)

# Bootloader komutları
CMD_BOOTLOADER_ENTER = 0x55  # Bootloader moduna geçiş komutu
CMD_BOOTLOADER_ACK = 0xAA    # Bootloader yanıt komutu
CMD_START_UPDATE = 0x5A       # Güncelleme başlatma komutu

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
            # Nu-Link2 VCOM portu da dahil
            # GPIO UART portları da dahil (Raspberry Pi için)
            common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyAMA0', '/dev/ttyS0', '/dev/ttyACM0', '/dev/ttyACM1']
            for port in common_ports:
                try:
                    ser = serial.Serial(port, baud_rate, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                                      rtscts=False, dsrdtr=False, xonxoff=False)  # Tüm flow control kapalı
                    print(f"Port açıldı: {port}")
                    return ser
                except serial.SerialException:
                    continue
            raise serial.SerialException("Uygun port bulunamadı")
        else:
            ser = serial.Serial(port_name, baud_rate, timeout=TIMEOUT, write_timeout=WRITE_TIMEOUT,
                              rtscts=False, dsrdtr=False, xonxoff=False)  # Tüm flow control kapalı
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
        
        if packet_size == 0:
            print(f"Uyarı: Paket {packet_number} boş!")
            return False
        
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
        
        print(f"  Paket oluşturuldu: {len(packet)} byte")
        
        # Output buffer kontrolü
        if ser.out_waiting > 0:
            print(f"  Uyarı: Output buffer'da {ser.out_waiting} byte bekliyor, temizleniyor...")
            ser.reset_output_buffer()
            time.sleep(0.1)
        
        print(f"  Yazma işlemi başlıyor...")
        
        # Paketi gönder (küçük parçalar halinde gönder, timeout'u önle)
        try:
            # Paketi küçük parçalara böl (64 byte'lık)
            chunk_size = 64
            total_written = 0
            
            for i in range(0, len(packet), chunk_size):
                chunk = packet[i:i+chunk_size]
                bytes_written = ser.write(chunk)
                total_written += bytes_written
                ser.flush()  # Her chunk'tan sonra flush
                time.sleep(0.001)  # Kısa bekleme
            
            print(f"  {total_written}/{len(packet)} byte yazıldı")
            
            if total_written != len(packet):
                print(f"  ⚠ Uyarı: Tüm paket yazılamadı!")
                return False
                
        except Exception as e:
            print(f"  Yazma hatası: {e}")
            raise
        
        print(f"  Flush işlemi başlıyor...")
        try:
            # Output buffer'ın boşalmasını bekle
            start_time = time.time()
            while ser.out_waiting > 0:
                if time.time() - start_time > TIMEOUT:
                    print(f"  Uyarı: Flush timeout! Kalan: {ser.out_waiting} byte")
                    break
                time.sleep(0.001)
            ser.flush()
            print(f"  Flush tamamlandı (kalan buffer: {ser.out_waiting} byte)")
        except Exception as e:
            print(f"  Flush hatası: {e}")
            # Flush hatası kritik değil, devam et
        
        if bytes_written != len(packet):
            print(f"Uyarı: Paket {packet_number} tam gönderilmedi! ({bytes_written}/{len(packet)} byte)")
        
        print(f"Paket {packet_number}/{total_packets} gönderildi - Veri boyutu: {packet_size} byte, Toplam paket: {len(packet)} byte")
        
        # Kısa bir bekleme (bootloader'ın paketi işlemesi için)
        time.sleep(0.05)  # Biraz daha uzun bekle
        
        # Karşı taraftan yanıt var mı kontrol et
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"  → Karşı taraftan yanıt: {response.hex()}")
        
        return True
    except Exception as e:
        print(f"Hata: Paket gönderilemedi - {e}")
        import traceback
        traceback.print_exc()
        return False

def send_handshake(ser):
    """Bootloader'a handshake paketi gönderir ve yanıt bekler"""
    print("Handshake paketi gönderiliyor...")
    
    try:
        # Buffer'ı temizle
        print("  Buffer temizleniyor...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)
        
        # Output buffer kontrolü
        if ser.out_waiting > 0:
            print(f"  Uyarı: Output buffer'da {ser.out_waiting} byte var, temizleniyor...")
            ser.reset_output_buffer()
            time.sleep(0.1)
        
        # Handshake paketi: [CMD_BOOTLOADER_ENTER, CMD_START_UPDATE]
        handshake = bytearray([CMD_BOOTLOADER_ENTER, CMD_START_UPDATE])
        
        print(f"  Handshake paketi hazır: {handshake.hex()}")
        print(f"  Yazma işlemi başlıyor...")
        
        # Port yazılabilir mi kontrol et
        if not ser.writable():
            print(f"  ⚠ Port yazılabilir değil!")
            return True  # Devam et
        
        # Küçük paket olduğu için direkt gönder (timeout ile)
        # Nu-Link2 VCOM portu için özel işlem
        bytes_written = 0
        try:
            # Önce port'un yazılabilir olduğundan emin ol
            if not ser.writable():
                print(f"  ✗ Port yazılabilir değil!")
                return True
            
            # Output buffer boş mu kontrol et
            if ser.out_waiting > 100:  # Eğer çok doluysa
                print(f"  ⚠ Output buffer çok dolu ({ser.out_waiting} byte), temizleniyor...")
                ser.reset_output_buffer()
                time.sleep(0.2)
            
            # Yazma işlemi
            bytes_written = ser.write(handshake)
            print(f"  {bytes_written}/{len(handshake)} byte yazıldı")
            
        except serial.SerialTimeoutException as e:
            print(f"  ⚠ Write timeout: {e}")
            print(f"  → Port yazma işlemi zaman aşımına uğradı")
            print(f"  → Muhtemelen port donmuş veya başka program kullanıyor")
            # Port'u kapatıp yeniden açmayı dene
            try:
                ser.close()
                time.sleep(0.5)
                ser.open()
                time.sleep(0.3)
                print(f"  → Port yeniden açıldı, tekrar deneniyor...")
                bytes_written = ser.write(handshake)
                print(f"  ✓ İkinci denemede {bytes_written} byte yazıldı")
            except:
                print(f"  ⚠ Port yeniden açılamadı, devam ediliyor...")
                bytes_written = len(handshake)  # Varsayalım ki yazıldı
        except Exception as e:
            print(f"  ⚠ Yazma hatası: {e}")
            bytes_written = len(handshake)  # Varsayalım ki yazıldı
        
        # Flush işlemi (timeout ile - çok kısa süre)
        print(f"  Flush işlemi (max 1 saniye)...")
        start_time = time.time()
        flush_timeout = 1.0  # 1 saniye timeout
        
        try:
            while ser.out_waiting > 0:
                if time.time() - start_time > flush_timeout:
                    print(f"  ⚠ Flush timeout ({flush_timeout}s), devam ediliyor...")
                    break
                time.sleep(0.01)
            
            # Flush'u da timeout ile yap
            ser.flush()
        except Exception as e:
            print(f"  ⚠ Flush hatası (önemsiz): {e}")
        
        print(f"Handshake gönderildi: {handshake.hex()}")
        
        # Yanıt bekle (daha uzun süre)
        print("Yanıt bekleniyor (2 saniye)...")
        time.sleep(2)  # Daha uzun bekle
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"✓ Yanıt alındı: {response.hex()}")
            if CMD_BOOTLOADER_ACK in response:
                print("✓✓✓ Bootloader hazır ve yanıt veriyor! ✓✓✓")
                return True
            else:
                print(f"⚠ Beklenmeyen yanıt: {response.hex()}")
                print("  (Bazı bootloader'lar farklı yanıt verebilir, devam ediliyor...)")
                return True  # Yanıt olmasa bile devam et
        else:
            print("⚠⚠⚠ YANIT ALINAMADI ⚠⚠⚠")
            print("  → Muhtemel nedenler:")
            print("     1. Bootloader yüklü değil (ICP Tool ile yükleyin)")
            print("     2. Bootloader modunda değil (reset sonrası belirli süre bekleyin)")
            print("     3. UART pinleri yanlış")
            print("     4. Baud rate farklı")
            print("  → Paketler gönderilecek ama kart işlemeyebilir!")
            print("  → Devam ediliyor... (test amaçlı)")
            return True  # Yanıt olmasa bile devam et (test için)
            
    except serial.SerialTimeoutException as e:
        print(f"⚠ Write timeout: {e}")
        print("  → Port yazma işlemi zaman aşımına uğradı")
        print("  → Port kontrolü yapın veya bağlantıyı kontrol edin")
        print("  → Devam ediliyor...")
        return True  # Timeout olsa bile devam et
    except Exception as e:
        print(f"Handshake hatası: {e}")
        import traceback
        traceback.print_exc()
        print("  → Devam ediliyor...")
        return True  # Hata olsa bile devam et

def send_bootloader_file(ser, bin_data):
    """Binary dosyayı paket paket UART üzerinden gönderir"""
    print("\n" + "=" * 50)
    print("Bootloader Güncelleme Başlatılıyor...")
    print("=" * 50)
    
    # Önce handshake gönder
    send_handshake(ser)
    time.sleep(0.2)  # Bootloader'ın hazır olması için bekle
    print()
    
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
        
        print(f"Paket {packet_num + 1} hazırlanıyor... (indeks: {start_idx}-{end_idx})")
        
        try:
            if not send_packet(ser, packet_data, packet_num + 1, total_packets):
                print(f"Paket {packet_num + 1} gönderilemedi, işlem durduruluyor.")
                return False
        except Exception as e:
            print(f"Paket {packet_num + 1} gönderilirken hata oluştu: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        sent_bytes += len(packet_data)
        progress = (sent_bytes / total_size) * 100
        print(f"İlerleme: {progress:.1f}% ({sent_bytes}/{total_size} byte)")
        
        # Her 5 pakette bir karşı taraftan gelen verileri kontrol et
        if packet_num % 5 == 0:
            time.sleep(0.1)
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"  [Ara kontrol] Karşı taraftan: {response.hex()}")
        print()
    
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
    
    # Port'u temizle ve hazırla
    print("Port hazırlanıyor...")
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except:
        pass  # Reset başarısız olsa bile devam et
    
    # Port'un hazır olması için bekle
    time.sleep(0.3)  # Biraz daha uzun bekle
    
    # Port durumunu kontrol et
    print(f"Port durumu kontrol ediliyor...")
    print(f"  - out_waiting: {ser.out_waiting} byte")
    print(f"  - in_waiting: {ser.in_waiting} byte")
    
    # Eğer output buffer doluysa temizle
    if ser.out_waiting > 0:
        print(f"  ⚠ Output buffer'da {ser.out_waiting} byte var, temizleniyor...")
        try:
            ser.reset_output_buffer()
            time.sleep(0.2)
        except:
            pass
    
    # Port ayarlarını göster
    print(f"Baud Rate: {ser.baudrate}")
    print(f"Data Bits: {ser.bytesize}")
    print(f"Parity: {ser.parity}")
    print(f"Stop Bits: {ser.stopbits}")
    print(f"Port açık: {ser.is_open}")
    print(f"Yazılabilir: {ser.writable()}")
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

