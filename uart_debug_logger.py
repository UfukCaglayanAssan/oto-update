#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UART Debug Logger - Gönderilen ve Alınan Tüm Verileri Loglar
Nuvoton karta giden ve gelen tüm verileri dosyaya kaydeder
"""

import serial
import serial.tools.list_ports
import sys
import time
from datetime import datetime

BAUD_RATE = 115200
TIMEOUT = 2
WRITE_TIMEOUT = 5

class UARTLogger:
    def __init__(self, port_name, log_file="uart_log.txt"):
        self.port_name = port_name
        self.log_file = log_file
        self.ser = None
        self.log_enabled = True
        
    def open(self):
        """Port'u açar"""
        try:
            self.ser = serial.Serial(
                self.port_name, 
                BAUD_RATE, 
                timeout=TIMEOUT,
                write_timeout=WRITE_TIMEOUT,
                rtscts=False, 
                dsrdtr=False, 
                xonxoff=False
            )
            print(f"✓ Port açıldı: {self.port_name}")
            print(f"✓ Log dosyası: {self.log_file}")
            return True
        except Exception as e:
            print(f"✗ Port açılamadı: {e}")
            return False
    
    def log(self, direction, data, description=""):
        """Veriyi loglar (GÖNDERİLEN veya ALINAN)"""
        if not self.log_enabled:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Hex formatı
        hex_str = ' '.join([f'{b:02X}' for b in data])
        
        # ASCII formatı (printable karakterler)
        ascii_str = ''.join([chr(b) if 32 <= b < 127 else '.' for b in data])
        
        # Log satırı
        log_line = f"[{timestamp}] {direction:10s} | {len(data):3d} byte | {description}\n"
        log_line += f"  Hex:   {hex_str}\n"
        log_line += f"  ASCII: {ascii_str}\n"
        log_line += f"  Bytes: {', '.join([f'0x{b:02X}' for b in data[:16]])}{'...' if len(data) > 16 else ''}\n"
        log_line += "-" * 80 + "\n"
        
        # Dosyaya yaz
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"⚠ Log yazma hatası: {e}")
        
        # Ekrana da yazdır (ilk 100 byte)
        print(f"[{timestamp}] {direction:10s} | {len(data):3d} byte | {description}")
        if len(data) <= 100:
            print(f"  Hex: {hex_str}")
        else:
            print(f"  Hex: {hex_str[:100]}... ({len(data)} byte)")
    
    def write(self, data, description=""):
        """Veri gönderir ve loglar"""
        if self.ser and self.ser.is_open:
            try:
                bytes_written = self.ser.write(data)
                self.ser.flush()
                self.log("GÖNDERİLEN", data, description)
                return bytes_written
            except Exception as e:
                print(f"✗ Yazma hatası: {e}")
                return 0
        return 0
    
    def read(self, size=1):
        """Veri okur ve loglar"""
        if self.ser and self.ser.is_open:
            try:
                data = self.ser.read(size)
                if len(data) > 0:
                    self.log("ALINAN", data, f"Okunan {len(data)} byte")
                return data
            except Exception as e:
                print(f"✗ Okuma hatası: {e}")
                return b''
        return b''
    
    def read_available(self):
        """Mevcut tüm veriyi okur ve loglar"""
        if self.ser and self.ser.is_open:
            try:
                available = self.ser.in_waiting
                if available > 0:
                    data = self.ser.read(available)
                    self.log("ALINAN", data, f"Buffer'dan {len(data)} byte")
                    return data
            except Exception as e:
                print(f"✗ Okuma hatası: {e}")
        return b''
    
    def close(self):
        """Port'u kapatır"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Port kapatıldı")

def main():
    if len(sys.argv) < 2:
        print("=" * 80)
        print("UART Debug Logger - Gönderilen ve Alınan Tüm Verileri Loglar")
        print("=" * 80)
        print()
        print("Kullanım:")
        print("  python3 uart_debug_logger.py <port> [log_file]")
        print()
        print("Örnek:")
        print("  python3 uart_debug_logger.py /dev/ttyACM0")
        print("  python3 uart_debug_logger.py /dev/ttyACM0 uart_log.txt")
        print()
        print("Bu script:")
        print("  - Port'u açar")
        print("  - Gönderilen TÜM verileri loglar (hex, ASCII, bytes)")
        print("  - Alınan TÜM verileri loglar (hex, ASCII, bytes)")
        print("  - Log dosyasına kaydeder")
        print("  - Ekrana da yazdırır")
        print()
        print("NOT: Bu script sadece logger. Veri göndermez, sadece dinler.")
        print("     Güncelleme yapmak için uart_receiver_nuvoton.py kullanın.")
        print()
        sys.exit(1)
    
    port_name = sys.argv[1]
    log_file = sys.argv[2] if len(sys.argv) > 2 else "uart_log.txt"
    
    logger = UARTLogger(port_name, log_file)
    
    if not logger.open():
        sys.exit(1)
    
    # Log dosyası başlığı
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"UART Debug Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Port: {port_name}\n")
        f.write(f"Baud Rate: {BAUD_RATE}\n")
        f.write("=" * 80 + "\n\n")
    
    print()
    print("=" * 80)
    print("UART Logger Aktif")
    print("=" * 80)
    print("Gönderilen ve alınan TÜM veriler loglanıyor...")
    print("Çıkmak için Ctrl+C tuşlarına basın")
    print("-" * 80)
    print()
    
    try:
        while True:
            # Alınan verileri kontrol et
            logger.read_available()
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print()
        print("-" * 80)
        print("Logger sonlandırıldı")
        print(f"Log dosyası: {log_file}")
        print()
    except Exception as e:
        print(f"✗ Hata: {e}")
    finally:
        logger.close()

if __name__ == "__main__":
    main()


