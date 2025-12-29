# Handshake Yanıt Vermiyor - Çözümler

## Durum

- ✅ Bootloader çalışıyor ("Bootloader NOT Used" mesajı geliyor)
- ✅ UART haberleşmesi çalışıyor
- ❌ Hiçbir handshake komutu yanıt vermiyor

## Muhtemel Nedenler

### 1. Bootloader Güncelleme Modunda Değil ⚠️ EN OLASI

**"Bootloader NOT Used" mesajı:**
- Bootloader çalışıyor ama **normal uygulama modunda**
- Güncelleme moduna geçmek için **özel bir şey gerekiyor**

### 2. Timing Sorunu

**Reset sonrası:**
- Çok hızlı gönderiyorsunuz (bootloader henüz hazır değil)
- Veya çok yavaş (bootloader zaten normal moda geçti)

### 3. DIP Switch Ayarları

Kartınızın sol üstünde **DIP switch** var:
- VCOM, TXD, RXD yazıyor
- Bu switch'ler bootloader modunu etkileyebilir

### 4. Özel Aktivasyon Gerekiyor

Bazı bootloader'lar:
- Flash boşsa güncelleme moduna geçer
- Özel pin kombinasyonu gerektirir
- Belirli bir komut dizisi gerektirir

## Çözümler

### Çözüm 1: Timing'i Değiştir

Reset sonrası **farklı zamanlarda** deneyin:

```python
# test_timing.py - Farklı timing'lerle test
import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

# Reset yapın, sonra:
for delay in [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]:
    print(f"\n{delay} saniye bekleyip gönderiyor...")
    time.sleep(delay)
    ser.reset_input_buffer()
    ser.write(bytes([0x55, 0x5A]))
    ser.flush()
    time.sleep(0.3)
    if ser.in_waiting > 0:
        print(f"✓ YANIT: {ser.read(ser.in_waiting).hex()}")
        break
    else:
        print("✗ Yanıt yok")
```

### Çözüm 2: DIP Switch Kontrolü

1. **DIP switch'leri kontrol edin:**
   - VCOM: Açık (ON) olmalı
   - TXD/RXD: Doğru ayarlanmış mı?

2. **Farklı kombinasyonlar deneyin:**
   - Tüm switch'ler kapalı
   - Tüm switch'ler açık
   - Farklı kombinasyonlar

### Çözüm 3: Reset Sonrası Gelen Mesajları Analiz Et

"Bootloader NOT Used" mesajından sonra:
- Başka bir mesaj geliyor mu?
- Belirli bir süre sonra başka bir şey geliyor mu?

```bash
# Dinleme scriptini çalıştırın
python3 uart_listener.py /dev/ttyACM0

# Reset yapın
# Tüm mesajları kaydedin
# Mesajların zamanlamasını analiz edin
```

### Çözüm 4: ISP Tool Protokolünü Kontrol Et

ISP Tool'un kullandığı protokolü araştırın:
- Nuvoton ISP Tool dokümantasyonuna bakın
- Hangi komutları kullanıyor?
- Hangi timing'i kullanıyor?

### Çözüm 5: Flash Durumunu Kontrol Et

Bazı bootloader'lar:
- Flash boşsa otomatik güncelleme moduna geçer
- Flash doluysa normal uygulamaya geçer

**Kontrol:**
- Flash'ın durumu nedir?
- Boş mu, dolu mu?

### Çözüm 6: Bootloader Kaynak Kodunu İncele

Eğer bootloader kaynak kodunuz varsa:
- Hangi komutları bekliyor?
- Hangi koşullarda güncelleme moduna geçiyor?
- Timing nedir?

## Test Senaryosu

### Adım 1: Timing Testi

```python
# test_timing_variations.py
import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
handshake = bytes([0x55, 0x5A])

print("Reset yapın, sonra testler başlayacak...")
time.sleep(3)

for delay in [0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.7, 1.0]:
    print(f"\n{delay}s bekleyip gönderiyor...")
    ser.reset_input_buffer()
    time.sleep(delay)
    ser.write(handshake)
    ser.flush()
    time.sleep(0.3)
    if ser.in_waiting > 0:
        print(f"✓✓✓ YANIT: {ser.read(ser.in_waiting).hex()}")
        break
```

### Adım 2: Uzun Dinleme

Reset sonrası **uzun süre** dinleyin:

```bash
python3 uart_listener.py /dev/ttyACM0
# Reset yapın
# 10-20 saniye bekleyin
# Tüm mesajları kaydedin
```

### Adım 3: ISP Tool ile Karşılaştır

ISP Tool'u açın ve:
- Hangi komutları gönderiyor?
- Timing nedir?
- Wireshark veya serial monitor ile izleyin

## Önerilen Yaklaşım

1. **Önce timing testi yapın** (Çözüm 1)
2. **DIP switch'leri kontrol edin** (Çözüm 2)
3. **Uzun dinleme yapın** (Çözüm 3)
4. **ISP Tool protokolünü araştırın** (Çözüm 4)

## Not

"Bootloader NOT Used" mesajı:
- Bootloader çalışıyor ✅
- Ama güncelleme modunda değil ❌
- Muhtemelen **özel bir aktivasyon** gerekiyor

Belki de:
- Flash boşsa güncelleme moduna geçer
- Veya özel bir pin kombinasyonu gerekiyor
- Veya ISP Tool'un kullandığı özel bir protokol var

