# ISP Tool Bağlantı Sorunları - "Waiting for device connection"

## Sorun

ISP Tool açıldı, UART/COM18 seçildi ama **"Waiting for device connection"** mesajında kalıyor.

## Nedenler ve Çözümler

### 1. Kart Bootloader Modunda Değil ⚠️ EN OLASI

**ISP Tool, kartın ISP bootloader modunda olmasını bekler.**

#### Çözüm: Kartı Bootloader Moduna Geçirin

**NuMaker-M263KI için genellikle:**

**Yöntem A: Reset + Pin Kombinasyonu**
1. Belirli bir GPIO pin'ini **GND'ye bağlayın**
   - Kartın dokümantasyonuna bakın (genellikle BOOT pin veya ISP pin)
   - Örnek: PA.13 veya benzeri bir pin
2. **Kartı resetleyin** (reset butonuna basın)
3. Pin'i **GND'den çıkarın**
4. ISP Tool'da **Connect** butonuna tıklayın

**Yöntem B: Boot Pin**
1. Kart üzerinde **BOOT** veya **ISP** pin'i var mı kontrol edin
2. Bu pin'i **GND'ye bağlayın**
3. Kartı resetleyin
4. ISP Tool ile bağlanmayı deneyin

**Yöntem C: Otomatik Mod**
1. Bazı kartlarda reset sonrası otomatik olarak ISP moduna geçer
2. Kartı resetleyin
3. **Hemen** (1-2 saniye içinde) ISP Tool'da Connect'e tıklayın

### 2. Port Yanlış Seçilmiş

**Kontrol:**
- COM18 doğru port mu?
- Device Manager'da hangi port görünüyor?
- Kart bağlı mı?

**Çözüm:**
1. **Device Manager'ı açın** (Windows)
2. **Ports (COM & LPT)** bölümüne bakın
3. Kartın hangi COM portunda olduğunu bulun
4. ISP Tool'da doğru port'u seçin

### 3. Baud Rate Yanlış

**Kontrol:**
- ISP Tool'da baud rate ayarı var mı?
- Genellikle 115200, 9600, 57600 olabilir

**Çözüm:**
1. ISP Tool'da baud rate ayarını kontrol edin
2. Farklı baud rate'ler deneyin:
   - 115200 (en yaygın)
   - 9600
   - 57600
   - 38400

### 4. ISP Bootloader Yüklü Değil

**Eğer kart fabrika çıkışı değilse veya flash silinmişse:**

ISP bootloader LDROM'da olmayabilir. Bu durumda:
- İlk kez **ICP Tool** ile yüklemeniz gerekir
- Veya başka bir programlanmış karttan kopyalayın

**Kontrol:**
- Kart fabrika çıkışı mı?
- Daha önce flash silindi mi?
- Başka bir programlama yapıldı mı?

### 5. UART Bağlantısı Çalışmıyor

**Kontrol:**
- USB kablosu bağlı mı?
- Port çalışıyor mu?
- Driver yüklü mü?

**Test:**
```bash
# Windows'ta Device Manager'da port görünüyor mu?
# Linux'ta:
ls -l /dev/tty* | grep -E "USB|ACM"
```

## Adım Adım Çözüm

### ⚠️ ÖNEMLİ: NuMaker-M263KI Kartında DIP Switch Var!

Kartınızın **sol üstünde DIP switch** var (VCOM, TXD, RXD yazıyor). Bu switch'ler ISP modu için kritik!

### Adım 1: DIP Switch Ayarları (ÖNCE BUNU YAPIN!)

1. **VCOM switch'ini AÇIK (ON) yapın**
   - UART haberleşmesi için gerekli
2. **TXD/RXD switch'lerini kontrol edin**
   - UART pin seçimi için

### Adım 2: Port Kontrolü

1. **Device Manager'ı açın** (Windows)
2. **Ports (COM & LPT)** bölümüne bakın
3. Kartın portunu bulun (COM18 veya başka)
4. ISP Tool'da doğru port'u seçin

### Adım 3: Kartı Bootloader Moduna Geçirin

**NuMaker-M263KI için:**

1. **DIP switch'leri ayarlayın** (VCOM açık)
2. **NRESET butonuna basın** (kartın sol tarafında)
3. **Hemen** (1-2 saniye içinde) ISP Tool'da Connect'e tıklayın

**Alternatif:**
- USB kablosunu çıkarıp takın (reset için)
- Hemen Connect'e tıklayın

**Alternatif:**
- Reset butonuna basın ve basılı tutun
- BOOT pin'ini GND'ye bağlayın
- Reset butonunu bırakın
- BOOT pin'ini serbest bırakın
- Connect'e tıklayın

### Adım 3: Timing (Zamanlama)

**Önemli:** ISP bootloader genellikle reset sonrası sadece belirli süre modda kalır (1-5 saniye).

1. Kartı resetleyin
2. **Hemen** (1-2 saniye içinde) Connect'e tıklayın
3. Beklemeyin, hemen deneyin

### Adım 4: Baud Rate Deneyin

ISP Tool'da baud rate ayarı varsa:
1. 115200 deneyin
2. Çalışmazsa 9600 deneyin
3. Çalışmazsa 57600 deneyin

### Adım 5: Kart Dokümantasyonuna Bakın

**NuMaker-M263KI için:**
- User Manual'da "ISP Mode" veya "Bootloader Mode" bölümüne bakın
- Hangi pin'ler kullanılır?
- Nasıl moda geçilir?
- Timing nedir?

## Hızlı Test

### Test 1: Port Çalışıyor mu?

```python
# Python ile port testi
import serial
ser = serial.Serial('COM18', 115200, timeout=1)
ser.write(b'TEST')
ser.close()
```

### Test 2: Bootloader Modunda mı?

1. Kartı bootloader moduna geçirin
2. Python scriptimizi çalıştırın:
   ```bash
   python3 uart_receiver.py COM18
   ```
3. Handshake yanıtı geliyor mu?

## Özet Kontrol Listesi

- [ ] Port doğru seçilmiş (COM18)
- [ ] Kart bağlı
- [ ] Driver yüklü
- [ ] Kart bootloader modunda (BOOT pin + Reset)
- [ ] Timing doğru (reset sonrası hemen)
- [ ] Baud rate doğru (115200)
- [ ] ISP bootloader yüklü (fabrika çıkışı kartlarda genellikle var)

## En Yaygın Çözüm

**%90 ihtimalle sorun:** Kart bootloader modunda değil

**Çözüm:**
1. BOOT pin'ini GND'ye bağlayın
2. Kartı resetleyin
3. BOOT pin'ini serbest bırakın
4. **Hemen** Connect'e tıklayın

## Not

Eğer hala bağlanamıyorsanız:
- Kartın dokümantasyonuna bakın
- ISP bootloader yüklü mü kontrol edin
- Farklı bir port deneyin
- Farklı bir USB kablosu deneyin

