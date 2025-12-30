#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firmware Güncelleme Sonrası Test Scripti
Reset sonrası yeni firmware'in çalışıp çalışmadığını kontrol eder
"""

import serial
import serial.tools.list_ports
import sys
import time

BAUD_RATE = 115200
TIMEOUT = 2

def find_serial_ports():
    """Mevcut serial portları bulur"""
    ports = serial.tools.list_ports.comports()
    if ports:
        print("Mevcut Serial Portlar:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")
    else:
        print("Serial port bulunamadı!")

def open_serial_port(port_name, baud_rate):
    """Serial port'u açar"""
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=TIMEOUT,
                          rtscts=False, dsrdtr=False, xonxoff=False)
        return ser
    except Exception as e:
        print(f"✗ Port açılamadı: {e}")
        return None

def main():
    print("=" * 60)
    print("Firmware Güncelleme Sonrası Test")
    print("=" * 60)
    print()
    
    # Port belirleme
    if len(sys.argv) > 1:
        port_name = sys.argv[1]
    else:
        find_serial_ports()
        print()
        port_name = input("Port adını girin (örn: /dev/ttyACM0): ").strip()
        if not port_name:
            print("✗ Port adı girilmedi!")
            sys.exit(1)
    
    print(f"Port: {port_name}")
    print()
    
    # Port'u aç
    ser = open_serial_port(port_name, BAUD_RATE)
    if not ser:
        sys.exit(1)
    
    print(f"✓ Port açıldı: {port_name}")
    print(f"  Baud Rate: {BAUD_RATE}")
    print()
    
    try:
        # Buffer'ları temizle
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.3)
        
        print("=" * 60)
        print("TEST 1: Reset Sonrası UART Mesajları")
        print("=" * 60)
        print()
        print("⚠️  Kartı RESET yapın (NRESET butonuna basın)")
        print("    Reset sonrası gelen tüm mesajlar burada görünecek...")
        print("    Çıkmak için Ctrl+C tuşlarına basın")
        print()
        print("-" * 60)
        
        start_time = time.time()
        packet_num = 0
        all_messages = []
        
        try:
            while True:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    elapsed = time.time() - start_time
                    packet_num += 1
                    
                    # Mesajı kaydet
                    all_messages.append({
                        'time': elapsed,
                        'packet_num': packet_num,
                        'data': data,
                        'hex': data.hex(),
                        'ascii': data.decode('ascii', errors='ignore')
                    })
                    
                    # Mesajı göster
                    print(f"[{elapsed:.2f}s] Paket #{packet_num}")
                    print(f"  Byte Sayısı: {len(data)}")
                    print(f"  Hex: {data.hex()[:100]}...")
                    print(f"  ASCII: {data.decode('ascii', errors='ignore')[:100]}")
                    print("-" * 60)
                    
                    # 5 saniye mesaj gelmezse uyar
                    last_message_time = elapsed
                else:
                    time.sleep(0.1)
                    # 5 saniye mesaj gelmediyse uyar
                    if time.time() - start_time > 5 and packet_num == 0:
                        print("⚠️  5 saniye geçti, henüz mesaj gelmedi...")
                        print("    Reset yaptınız mı?")
                        time.sleep(1)
                        
        except KeyboardInterrupt:
            print()
            print("=" * 60)
            print("TEST SONUÇLARI")
            print("=" * 60)
            print()
            
            if all_messages:
                print(f"✓ Toplam {len(all_messages)} mesaj alındı")
                print()
                
                # Mesajları analiz et
                print("MESAJ ANALİZİ:")
                print("-" * 60)
                
                for i, msg in enumerate(all_messages, 1):
                    print(f"\nMesaj #{i} ({msg['time']:.2f}s):")
                    print(f"  Boyut: {len(msg['data'])} byte")
                    print(f"  İlk 50 byte hex: {msg['hex'][:100]}")
                    print(f"  ASCII (ilk 100 char): {msg['ascii'][:100]}")
                    
                    # Bootloader mesajı mı kontrol et
                    if "Bootloader" in msg['ascii'] or "bootloader" in msg['ascii'].lower():
                        print(f"  ⚠️  BOOTLOADER MESAJI TESPİT EDİLDİ!")
                    
                    # Application mesajı mı kontrol et
                    if "CPU @" in msg['ascii']:
                        print(f"  ✓ Application başlangıç mesajı")
                    
                    # LED blink mesajı var mı?
                    if "LED" in msg['ascii'] or "led" in msg['ascii'].lower():
                        print(f"  ✓ LED ile ilgili mesaj var")
                
                print()
                print("=" * 60)
                print("SONUÇ:")
                print("=" * 60)
                
                # Sonuç analizi
                has_bootloader = any("bootloader" in msg['ascii'].lower() for msg in all_messages)
                has_application = any("CPU @" in msg['ascii'] for msg in all_messages)
                has_led = any("LED" in msg['ascii'] or "led" in msg['ascii'].lower() for msg in all_messages)
                
                if has_bootloader and not has_application:
                    print("⚠️  Sadece bootloader mesajları var")
                    print("    → Firmware yazılmamış veya çalışmıyor olabilir")
                    print("    → ISP Tool ile APROM'u kontrol edin")
                elif has_application:
                    print("✓ Application mesajları var")
                    print("  → Firmware çalışıyor gibi görünüyor")
                    if has_led:
                        print("  → LED mesajları da var")
                    else:
                        print("  ⚠️  LED mesajları yok (firmware LED'i kontrol etmiyor olabilir)")
                else:
                    print("⚠️  Ne bootloader ne de application mesajı yok")
                    print("    → Kart çalışmıyor olabilir")
                    print("    → Reset yaptınız mı?")
            else:
                print("✗ Hiç mesaj alınmadı!")
                print("  → Reset yaptınız mı?")
                print("  → Port doğru mu?")
                print("  → Baud rate doğru mu?")
            
            print()
            
    except Exception as e:
        print(f"✗ Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ser.close()
        print("Port kapatıldı.")

if __name__ == "__main__":
    main()

