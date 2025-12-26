# NuMaker-M263KI Yazılım Yükleme Rehberi

## Yöntem 1: Nu-Link Programlayıcı ile İlk Yükleme (Önerilen)

### Gereksinimler
- **Nu-Link Programlayıcı**: Kart üzerinde genellikle Nu-Link-Me veya harici Nu-Link programlayıcı
- **NuMicro ICP Programming Tool**: Nuvoton'un resmi programlama yazılımı
- **USB Kablosu**: Kartı bilgisayara bağlamak için

### Adımlar

1. **Yazılımı İndirin**
   - Nuvoton resmi web sitesinden **NuMicro ICP Programming Tool** indirin
   - Link: https://www.nuvoton.com/tool-and-software/software-development-tool/code-burning-tool/

2. **Kartı Bağlayın**
   - NuMaker-M263KI kartını USB kablosu ile bilgisayara bağlayın
   - Kart üzerindeki Nu-Link programlayıcı otomatik olarak tanınmalı

3. **ICP Tool'u Açın**
   - NuMicro ICP Programming Tool'u çalıştırın
   - Kart otomatik olarak algılanmalı

4. **Firmware Yükleyin**
   - **Connect** butonuna tıklayın
   - **APROM** veya **LDROM** seçin (genellikle APROM)
   - **Browse** ile `.bin` veya `.hex` dosyanızı seçin
   - **Start** butonuna tıklayın
   - Programlama tamamlanana kadar bekleyin

### Nu-Link-Me (Kart Üzerindeki Programlayıcı)

NuMaker-M263KI kartında genellikle **Nu-Link-Me** programlayıcı bulunur:
- Kartın USB portuna bağlandığında otomatik olarak programlayıcı olarak çalışır
- Ayrı bir programlayıcı gerekmez
- ICP Tool ile doğrudan kullanılabilir

---

## Yöntem 2: UART Bootloader ile Güncelleme (Bizim Scriptimiz)

Bu yöntem, kartta zaten bir bootloader yüklü olduğunda kullanılır.

### USB Bağlantısı (Önerilen - Kolay Yöntem) ✅

**Evet, resimdeki USB kablosunu bilgisayara bağlayabilirsiniz!**

NuMaker-M263KI kartında genellikle **USB-to-UART dönüştürücü** bulunur:
- Kartın üzerindeki **USB portuna** (resimde görünen) USB kablosu takılı
- Diğer ucunu **bilgisayarınıza** bağlayın
- Windows'ta: `COMx` portu olarak görünür (Device Manager'da kontrol edin)
- Linux'ta: `/dev/ttyUSB0` veya `/dev/ttyACM0` olarak görünür

**Kullanım:**
```bash
# Windows'ta
python uart_receiver.py COM3

# Linux'ta
python3 uart_receiver.py /dev/ttyUSB0

# Veya otomatik port tespiti
python3 uart_receiver.py
```

### Manuel UART Bağlantısı (Alternatif - Raspberry Pi ile)

Eğer USB portu yoksa veya farklı bir UART kullanmak istiyorsanız:

