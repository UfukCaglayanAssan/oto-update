#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handshake Sonrası Komut Dizisi Testi
Handshake'den sonra farklı komutlar gönderir
"""

import serial
import time
import sys

BAUD_RATE = 115200
TIMEOUT = 1

def open_serial_port(port_name):
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=TIMEOUT,
                           rtscts=False, dsrdtr=False, xonxoff=False)
        return ser
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)

def test_sequence(ser, sequence_name, commands, delays):
    """Komut dizisini test eder"""
    print(f"\n{'='*60}")
    print(f"Test: {sequence_name}")
    print(f"{'='*60}")
    
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.05)
    
    # Komutları gönder
    for i, (cmd, delay) in enumerate(zip(commands, delays)):
        print(f"  Komut {i+1}: {cmd.hex()} ({len(cmd)} byte)")
        ser.write(cmd)
        ser.flush()
        time.sleep(delay)
    
    # Yanıt bekle
    print("Yanıt bekleniyor (0.5 saniye)...")
    time.sleep(0.5)
    
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting)
        print(f"\n✓✓✓ YANIT ALINDI! ✓✓✓")
        print(f"  Byte Sayısı: {len(response)}")
        print(f"  Hex: {response.hex()[:100]}...")  # İlk 100 karakter
        
        # ASCII göster
        try:
            ascii_str = ''.join([chr(b) if 32 <= b < 127 else '.' for b in response[:200]])
            print(f"  ASCII (ilk 200 byte): {ascii_str}")
        except:
            pass
        
        # "Bootloader" kelimesi var mı kontrol et
        if b'Bootloader' in response:
            if b'NOT Used' in response:
                print(f"  ⚠ Hala 'Bootloader NOT Used' mesajı")
            else:
                print(f"  ✓✓✓ 'Bootloader' mesajı var ama 'NOT Used' yok! ✓✓✓")
        
        return True, response
    else:
        print(f"\n✗ YANIT YOK")
        return False, None

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
    
    print("=" * 60)
    print("Handshake Sonrası Komut Dizisi Testi")
    print("=" * 60)
    print(f"\nPort: {port}")
    print("\nReset yapın, sonra testler başlayacak...")
    print("3 saniye sonra başlıyor...")
    for i in range(3, 0, -1):
        print(f"  {i}...", end='\r')
        time.sleep(1)
    print("\n\n⚡ RESET BUTONUNA BASIN! ⚡")
    time.sleep(0.5)
    print("Testler başlıyor...\n")
    
    ser = open_serial_port(port)
    
    # Test edilecek komut dizileri
    test_sequences = [
        # (İsim, Komutlar, Gecikmeler)
        ("Handshake + Start Update", 
         [bytes([0x55, 0x5A]), bytes([0x5A])], 
         [0.1, 0.2]),
        
        ("Handshake + Enter Bootloader", 
         [bytes([0x55, 0x5A]), bytes([0x42])], 
         [0.1, 0.2]),
        
        ("Handshake + ISP Enter", 
         [bytes([0x55, 0x5A]), bytes([0x7F])], 
         [0.1, 0.2]),
        
        ("Handshake + Command 0x01", 
         [bytes([0x55, 0x5A]), bytes([0x01])], 
         [0.1, 0.2]),
        
        ("Handshake + Command 0x02", 
         [bytes([0x55, 0x5A]), bytes([0x02])], 
         [0.1, 0.2]),
        
        ("Handshake + Command 0x03", 
         [bytes([0x55, 0x5A]), bytes([0x03])], 
         [0.1, 0.2]),
        
        ("Handshake + ACK", 
         [bytes([0x55, 0x5A]), bytes([0xAA])], 
         [0.1, 0.2]),
        
        ("Handshake + Update Start (0x55 0x5A 0x01)", 
         [bytes([0x55, 0x5A, 0x01])], 
         [0.2]),
        
        ("Handshake + Update Start (0x55 0x5A 0x02)", 
         [bytes([0x55, 0x5A, 0x02])], 
         [0.2]),
        
        ("Triple Handshake", 
         [bytes([0x55, 0x5A]), bytes([0x55, 0x5A]), bytes([0x55, 0x5A])], 
         [0.1, 0.1, 0.2]),
    ]
    
    successful = []
    
    for i, (name, commands, delays) in enumerate(test_sequences, 1):
        elapsed = time.time() - start_time if 'start_time' in locals() else 0
        if elapsed > 2.0:
            print(f"\n⚠️ 2 saniye geçti, yeni reset yapın")
            break
        
        if i == 1:
            start_time = time.time()
        
        print(f"\n[{i}/{len(test_sequences)}] Test ediliyor...")
        success, response = test_sequence(ser, name, commands, delays)
        
        if success:
            successful.append((name, response))
            # "NOT Used" yoksa başarılı olabilir
            if response and b'NOT Used' not in response:
                print(f"\n🎉🎉🎉 BAŞARILI! 'NOT Used' mesajı yok! 🎉🎉🎉")
        
        time.sleep(0.05)
    
    # Özet
    print("\n" + "=" * 60)
    print("ÖZET")
    print("=" * 60)
    print(f"Başarılı testler: {len(successful)}")
    
    if successful:
        print("\nBaşarılı testler:")
        for name, response in successful:
            print(f"  - {name}")
    
    ser.close()

if __name__ == "__main__":
    main()

