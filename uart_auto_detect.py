#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UART Port Otomatik Tespit ve Bootloader Test
Reset sonrası UART'tan gelen veriyi dinler, portu tespit eder, handshake gönderir
"""

import serial
import serial.tools.list_ports
import time
import sys

# Bootloader komutları
CMD_BOOTLOADER_ENTER = 0x55
CMD_BOOTLOADER_ACK = 0xAA
CMD_START_UPDATE = 0x5A

def find_all_ports():
    """Tüm mevcut portları listeler"""
    ports = serial.tools.list_ports.comports()
    port_list = []
    for port in ports:
        port_list.append(port.device)
    return port_list

def listen_for_data(port_name, timeout=5):
    """Belirli bir port'tan veri gelip gelmediğini kontrol eder"""
    try:
        ser = serial.Serial(port_name, 115200, timeout=1)
        ser.reset_input_buffer()
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                ser.close()
                return True, data
            time.sleep(0.1)
        
        ser.close()
        return False, None
    except:
        return False, None

def detect_active_port(timeout=10):
    """Reset sonrası veri gönderen portu tespit eder"""
    print("=" * 60)
    print("UART Port Otomatik Tespit")
    print("=" * 60)
    print("\nTüm portlar taranıyor...")
    
    # Tüm portları al
    all_ports = find_all_ports()
    
    if len(all_ports) == 0:
        print("✗ Hiç port bulunamadı!")
        return None
    
    print(f"\nMevcut portlar: {', '.join(all_ports)}")
    print(f"\n⚠️  ŞİMDİ NRESET BUTONUNA BASIN!")
    print(f"Port tespiti başlıyor ({timeout} saniye)...\n")
    
    # Her portu dinle
    start_time = time.time()
    while time.time() - start_time < timeout:
        for port in all_ports:
            has_data, data = listen_for_data(port, timeout=0.5)
            if has_data:
                print(f"\n✓✓✓ PORT TESPİT EDİLDİ: {port} ✓✓✓")
                print(f"Gelen veri: {data.hex()}")
                print(f"ASCII: {data.decode('utf-8', errors='replace')}")
                return port
        
        time.sleep(0.2)
        elapsed = int(time.time() - start_time)
        if elapsed % 2 == 0:
            print(f"  Taranıyor... ({elapsed}/{timeout} saniye)", end='\r')
    
    print(f"\n✗ {timeout} saniye içinde veri gönderen port bulunamadı")
    print("→ Reset butonuna bastınız mı?")
    print("→ Port bağlantısı doğru mu?")
    return None

def send_handshake(port_name):
    """Tespit edilen port'a handshake gönderir"""
    print("\n" + "=" * 60)
    print("Handshake Gönderiliyor")
    print("=" * 60)
    
    try:
        ser = serial.Serial(port_name, 115200, timeout=2, write_timeout=2)
        
        # Buffer temizle
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)
        
        # Handshake paketi
        handshake = bytes([CMD_BOOTLOADER_ENTER, CMD_START_UPDATE])
        
        print(f"Port: {port_name}")
        print(f"Handshake gönderiliyor: {handshake.hex()}")
        
        ser.write(handshake)
        ser.flush()
        
        # Yanıt bekle
        print("Yanıt bekleniyor (3 saniye)...")
        time.sleep(3)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"\n✓✓✓ YANIT ALINDI: {response.hex()} ✓✓✓")
            
            if CMD_BOOTLOADER_ACK in response:
                print("✓✓✓ BOOTLOADER HAZIR VE ÇALIŞIYOR! ✓✓✓")
                ser.close()
                return True
            else:
                print(f"⚠ Yanıt var ama beklenen değil: {response.hex()}")
                ser.close()
                return False
        else:
            print("\n✗ YANIT ALINAMADI")
            print("→ Bootloader modunda olmayabilir")
            print("→ Veya bootloader yanıt vermiyor")
            ser.close()
            return False
            
    except Exception as e:
        print(f"\n✗ Hata: {e}")
        return False

def main():
    """Ana fonksiyon"""
    print("\n" + "=" * 60)
    print("UART Port Tespit ve Bootloader Test")
    print("=" * 60)
    print("\nBu script:")
    print("1. Reset sonrası veri gönderen portu tespit eder")
    print("2. Tespit edilen port'a handshake gönderir")
    print("3. Bootloader yanıtını kontrol eder")
    print("\n" + "-" * 60)
    
    # Port tespiti
    detected_port = detect_active_port(timeout=10)
    
    if detected_port is None:
        print("\n✗ Port tespit edilemedi")
        print("\nManuel port belirtmek için:")
        print(f"  python3 {sys.argv[0]} <port>")
        print(f"  Örnek: python3 {sys.argv[0]} /dev/ttyACM0")
        sys.exit(1)
    
    # Handshake gönder
    success = send_handshake(detected_port)
    
    if success:
        print("\n" + "=" * 60)
        print("✓✓✓ TEST BAŞARILI! ✓✓✓")
        print("=" * 60)
        print(f"\nTespit edilen port: {detected_port}")
        print("Bu port'u Python scriptinizde kullanabilirsiniz:")
        print(f"  python3 uart_receiver.py {detected_port}")
    else:
        print("\n" + "=" * 60)
        print("⚠ TEST TAMAMLANAMADI")
        print("=" * 60)
        print(f"\nPort tespit edildi: {detected_port}")
        print("Ama bootloader yanıt vermedi.")
        print("→ Bootloader modunda olmayabilir")
        print("→ Veya bootloader yüklü değil")

if __name__ == "__main__":
    # Eğer port manuel belirtilmişse
    if len(sys.argv) > 1:
        port = sys.argv[1]
        print(f"Manuel port: {port}")
        send_handshake(port)
    else:
        main()

