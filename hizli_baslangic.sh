#!/bin/bash
# NuMaker-M263KI Hızlı Başlangıç Scripti
# UART üzerinden bootloader güncellemesi için

echo "=========================================="
echo "NuMaker-M263KI Bootloader Güncelleme"
echo "=========================================="
echo ""

# Port tespiti
echo "Mevcut serial portlar:"
ls -l /dev/tty* | grep -E "USB|ACM|AMA|S0" | head -5
echo ""

# Port seçimi
read -p "Port adını girin (örn: /dev/ttyUSB0, /dev/ttyS0): " PORT

if [ -z "$PORT" ]; then
    echo "Port belirtilmedi, otomatik tespit edilecek..."
    PORT=""
fi

# Binary dosya kontrolü
BIN_FILE="NuvotonM26x-Bootloader-Test.bin"

if [ ! -f "$BIN_FILE" ]; then
    echo "Hata: $BIN_FILE bulunamadı!"
    exit 1
fi

echo "Binary dosya: $BIN_FILE"
echo "Port: ${PORT:-Otomatik}"
echo ""

# Python scriptini çalıştır
if [ -z "$PORT" ]; then
    python3 uart_receiver.py
else
    python3 uart_receiver.py "$PORT"
fi



