# Bootloader Durum Kontrolü ve Çözümler

## Mevcut Durum

✅ **Baud Rate**: 115200 (doğru)
✅ **Handshake Gönderiliyor**: 0x55 0x5A
❌ **Yanıt Alınamıyor**: Bootloader yanıt vermiyor

## Muhtemel Nedenler ve Çözümler

### 1. Bootloader Yüklü Değil ⚠️ EN OLASI

**Belirtiler:**
- Handshake gönderiliyor ama yanıt yok
- Paketler gönderiliyor ama kart işlemiyor

**Çözüm:**
1. **ISP Tool ile bootloader yükleyin**
   - `UART_ILE_BOOTLOADER_YUKLEME.md` dosyasındaki adımları izleyin
   - ISP Tool ile LDROM'a bootloader yükleyin

2. **Veya ICP Tool ile yükleyin** (eğer ISP bootloader yoksa)
   - `BOOTLOADER_YUKLEME_ADIMLARI.md` dosyasındaki adımları izleyin

### 2. Bootloader Modunda Değil

**Belirtiler:**
- Bootloader yüklü ama yanıt vermiyor
- Normal uygulama çalışıyor olabilir

**Çözüm:**
1. **Kartı resetleyin**
   - Reset butonuna basın
   - Bootloader genellikle reset sonrası belirli süre modda kalır

2. **Bootloader moduna geçin**
   - Belirli bir pin'i GND'ye bağlayın (kartın dokümantasyonuna bakın)
   - Veya boot pin kullanın
   - Reset sonrası bootloader moduna geçer

3. **Zamanlama**
   - Reset sonrası hemen (1-2 saniye içinde) handshake gönderin
   - Bazı bootloader'lar sadece belirli süre modda kalır

### 3. UART Pinleri Yanlış

**Belirtiler:**
- Veri gönderiliyor ama ulaşmıyor
- Hiçbir yanıt yok

**Çözüm:**
1. **Pin kontrolü**
   - NuMaker-M263KI kartında hangi UART kullanılıyor?
   - USB-to-UART dönüştürücü hangi UART'a bağlı?
   - Kartın pinout'una bakın

2. **TX-RX kontrolü**
   - TX-RX çapraz bağlı mı? (TX->RX, RX->TX)
   - GND ortak mı?

### 4. Baud Rate Farklı (Ama siz 115200 dediniz, bu doğru)

**Kontrol:**
- Bootloader kodunda baud rate 115200 mi?
- Python scripti ile aynı mı?

## Test Adımları

### Test 1: Bootloader Yüklü mü?

1. **ISP Tool ile kontrol edin**
   - ISP Tool'u açın
   - UART modunu seçin
   - Port'u seçin
   - Connect butonuna tıklayın
   - Bağlanırsa → Bootloader var ✅
   - Bağlanamazsa → Bootloader yok ❌

### Test 2: Bootloader Modunda mı?

1. **Kartı resetleyin**
2. **Hemen Python scriptini çalıştırın** (1-2 saniye içinde)
3. **Handshake yanıtı geliyor mu?**
   - Geliyorsa → Bootloader modunda ✅
   - Gelmiyorsa → Modunda değil ❌

### Test 3: UART Bağlantısı Çalışıyor mu?

1. **Basit test scripti çalıştırın**
   ```bash
   python3 test_port_simple.py /dev/ttyACM0
   ```
2. **Port yazılabilir mi?**
   - Evet → Port çalışıyor ✅
   - Hayır → Port sorunu ❌

## Önerilen Çözüm Sırası

### Adım 1: Bootloader Yüklü mü Kontrol Et

```bash
# ISP Tool ile bağlanmayı deneyin
# Bağlanırsa → Bootloader var, Adım 2'ye geç
# Bağlanamazsa → Bootloader yok, Adım 3'e geç
```

### Adım 2: Bootloader Moduna Geç

1. Kartı resetleyin
2. Hemen (1-2 saniye içinde) Python scriptini çalıştırın:
   ```bash
   python3 uart_receiver.py /dev/ttyACM0
   ```
3. Handshake yanıtı geliyor mu kontrol edin

### Adım 3: Bootloader Yükle

1. **ISP Tool ile yükleyin** (önerilen)
   - `UART_ILE_BOOTLOADER_YUKLEME.md` dosyasındaki adımları izleyin

2. **Veya ICP Tool ile yükleyin**
   - `BOOTLOADER_YUKLEME_ADIMLARI.md` dosyasındaki adımları izleyin

## Hızlı Kontrol Listesi

- [ ] Baud rate 115200 (✅ doğru)
- [ ] Port açılıyor (`/dev/ttyACM0`)
- [ ] Handshake gönderiliyor (0x55 0x5A)
- [ ] Yanıt alınıyor mu? (❌ hayır)
- [ ] Bootloader yüklü mü? (kontrol et)
- [ ] Bootloader modunda mı? (kontrol et)
- [ ] UART pinleri doğru mu? (kontrol et)

## Sonraki Adımlar

1. **ISP Tool ile bootloader durumunu kontrol edin**
2. **Eğer bootloader yoksa, yükleyin**
3. **Eğer bootloader varsa, moduna geçmeyi deneyin**
4. **Python scriptini tekrar çalıştırın**

## Not

Paketler gönderiliyor ama kart işlemiyor olabilir. Bootloader yüklü olmadan veya modunda olmadan paketler işlenmez. Önce bootloader'ı yükleyin veya moduna geçirin.

