#!/usr/bin/env python3
# Port tanılama scripti - Hangi portlar mevcut ve hangisi çalışıyor?

import serial
import serial.tools.list_ports
import time

print("=" * 60)
print("Port Tanılama")
print("=" * 60)

# Tüm portları listele
print("\n1. TÜM MEVCUT PORTLAR:")
print("-" * 60)
ports = serial.tools.list_ports.comports()
if len(ports) == 0:
    print("  ✗ Hiç port bulunamadı!")
    print("  → USB kablosunu kontrol edin")
    print("  → lsusb komutu ile USB cihazlarını kontrol edin")
else:
    for i, port in enumerate(ports, 1):
        print(f"  {i}. {port.device}")
        print(f"     Açıklama: {port.description}")
        print(f"     Üretici: {port.manufacturer}")
        print(f"     HWID: {port.hwid}")
        print()

# Her portu test et
print("\n2. PORT TESTLERİ:")
print("-" * 60)

test_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1', 
              '/dev/ttyAMA0', '/dev/ttyS0']

for port_name in test_ports:
    print(f"\nTest: {port_name}")
    try:
        ser = serial.Serial(port_name, 115200, timeout=1, write_timeout=2,
                           rtscts=False, dsrdtr=False, xonxoff=False)
        print(f"  ✓ Port açıldı")
        print(f"  - Yazılabilir: {ser.writable()}")
        print(f"  - Okunabilir: {ser.readable()}")
        print(f"  - Output buffer: {ser.out_waiting} byte")
        print(f"  - Input buffer: {ser.in_waiting} byte")
        
        # Test yazma
        try:
            test_data = b"TEST"
            ser.write(test_data)
            ser.flush()
            print(f"  ✓ Test yazma başarılı")
        except Exception as e:
            print(f"  ✗ Test yazma hatası: {e}")
        
        ser.close()
        print(f"  ✓ Port kapatıldı")
        
    except FileNotFoundError:
        print(f"  - Port mevcut değil")
    except serial.SerialException as e:
        print(f"  ✗ Port açılamadı: {e}")
    except Exception as e:
        print(f"  ✗ Hata: {e}")

print("\n" + "=" * 60)
print("Tanılama tamamlandı")
print("=" * 60)
print("\nÖNERİLER:")
print("1. Nu-Link2 VCOM portu (/dev/ttyACM0) genellikle UART için kullanılabilir")
print("2. Eğer write timeout alıyorsanız:")
print("   - Port'u kapatıp açın")
print("   - USB kablosunu çıkarıp takın")
print("   - Başka program port'u kullanıyor olabilir (lsof ile kontrol edin)")
print("3. Manuel UART pinlerini kullanmak için:")
print("   - Kartın pinout'una bakın (UART0 TX/RX)")
print("   - USB-to-UART dönüştürücü kullanın")



