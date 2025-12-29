# Raspberry Pi UART Bağlantısı ile Bootloader Yükleme

## Mevcut Durum

✅ Raspberry Pi ile kart arasında UART bağlantısı var
✅ Python scripti Raspberry Pi'de çalışıyor
❌ Handshake yanıtı alınamıyor (bootloader yok veya modunda değil)

## Sorun

Raspberry Pi'de **ISP Tool** çalıştıramazsınız çünkü:
- ISP Tool GUI program (Windows/Linux masaüstü)
- Raspberry Pi genellikle headless (monitör yok)
- X11/display gerektirir

## Çözüm Seçenekleri

### Seçenek 1: Başka Bir Bilgisayar Kullanın (Önerilen) ⭐

**En kolay yöntem:**

1. **Kartı başka bir bilgisayara bağlayın**
   - Windows veya Linux masaüstü bilgisayar
   - USB kablosu ile bağlayın

2. **ISP Tool ile bootloader yükleyin**
   - `UART_ILE_BOOTLOADER_YUKLEME.md` dosyasındaki adımları izleyin
   - LDROM'a bootloader yükleyin

3. **Kartı Raspberry Pi'ye geri bağlayın**
   - UART bağlantısını yapın
   - Python scripti ile güncelleme yapın

### Seçenek 2: Raspberry Pi'de VNC/X11 ile ISP Tool (Zor)

**Eğer Raspberry Pi'de GUI varsa:**

1. **VNC veya X11 forwarding kullanın**
   ```bash
   # VNC server kurun
   sudo apt install tightvncserver
   vncserver :1
   ```

2. **ISP Tool'u X11 ile çalıştırın**
   ```bash
   export DISPLAY=:1
   # ISP Tool'u çalıştırın (eğer Linux versiyonu varsa)
   ```

**Not**: ISP Tool'un Linux versiyonu olmalı ve X11 gerektirir.

### Seçenek 3: Python Scripti ile Bootloader Yükleme (Gelişmiş)

**Eğer bootloader zaten yüklüyse:**

Python scriptimiz zaten bootloader ile haberleşiyor. Eğer bootloader yüklü değilse, önce yüklemeniz gerekir.

**Ama eğer LDROM'da ISP bootloader varsa:**

ISP bootloader ile haberleşen bir Python scripti yazabiliriz. Bu, ISP Tool'un Python versiyonu gibi çalışır.

### Seçenek 4: Raspberry Pi GPIO ile Bootloader Moduna Geçme

**Eğer bootloader yüklüyse ama modunda değilse:**

Raspberry Pi GPIO pinlerini kullanarak kartı bootloader moduna geçirebilirsiniz:

```python
# bootloader_mode.py
import RPi.GPIO as GPIO
import time

# Bootloader moduna geçirmek için pin kontrolü
# (Kartın dokümantasyonuna göre ayarlayın)

BOOT_PIN = 18  # Örnek pin (kartın boot pin'ine bağlı)

GPIO.setmode(GPIO.BCM)
GPIO.setup(BOOT_PIN, GPIO.OUT)

# Boot pin'i aktif et
GPIO.output(BOOT_PIN, GPIO.LOW)
time.sleep(0.1)

# Reset (eğer reset pin'i varsa)
# GPIO.output(RESET_PIN, GPIO.LOW)
# time.sleep(0.1)
# GPIO.output(RESET_PIN, GPIO.HIGH)

# Boot pin'i serbest bırak
GPIO.output(BOOT_PIN, GPIO.HIGH)

GPIO.cleanup()
```

## Önerilen Yöntem: Seçenek 1

**En pratik çözüm:**

1. ✅ Kartı Windows/Linux bilgisayara bağlayın
2. ✅ ISP Tool ile bootloader yükleyin
3. ✅ Kartı Raspberry Pi'ye geri bağlayın
4. ✅ Python scripti ile güncelleme yapın

## Raspberry Pi UART Bağlantısı Kontrolü

### Bağlantı Kontrolü

```bash
# UART bağlantısını test edin
python3 test_port_simple.py /dev/ttyS0
# veya
python3 test_port_simple.py /dev/ttyAMA0
```

### GPIO UART Pinleri (Raspberry Pi)

```
Raspberry Pi          NuMaker-M263KI
-----------          ---------------
GPIO 14 (TX)  ----->  UART0 RX
GPIO 15 (RX)  <-----  UART0 TX
GND           ----->  GND
```

### UART Aktif Etme (Raspberry Pi)

```bash
# UART'ı aktif et (Raspberry Pi 4 için)
sudo raspi-config
# Interface Options > Serial Port > Enable

# Veya
sudo systemctl enable serial-getty@ttyS0.service
sudo systemctl start serial-getty@ttyS0.service
```

## Python Scripti ile Test

Bootloader yüklendikten sonra:

```bash
# Raspberry Pi'de
python3 uart_receiver.py /dev/ttyS0
# veya
python3 uart_receiver.py /dev/ttyAMA0
```

## Sorun Giderme

### UART Port Bulunamıyor

```bash
# Hangi port kullanılıyor?
ls -l /dev/tty* | grep -E "S0|AMA"

# Port izinleri
sudo chmod 666 /dev/ttyS0
sudo usermod -a -G dialout $USER
```

### Handshake Yanıtı Yok

1. **Bootloader yüklü mü?** → ISP Tool ile kontrol edin
2. **Bootloader modunda mı?** → Reset sonrası hemen deneyin
3. **UART pinleri doğru mu?** → TX-RX çapraz bağlı mı?

## Özet

✅ **Raspberry Pi UART bağlantısı ile Python scripti çalışıyor**
⚠️ **Bootloader yüklü değil veya modunda değil**
✅ **Çözüm**: Başka bilgisayarda ISP Tool ile bootloader yükleyin
✅ **Sonra**: Raspberry Pi'de Python scripti ile güncelleme yapın

---

**Not**: Eğer bootloader zaten yüklüyse, sadece bootloader moduna geçmeniz yeterli. Raspberry Pi GPIO ile bunu yapabilirsiniz.

