#!/usr/bin/env python3
# Bootloader test scripti - Farklı baud rate'ler ve handshake yöntemleri dener

import serial
import time
import sys

# Test edilecek baud rate'ler
BAUD_RATES = [115200, 9600, 19200, 38400, 57600, 230400]

# Test edilecek handshake paketleri
HANDSHAKE_VARIANTS = [
    ([0x55, 0x5A], "Standart (0x55, 0x5A)"),
    ([0xAA, 0x55], "Alternatif 1 (0xAA, 0x55)"),
    ([0x5A, 0x55], "Alternatif 2 (0x5A, 0x55)"),
    ([0x55], "Tek byte (0x55)"),
    ([0xAA], "Tek byte (0xAA)"),
]

def test_handshake(port_name, baud_rate, handshake_data, description):
    """Belirli bir baud rate ve handshake ile test yapar"""
    try:
        print(f"\n  Test: {description} @ {baud_rate} baud")
        ser = serial.Serial(port_name, baud_rate, timeout=2, write_timeout=2,
                           rtscts=False, dsrdtr=False, xonxoff=False)
        
        # Buffer temizle
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)
        
        # Handshake gönder
        handshake = bytes(handshake_data)
        ser.write(handshake)
        ser.flush()
        print(f"    Gönderildi: {handshake.hex()}")
        
        # Yanıt bekle
        time.sleep(1)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"    ✓✓✓ YANIT ALINDI: {response.hex()} ✓✓✓")
            ser.close()
            return True
        else:
            print(f"    ✗ Yanıt yok")
            ser.close()
            return False
            
    except Exception as e:
        print(f"    ✗ Hata: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python3 bootloader_test.py <port>")
        print("Örnek: python3 bootloader_test.py /dev/ttyACM0")
        sys.exit(1)
    
    port_name = sys.argv[1]
    
    print("=" * 60)
    print("Bootloader Test - Farklı Baud Rate ve Handshake Testleri")
    print("=" * 60)
    print(f"\nPort: {port_name}")
    print(f"Test edilecek baud rate'ler: {BAUD_RATES}")
    print(f"Test edilecek handshake'ler: {len(HANDSHAKE_VARIANTS)}")
    print("\n" + "=" * 60)
    
    success_count = 0
    
    for baud_rate in BAUD_RATES:
        print(f"\n{'='*60}")
        print(f"BAUD RATE: {baud_rate}")
        print(f"{'='*60}")
        
        for handshake_data, description in HANDSHAKE_VARIANTS:
            if test_handshake(port_name, baud_rate, handshake_data, description):
                success_count += 1
                print(f"\n  ⭐ BAŞARILI KOMBİNASYON BULUNDU! ⭐")
                print(f"  → Baud Rate: {baud_rate}")
                print(f"  → Handshake: {description} ({bytes(handshake_data).hex()})")
                print(f"\n  Bu ayarları uart_receiver.py'de kullanın!")
                return
    
    print(f"\n{'='*60}")
    print("SONUÇ")
    print(f"{'='*60}")
    
    if success_count == 0:
        print("\n✗ Hiçbir kombinasyonda yanıt alınamadı.")
        print("\nMuhtemel nedenler:")
        print("1. Bootloader yüklü değil")
        print("   → ISP Tool ile bootloader yükleyin")
        print("   → Veya ICP Tool ile LDROM'a bootloader yükleyin")
        print("\n2. Bootloader modunda değil")
        print("   → Kartı resetleyin")
        print("   → Belirli bir pin'i GND'ye bağlayın (kart dokümantasyonuna bakın)")
        print("   → Reset sonrası belirli süre bekleyin")
        print("\n3. UART pinleri yanlış")
        print("   → Kartın pinout'una bakın")
        print("   → USB-to-UART dönüştürücü hangi UART'ı kullanıyor?")
        print("\n4. Bootloader farklı protokol kullanıyor")
        print("   → Bootloader kodunu kontrol edin")
        print("   → Handshake formatını kontrol edin")
    else:
        print(f"\n✓ {success_count} kombinasyonda yanıt alındı!")

if __name__ == "__main__":
    main()

