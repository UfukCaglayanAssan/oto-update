# UART-to-USB ile Bootloader Yükleme (Programlayıcı Gerektirmez)

## Özet

Programlayıcı (ICP Tool/Nu-Link) olmadan, sadece UART-to-USB kablosu ile bootloader yükleyebilirsiniz!

## Gereksinimler

1. ✅ **USB-to-UART kablosu** (kartta zaten var)
2. ✅ **ISP Tool** (ücretsiz, indirilebilir)
3. ⚠️ **LDROM'da ISP bootloader** (genellikle fabrika çıkışı kartlarda var)

## Adım 1: ISP Bootloader Kontrolü

### Kartınızda ISP Bootloader Var mı?

**Fabrika çıkışı NuMaker-M263KI kartlarında genellikle LDROM'da ISP bootloader zaten yüklüdür!**

Kontrol etmek için:
1. Kartı USB ile bilgisayara bağlayın
2. ISP Tool'u açın
3. UART modunu seçin
4. Port'u seçin
5. Kartı bootloader moduna alın (reset + pin kombinasyonu)
6. Connect butonuna tıklayın

**Eğer bağlanırsa:** ✅ ISP bootloader var, devam edin!
**Eğer bağlanamazsa:** ❌ ISP bootloader yok, önce ICP Tool ile yüklemeniz gerekir

## Adım 2: ISP Tool İndirme ve Kurulum

1. **Nuvoton web sitesine gidin**
   - https://www.nuvoton.com/tool-and-software/software-development-tool/code-burning-tool/

2. **İndirme sayfasında:**
   - **NuMicro_ISP_Programming_Tool_V4.16** seçin
   - Windows veya Linux versiyonunu indirin

3. **Kurulum:**
   - İndirilen dosyayı çalıştırın
   - Kurulum talimatlarını izleyin

## Adım 3: Bootloader Moduna Geçme

### NuMaker-M263KI için Genellikle:

**Yöntem 1: Reset + Pin Kombinasyonu**
1. Belirli bir GPIO pin'ini GND'ye bağlayın (kartın dokümantasyonuna bakın)
2. Kartı resetleyin
3. Pin'i GND'den çıkarın
4. ISP Tool ile bağlanın

**Yöntem 2: Boot Pin**
1. Boot pin'ini aktif edin (kartın dokümantasyonuna bakın)
2. Kartı resetleyin
3. ISP Tool ile bağlanın

**Yöntem 3: Otomatik Mod**
1. Bazı kartlarda reset sonrası otomatik olarak ISP moduna geçer
2. ISP Tool ile bağlanmayı deneyin

### Kart Dokümantasyonu

Kartın kullanım kılavuzunda "ISP Mode" veya "Bootloader Mode" bölümüne bakın:
- Hangi pin'ler kullanılır?
- Nasıl moda geçilir?
- Ne kadar süre beklenir?

## Adım 4: ISP Tool ile Bootloader Yükleme

### 4.1. ISP Tool'u Açın

1. **ISP Tool'u çalıştırın**
2. **UART** modunu seçin (USB değil!)
3. Port'u seçin:
   - Windows: `COM3`, `COM4` vb.
   - Linux: `/dev/ttyUSB0`, `/dev/ttyACM0` vb.
4. Baud rate: **115200** (genellikle)

### 4.2. Bağlanın

1. Kartı bootloader moduna alın (yukarıdaki adımlar)
2. **Connect** butonuna tıklayın
3. Bağlantı başarılı olursa:
   - Chip bilgileri görünecek
   - Flash bölümleri görünecek

### 4.3. Bootloader'ı LDROM'a Yükleyin

**ÖNEMLİ**: Bootloader **LDROM** bölümüne yüklenmelidir!

1. **LDROM** (veya **Loader ROM**) sekmesini seçin
2. **Browse** butonuna tıklayın
3. Bootloader `.bin` veya `.hex` dosyanızı seçin
4. **Program** butonuna tıklayın
5. Yükleme tamamlanana kadar bekleyin
6. Başarılı mesajını kontrol edin

### 4.4. Uygulama Kodunu APROM'a Yükleyin (Opsiyonel)

1. **APROM** sekmesini seçin
2. **Browse** ile uygulama `.bin` dosyanızı seçin
3. **Program** butonuna tıklayın

## Adım 5: Test

Bootloader yüklendikten sonra:

1. Kartı normal moda geçirin (reset)
2. Python scriptimizi çalıştırın:
   ```bash
   python3 uart_receiver.py /dev/ttyACM0
   ```
3. Handshake yanıtı gelip gelmediğini kontrol edin

## Sorun Giderme

### ISP Tool Bağlanamıyor

**Nedenler:**
1. ISP bootloader yok → ICP Tool ile yükleyin
2. Bootloader modunda değil → Pin kombinasyonunu kontrol edin
3. Yanlış port → Port numarasını kontrol edin
4. Baud rate yanlış → 115200, 9600, 57600 deneyin

**Çözümler:**
- Kartın dokümantasyonuna bakın
- Farklı baud rate'ler deneyin
- Port'u kapatıp açın
- USB kablosunu çıkarıp takın

### Bootloader Yüklenmiyor

**Nedenler:**
1. Flash kilitli → Unlock veya Chip Erase yapın
2. Yanlış adres → LDROM adresine (0x00100000) derlenmiş olmalı
3. Dosya formatı → `.bin` veya `.hex` formatında olmalı

**Çözümler:**
- ISP Tool'da **Unlock** veya **Chip Erase** seçeneğini kullanın
- Bootloader'ı doğru adrese derlediğinizden emin olun

### Port Bulunamıyor

**Linux'ta:**
```bash
# Portları listele
ls -l /dev/tty* | grep -E "USB|ACM"

# Port izinlerini kontrol et
sudo chmod 666 /dev/ttyUSB0

# Kullanıcıyı dialout grubuna ekle
sudo usermod -a -G dialout $USER
# Sonra logout/login yapın
```

**Windows'ta:**
- Device Manager'da COM portlarını kontrol edin
- Driver güncel mi kontrol edin

## Alternatif: Python Scripti ile Test

ISP Tool ile bootloader yükledikten sonra, Python scriptimizle test edebilirsiniz:

```bash
python3 uart_receiver.py /dev/ttyACM0
```

## Özet

✅ **Programlayıcı gerekmez!**
✅ **Sadece USB-to-UART kablosu yeterli!**
✅ **ISP Tool ücretsiz ve indirilebilir!**
⚠️ **LDROM'da ISP bootloader olmalı (genellikle fabrika çıkışı kartlarda var)**

## Kaynaklar

- **ISP Tool**: https://github.com/OpenNuvoton/ISPTool
- **Nuvoton İndirme**: https://www.nuvoton.com/tool-and-software/software-development-tool/code-burning-tool/
- **Kart Dokümantasyonu**: NuMaker-M263KI User Manual

---

**Not**: Eğer kartınızda ISP bootloader yoksa, ilk kez ICP Tool ile yüklemeniz gerekir. Ama çoğu fabrika çıkışı kartta zaten var!

