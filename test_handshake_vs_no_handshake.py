#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handshake Göndermeden vs Göndererek Karşılaştırma
Reset sonrası mesajların handshake'e yanıt mı yoksa otomatik mi olduğunu test eder
"""

import serial
import time
import sys

BAUD_RATE = 115200
TIMEOUT = 2

def open_serial_port(port_name):
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=TIMEOUT,
                           rtscts=False, dsrdtr=False, xonxoff=False)
        return ser
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)

def collect_messages(ser, duration=3):
    """Belirli süre boyunca gelen mesajları toplar"""
    messages = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            messages.append({
                'time': time.time() - start_time,
                'data': data,
                'hex': data.hex(),
                'ascii': ''.join([chr(b) if 32 <= b < 127 else '.' for b in data])
            })
        time.sleep(0.01)
    
    return messages

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
    
    print("=" * 60)
    print("Handshake Göndermeden vs Göndererek Karşılaştırma")
    print("=" * 60)
    print(f"\nPort: {port}")
    
    ser = open_serial_port(port)
    
    # Test 1: Handshake göndermeden
    print("\n" + "=" * 60)
    print("TEST 1: Handshake GÖNDERMEDEN")
    print("=" * 60)
    print("\nReset yapın, 3 saniye bekleyin...")
    print("3 saniye sonra başlıyor...")
    for i in range(3, 0, -1):
        print(f"  {i}...", end='\r')
        time.sleep(1)
    print("\n\n⚡ RESET BUTONUNA BASIN! ⚡")
    time.sleep(0.5)
    
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    
    print("\nMesajlar toplanıyor (3 saniye)...")
    messages_without = collect_messages(ser, duration=3)
    
    print(f"\n✓ {len(messages_without)} mesaj toplandı")
    for i, msg in enumerate(messages_without, 1):
        print(f"\nMesaj {i} ({msg['time']:.2f}s):")
        print(f"  Byte: {len(msg['data'])}")
        print(f"  Hex: {msg['hex'][:100]}...")
        print(f"  ASCII: {msg['ascii'][:100]}")
    
    time.sleep(2)
    
    # Test 2: Handshake göndererek
    print("\n\n" + "=" * 60)
    print("TEST 2: Handshake GÖNDEREREK")
    print("=" * 60)
    print("\nReset yapın, 0.1 saniye sonra handshake gönderilecek...")
    print("3 saniye sonra başlıyor...")
    for i in range(3, 0, -1):
        print(f"  {i}...", end='\r')
        time.sleep(1)
    print("\n\n⚡ RESET BUTONUNA BASIN! ⚡")
    time.sleep(0.1)  # Reset sonrası kısa bekleme
    
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    
    # Handshake gönder
    handshake = bytes([0x55, 0x5A])
    print(f"\nHandshake gönderiliyor: {handshake.hex()}")
    ser.write(handshake)
    ser.flush()
    
    print("\nMesajlar toplanıyor (3 saniye)...")
    messages_with = collect_messages(ser, duration=3)
    
    print(f"\n✓ {len(messages_with)} mesaj toplandı")
    for i, msg in enumerate(messages_with, 1):
        print(f"\nMesaj {i} ({msg['time']:.2f}s):")
        print(f"  Byte: {len(msg['data'])}")
        print(f"  Hex: {msg['hex'][:100]}...")
        print(f"  ASCII: {msg['ascii'][:100]}")
    
    # Karşılaştırma
    print("\n\n" + "=" * 60)
    print("KARŞILAŞTIRMA")
    print("=" * 60)
    
    if len(messages_without) == len(messages_with):
        print("\n⚠️ Mesaj sayısı aynı")
        print("  → Muhtemelen otomatik mesajlar (handshake'e yanıt değil)")
    else:
        print(f"\n✓ Mesaj sayısı farklı ({len(messages_without)} vs {len(messages_with)})")
        print("  → Handshake'e yanıt olabilir")
    
    # İçerik karşılaştırması
    if messages_without and messages_with:
        first_without = messages_without[0]['hex']
        first_with = messages_with[0]['hex']
        
        if first_without == first_with:
            print("\n⚠️ İlk mesajlar aynı")
            print("  → Otomatik mesajlar (handshake'e yanıt değil)")
        else:
            print("\n✓ İlk mesajlar farklı")
            print("  → Handshake'e yanıt olabilir")
            print(f"\nFark:")
            print(f"  Göndermeden: {first_without[:50]}...")
            print(f"  Göndererek:  {first_with[:50]}...")
    
    ser.close()
    print("\nTest tamamlandı.")

if __name__ == "__main__":
    main()

