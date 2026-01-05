# UART Verilerini Görüntüleme Yöntemleri

## 🎯 Nuvoton Karta Giden Verileri Görme Yöntemleri

### 1. ✅ Python Script'te Debug Logging (EN PRATİK)

**Avantajlar:**
- Ücretsiz
- Kolay kullanım
- Tüm verileri dosyaya kaydeder
- Hex, ASCII ve byte formatında gösterir

**Kullanım:**

#### Yöntem A: Ayrı Logger Scripti
```bash
# Terminal 1: Logger'ı başlat
python3 uart_debug_logger.py /dev/ttyACM0

# Terminal 2: Güncelleme scriptini çalıştır
python3 uart_receiver_nuvoton.py /dev/ttyACM0 NuvotonM26x-Bootloader-Test.bin
```

Logger tüm gönderilen ve alınan verileri `uart_log.txt` dosyasına kaydeder.

#### Yöntem B: Mevcut Script'e Logging Eklemek
`uart_receiver_nuvoton.py` scriptine logging eklenebilir (isteğe bağlı).

---

### 2. 🔬 Logic Analyzer (HARDWARE SEVİYESİNDE)

**Avantajlar:**
- En doğru yöntem
- Hardware seviyesinde sinyalleri görür
- Timing analizi yapabilir
- Baud rate, parity, stop bit kontrolü

**Gereksinimler:**
- Logic Analyzer cihazı (ör: Saleae Logic, Sigrok, DSLogic)
- UART TX pin'ine bağlantı (genellikle PB12 veya PB13)
- GND bağlantısı

**Bağlantı:**
```
Logic Analyzer CH0  →  Nuvoton UART TX (PB12 veya PB13)
Logic Analyzer GND  →  Nuvoton GND
```

**Yazılım:**
- **Saleae Logic** (ücretli, en iyi)
- **PulseView (Sigrok)** (ücretsiz, açık kaynak)
- **DSView** (DSLogic için)

**Kullanım:**
1. Logic Analyzer'ı USB'ye bağla
2. CH0'u Nuvoton TX pin'ine bağla
3. PulseView/Saleae Logic'i aç
4. UART protokolü ekle (115200 baud, 8N1)
5. Capture başlat
6. Python script'i çalıştır
7. Verileri analiz et

**Örnek Logic Analyzer'lar:**
- **Saleae Logic 8** (~$300) - En popüler
- **DSLogic Plus** (~$100) - Uygun fiyatlı
- **ChipWhisperer** (~$200) - Güvenlik odaklı
- **USBee AX Pro** (~$200)

---

### 3. 📡 Serial Port Monitor (UART SEVİYESİNDE)

**Avantajlar:**
- Ücretsiz
- Kolay kullanım
- Real-time görüntüleme

**Yazılımlar:**
- **PuTTY** (Windows/Linux)
- **minicom** (Linux)
- **screen** (Linux)
- **Serial Monitor** (Arduino IDE)
- **RealTerm** (Windows)

**Kullanım:**
```bash
# Linux
minicom -D /dev/ttyACM0 -b 115200

# Veya screen
screen /dev/ttyACM0 115200
```

**NOT:** Bu yöntem sadece **alınan** verileri gösterir, **gönderilen** verileri göstermez.

---

### 4. 🐍 Python Script'te Print Statements

**Mevcut script'te zaten var:**
- `send_packet()` fonksiyonu paket gönderirken debug mesajları yazdırıyor
- `receive_response()` fonksiyonu yanıtları gösteriyor

**Daha detaylı logging için:**
- `uart_debug_logger.py` scriptini kullanın
- Veya `uart_receiver_nuvoton.py`'ye logging ekleyin

---

### 5. 🔍 Wireshark (USB Serial için)

**Avantajlar:**
- USB-UART dönüştürücüler için
- USB seviyesinde paket analizi

**Kullanım:**
1. Wireshark'ı aç
2. USB interface'ini seç
3. USB serial trafiğini yakala
4. UART verilerini analiz et

**NOT:** Bu yöntem USB-UART dönüştürücü kullanıyorsanız işe yarar.

---

## 🎯 Önerilen Yöntem

### Hızlı Test İçin:
✅ **Python Debug Logger** (`uart_debug_logger.py`)
- En pratik
- Ücretsiz
- Tüm verileri dosyaya kaydeder

### Profesyonel Analiz İçin:
✅ **Logic Analyzer**
- En doğru
- Timing analizi
- Hardware seviyesinde doğrulama

---

## 📋 Örnek Kullanım

### Python Logger ile:

```bash
# Terminal 1: Logger başlat
python3 uart_debug_logger.py /dev/ttyACM0 uart_log.txt

# Terminal 2: Güncelleme yap
python3 uart_receiver_nuvoton.py /dev/ttyACM0 NuvotonM26x-Bootloader-Test.bin
```

**Log dosyası örneği:**
```
[14:23:45.123] GÖNDERİLEN |  64 byte | CMD_CONNECT
  Hex:   AE 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ...
  ASCII: ................
  Bytes: 0xAE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00...
--------------------------------------------------------------------------------
[14:23:45.156] ALINAN    |  64 byte | Buffer'dan 64 byte
  Hex:   AE 00 00 00 02 00 00 00 00 08 00 00 00 08 00 00 ...
  ASCII: ................
  Bytes: 0xAE, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00...
--------------------------------------------------------------------------------
```

---

## 🔧 Logic Analyzer Bağlantı Şeması

```
                    Nuvoton M263KI
                    ┌─────────────┐
                    │             │
  Logic Analyzer    │   UART TX   │───┐
  CH0 ─────────────┤   (PB12)    │   │
                    │             │   │
  Logic Analyzer    │     GND     │───┼─── GND
  GND ─────────────┤             │   │
                    └─────────────┘   │
                                      │
                                      │
                    Logic Analyzer     │
                    ┌─────────────┐   │
                    │             │   │
                    │    CH0      │───┘
                    │             │
                    │    GND      │───┘
                    └─────────────┘
```

---

## 📝 Sonuç

**En pratik çözüm:** `uart_debug_logger.py` scriptini kullanın.
- Ücretsiz
- Kolay
- Tüm verileri kaydeder

**En doğru çözüm:** Logic Analyzer kullanın.
- Hardware seviyesinde doğrulama
- Timing analizi
- Profesyonel debug


