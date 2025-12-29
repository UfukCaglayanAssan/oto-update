# Bootloader Test Adımları

## Durum

✅ Bootloader LDROM'a yüklendi
✅ Reset sonrası mesajlar geliyor
⚠️ Ama bu mesajlar uygulama kodundan (APROM) geliyor gibi görünüyor

## Test: Bootloader Çalışıyor mu?

### Test 1: Handshake Testi

Reset sonrası bootloader'ın handshake'e yanıt verip vermediğini test edin:

```bash
python3 test_timing_variations.py /dev/ttyACM0
```

**Beklenen:**
- Handshake gönderildi: 0x55 0x5A
- Yanıt alındı: 0xAA veya benzeri
- "Bootloader NOT Used" mesajı gelmemeli

### Test 2: UART Listener ile Kontrol

Reset sonrası hemen handshake gönderin:

```bash
# Terminal 1: Dinleme
python3 uart_listener.py /dev/ttyACM0

# Terminal 2: Handshake gönder (reset sonrası hemen)
python3 -c "
import serial, time
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(0.1)  # Reset sonrası bekleme
ser.write(bytes([0x55, 0x5A]))
ser.flush()
time.sleep(0.5)
if ser.in_waiting > 0:
    print('YANIT:', ser.read(ser.in_waiting).hex())
ser.close()
"
```

## Mesaj Analizi

Gelen mesajlar:
- "CPU @ 64000000Hz" → Sistem başlangıç mesajı
- "PB.3 and PD.7 Sample Code" → Uygulama kodu çalışıyor
- "Press any key to start" → Uygulama kodu bekliyor

**Bu mesajlar:**
- Bootloader'dan değil, APROM'daki uygulama kodundan geliyor
- Bootloader çalıştı, normal uygulamaya geçti
- Handshake testi yaparak bootloader'ın moduna geçip geçmediğini kontrol edin

## Bootloader Moduna Geçirme

Eğer bootloader handshake'e yanıt vermiyorsa:

1. **Timing:** Reset sonrası hemen (0.1-0.2 saniye içinde) handshake gönderin
2. **UART Pinleri:** Chip Settings'te "PA.3/PA.2" seçili, Raspberry Pi bağlantınız bu pinlere uygun mu?
3. **DIP Switch:** VCOM switch'i açık mı?

## Sonraki Adımlar

1. Handshake testi yapın
2. Yanıt gelirse → Bootloader çalışıyor ✅
3. Yanıt gelmezse → Timing veya pin bağlantısını kontrol edin

