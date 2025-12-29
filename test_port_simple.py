#!/usr/bin/env python3
# Basit port testi - Handshake takılmasını test eder

import serial
import time
import sys

if len(sys.argv) < 2:
    print("Kullanım: python3 test_port_simple.py <port>")
    print("Örnek: python3 test_port_simple.py /dev/ttyUSB0")
    sys.exit(1)

port_name = sys.argv[1]

print(f"Port açılıyor: {port_name}")
try:
    ser = serial.Serial(port_name, 115200, timeout=2, write_timeout=2,
                       rtscts=False, dsrdtr=False, xonxoff=False)
    print("✓ Port açıldı")
    
    # Buffer temizle
    print("Buffer temizleniyor...")
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.2)
    
    # Handshake gönder
    handshake = bytes([0x55, 0x5A])
    print(f"Handshake gönderiliyor: {handshake.hex()}")
    
    start = time.time()
    bytes_written = ser.write(handshake)
    elapsed = time.time() - start
    print(f"✓ {bytes_written} byte yazıldı ({elapsed:.3f} saniye)")
    
    # Flush
    print("Flush yapılıyor...")
    start = time.time()
    ser.flush()
    elapsed = time.time() - start
    print(f"✓ Flush tamamlandı ({elapsed:.3f} saniye)")
    
    print("✓✓✓ Handshake başarılı! ✓✓✓")
    
    ser.close()
    
except serial.SerialTimeoutException as e:
    print(f"✗ TIMEOUT: {e}")
    print("  → Port yazma işlemi zaman aşımına uğradı")
    print("  → Port başka program tarafından kullanılıyor olabilir")
except Exception as e:
    print(f"✗ HATA: {e}")
    import traceback
    traceback.print_exc()