NuMaker-M263KI kartında UART pinleri:
- **UART0 TX**: Genellikle PA.0 veya PA.2 (kartın pinout'una bakın)
- **UART0 RX**: Genellikle PA.1 veya PA.3
- **GND**: Ortak toprak

Raspberry Pi bağlantısı:
```
NuMaker-M263KI          Raspberry Pi
-----------             -----------
UART0 TX  ----------->  GPIO 15 (RX)
UART0 RX  <-----------   GPIO 14 (TX)
GND       ----------->  GND
```

**ÖNEMLİ**: Raspberry Pi'nin 3.3V mantık seviyesi kullandığından emin olun. 5V kullanmayın!

### Adımlar

1. **Bootloader Moduna Geçirin**
   - Kartı resetleyin veya özel bir tuş kombinasyonu ile bootloader moduna geçirin
   - (Bootloader kodunuzda bu mekanizma olmalı)

2. **Python Scriptini Çalıştırın**
   ```bash
   python3 uart_receiver.py /dev/ttyS0
   ```
   veya otomatik port tespiti:
   ```bash
   python3 uart_receiver.py
   ```

3. **Güncelleme Otomatik Başlar**
   - Script handshake paketi gönderir
   - Bootloader yanıt verirse paketler gönderilir
   - Güncelleme tamamlanır

---

## Yöntem 3: ISP Tool ile UART Üzerinden Yükleme

Nuvoton'un resmi ISP (In-System Programming) aracı.

### USB Bağlantısı

**Evet, resimdeki USB kablosunu bilgisayara bağlayabilirsiniz!**

- Kartın üzerindeki **USB portuna** takılı olan kabloyu bilgisayara bağlayın
- Windows'ta: Device Manager'da `COMx` portu görünecek
- Linux'ta: `/dev/ttyUSB0` veya `/dev/ttyACM0` olarak görünecek

### Gereksinimler
- **ISPTool**: Nuvoton'un ISP programlama aracı
- USB kablosu (kartta zaten var)
- LDROM'da ISP bootloader olmalı (ilk yükleme için ICP Tool ile yüklenir)

### Adımlar

1. **USB Kablosunu Bağlayın**
   - Kartın USB portundaki kabloyu bilgisayara takın
   - Port numarasını not edin (Windows: COM3, Linux: /dev/ttyUSB0)

2. **ISPTool'u İndirin**
   - Nuvoton web sitesinden ISPTool indirin
   - GitHub: https://github.com/OpenNuvoton/ISPTool
   - Windows/Linux versiyonunu indirin

3. **ISPTool'u Açın**
   - ISPTool'u çalıştırın
   - **UART** modunu seçin
   - Port'u seçin (COMx veya /dev/ttyUSB0)
   - Baud rate: 115200 (genellikle)

4. **Kartı Bootloader Moduna Alın**
   - Kartı resetleyin
   - Veya belirli pin kombinasyonu ile bootloader moduna geçin
   - (Kartın dokümantasyonuna bakın)

5. **Bağlanın**
   - **Connect** butonuna tıklayın
   - Bağlantı başarılı olursa kart bilgileri görünecek

6. **Firmware Yükleyin**
   - **Browse** ile `.bin` dosyanızı seçin
   - **Program** butonuna tıklayın
   - Güncelleme tamamlanana kadar bekleyin

**Not**: İlk kez kullanıyorsanız, önce ICP Tool ile LDROM'a ISP bootloader yüklemeniz gerekebilir.

---

## Yöntem 4: Keil MDK / IAR ile Programlama

Geliştirme sırasında IDE üzerinden programlama.

### Keil MDK-ARM

1. **Projeyi Açın**
   - Keil MDK-ARM'de projenizi açın

2. **Nu-Link Driver Yükleyin**
   - Nu-Link driver'ı yüklü olmalı
   - Nuvoton paketini Keil'e yükleyin

3. **Programlama**
   - **Flash > Download** (F8) ile programlayın
   - Veya **Flash > Erase** ile silip sonra programlayın

### IAR Embedded Workbench

1. **Projeyi Açın**
   - IAR'da projenizi açın

2. **Nu-Link Ayarları**
   - Project > Options > Debugger > Nu-Link
   - Nu-Link driver'ı seçin

3. **Programlama**
   - **Project > Download and Debug** ile programlayın

---

## Bootloader Geliştirme ve Yükleme

### İlk Bootloader Yükleme

1. **Bootloader Kodunu Derleyin**
   ```bash
   # Keil veya IAR ile derleyin
   # .bin veya .hex dosyası oluşturun
   ```

2. **LDROM'a Yükleyin**
   - ICP Tool ile **LDROM** seçeneğini kullanın
   - Bootloader'ı LDROM'a yükleyin
   - APROM'u normal uygulama için kullanın

3. **Uygulama Kodunu APROM'a Yükleyin**
   - Normal uygulama kodunuzu APROM'a yükleyin
   - Bootloader, APROM'daki uygulamayı çalıştırır

### Bootloader ile Güncelleme

Bootloader yüklendikten sonra:
- UART üzerinden Python scriptimiz ile güncelleme yapabilirsiniz
- Bootloader, APROM'u günceller
- Güncelleme sonrası yeni firmware çalışır

---

## Sorun Giderme

### Kart Tanınmıyor

1. **Driver Kontrolü**
   - Windows Device Manager'da Nu-Link görünüyor mu?
   - Driver güncel mi?

2. **USB Kablosu**
   - Veri kablosu kullanın (sadece şarj kablosu değil)
   - Farklı bir USB portu deneyin

3. **ICP Tool Versiyonu**
   - En son versiyonu kullanın
   - Nuvoton web sitesinden güncelleyin

### UART Bağlantısı Çalışmıyor

1. **Pin Bağlantıları**
   - TX-RX çapraz bağlı mı? (TX->RX, RX->TX)
   - GND ortak mı?
   - 3.3V mantık seviyesi kullanılıyor mu?

2. **Baud Rate**
   - Her iki tarafta da aynı baud rate (115200)
   - Parity, stop bit ayarları kontrol edin

3. **Port Kontrolü**
   ```bash
   # Linux'ta portları listeleyin
   ls -l /dev/tty*
   
   # Port izinlerini kontrol edin
   sudo chmod 666 /dev/ttyUSB0
   ```

### Programlama Hatası

1. **Flash Kilitli mi?**
   - ICP Tool'da **Unlock** seçeneğini deneyin
   - Chip Erase yapın

2. **Yanlış Adres**
   - APROM/LDROM adreslerini kontrol edin
   - Memory map'e bakın

3. **Bootloader Çakışması**
   - Eski bootloader'ı silin
   - Tam chip erase yapın

---

## Önemli Notlar

### Flash Bölümleme (M263KI için örnek)

- **LDROM**: 0x00100000 - 0x00100FFF (4 KB) - Bootloader için
- **APROM**: 0x00000000 - 0x000FFFFF (1 MB) - Uygulama için
- **Data Flash**: 0x00300000 - 0x00300FFF (4 KB) - Konfigürasyon için

### Güvenlik

- Production'da bootloader'ı koruyun
- Flash lock bitlerini kullanın
- Checksum/CRC kontrolü yapın

### Kaynaklar

- **Nuvoton Resmi Site**: https://www.nuvoton.com/
- **NuMaker-M263KI Dokümantasyon**: Nuvoton web sitesinden indirin
- **ISP Tool GitHub**: https://github.com/OpenNuvoton/ISPTool
- **BSP ve Örnekler**: Nuvoton GitHub reposu

---

## Hızlı Başlangıç Özeti

**İlk Yükleme (Bootloader yoksa):**
1. NuMicro ICP Tool indir
2. Kartı USB ile bağla
3. ICP Tool'da Connect > Browse > Start

**Güncelleme (Bootloader varsa):**
1. UART bağlantısı yap
2. `python3 uart_receiver.py` çalıştır
3. Otomatik güncelleme başlar

