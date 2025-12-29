# Bootloader Yükleme Adımları - NuMaker-M263KI

## Özet

Python scriptimizle gönderdiğimiz paketleri dinleyecek bootloader'ı karta yüklemek için aşağıdaki adımları izleyin.

## Gereksinimler

1. **NuMicro ICP Programming Tool** - İndirin ve kurun
2. **Bootloader kodu** - Derlenmiş `.bin` veya `.hex` dosyası
3. **Nu-Link programlayıcı** - Kart üzerinde zaten var (Nu-Link-Me)

## Adım 1: Bootloader Kodunu Hazırlama

### Seçenek A: Mevcut Bootloader Kullanma

Eğer hazır bir bootloader'ınız varsa:
- `.bin` veya `.hex` dosyasını hazırlayın
- Doğrudan Adım 2'ye geçin

### Seçenek B: Bootloader Kodunu Geliştirme

1. **Nuvoton BSP (Board Support Package) İndirin**
   - Nuvoton web sitesinden M263KI için BSP indirin
   - GitHub: https://github.com/OpenNuvoton/Nuvoton_M263KI_BSP

2. **Bootloader Kodunu Yazın**
   - `nuvoton_bootloader_example.c` dosyamızı referans alın
   - Nuvoton SDK fonksiyonlarını kullanın
   - UART, Flash yazma fonksiyonlarını implement edin

3. **Derleyin**
   - **Keil MDK-ARM** veya **IAR Embedded Workbench** kullanın
   - Bootloader'ı **LDROM** adresine derleyin (genellikle 0x00100000)
   - `.bin` veya `.hex` dosyası oluşturun

## Adım 2: ICP Tool ile Bootloader Yükleme

### 2.1. ICP Tool'u Açın

1. **NuMicro ICP Programming Tool**'u çalıştırın
2. Kartı USB kablosu ile bilgisayara bağlayın
3. Tool otomatik olarak kartı algılamalı

### 2.2. Bağlantı Ayarları

1. **Connect** butonuna tıklayın
2. Kart bağlantısı başarılı olursa:
   - Chip bilgileri görünecek
   - Flash bölümleri görünecek

### 2.3. Bootloader'ı LDROM'a Yükleyin

**ÖNEMLİ**: Bootloader **LDROM** bölümüne yüklenmelidir!

1. **LDROM** sekmesini seçin (veya **Loader ROM** bölümünü seçin)
2. **Browse** butonuna tıklayın
3. Bootloader `.bin` veya `.hex` dosyanızı seçin
4. **Start** veya **Program** butonuna tıklayın
5. Yükleme tamamlanana kadar bekleyin

### 2.4. Doğrulama

1. Yükleme başarılı mesajını kontrol edin
2. **Verify** butonu ile doğrulama yapabilirsiniz
3. Kartı resetleyin

## Adım 3: Bootloader'ı Test Etme

### 3.1. Python Scripti ile Test

1. Kartı resetleyin
2. Bootloader moduna geçirin (kodunuzda nasıl geçileceğini belirlemiş olmalısınız)
3. Python scriptimizi çalıştırın:
   ```bash
   python3 uart_receiver.py /dev/ttyACM0
   ```
4. Handshake yanıtı gelip gelmediğini kontrol edin

### 3.2. Beklenen Sonuç

- Handshake paketi gönderildiğinde bootloader `0xAA` yanıtı vermeli
- Paketler gönderildiğinde bootloader bunları işlemeli
- Flash'a yazma işlemi başarılı olmalı

## Adım 4: Uygulama Kodunu APROM'a Yükleme

Bootloader yüklendikten sonra:

1. **APROM** sekmesini seçin
2. Uygulama `.bin` veya `.hex` dosyanızı seçin
3. **Start** butonuna tıklayın
4. Uygulama APROM'a yüklenecek
5. Bootloader, APROM'daki uygulamayı çalıştıracak

## Sorun Giderme

### Bootloader Yüklenmiyor

1. **Port Kontrolü**
   - Device Manager'da Nu-Link görünüyor mu?
   - Driver güncel mi?

2. **Flash Kilitli**
   - **Unlock** veya **Chip Erase** yapın
   - ICP Tool'da bu seçenekleri kullanın

3. **Yanlış Adres**
   - Bootloader LDROM adresine (0x00100000) derlenmiş olmalı
   - Derleme ayarlarını kontrol edin

### Bootloader Çalışmıyor

1. **Reset Sonrası Kontrol**
   - Kart resetlendiğinde bootloader çalışıyor mu?
   - UART'tan veri geliyor mu?

2. **Baud Rate**
   - Bootloader kodunda baud rate 115200 mi?
   - Python scripti ile aynı mı?

3. **Pin Kontrolü**
   - UART pinleri doğru mu?
   - USB-to-UART dönüştürücü hangi UART'ı kullanıyor?

### Handshake Yanıtı Yok

1. **Bootloader Modunda mı?**
   - Bootloader kodunuz reset sonrası otomatik moda geçiyor mu?
   - Özel bir tuş kombinasyonu gerekiyor mu?

2. **UART Bağlantısı**
   - TX-RX çapraz bağlı mı?
   - GND ortak mı?

3. **Bootloader Kodu**
   - Handshake fonksiyonu doğru çalışıyor mu?
   - UART okuma fonksiyonları doğru mu?

## Önemli Notlar

### Flash Bölümleme (M263KI için örnek)

- **LDROM**: 0x00100000 - 0x00100FFF (4 KB) - Bootloader için
- **APROM**: 0x00000000 - 0x000FFFFF (1 MB) - Uygulama için
- **Data Flash**: 0x00300000 - 0x00300FFF (4 KB) - Konfigürasyon için

### Bootloader Geliştirme İpuçları

1. **Watchdog Timer**: Sistem donmasını önlemek için kullanın
2. **Timeout Mekanizması**: Her işlem için timeout ekleyin
3. **Hata Yönetimi**: Checksum hatalarını kontrol edin
4. **LED Göstergeleri**: Debug için LED kullanın
5. **UART Debug**: UART üzerinden debug mesajları gönderin

### Güvenlik

- Production'da bootloader'ı koruyun
- Flash lock bitlerini kullanın
- Bootloader'ın üzerine yazılmasını engelleyin

## Kaynaklar

- **Nuvoton BSP**: https://github.com/OpenNuvoton/Nuvoton_M263KI_BSP
- **ICP Tool**: Nuvoton web sitesinden indirin
- **Bootloader Örnek Kodu**: `nuvoton_bootloader_example.c`
- **Bootloader Notları**: `BOOTLOADER_NOTLARI.md`

## Hızlı Başlangıç Özeti

1. ✅ **ICP Tool indir ve kur**
2. ✅ **Bootloader kodunu derle** (veya hazır bootloader kullan)
3. ✅ **ICP Tool ile LDROM'a bootloader yükle**
4. ✅ **Python scripti ile test et**
5. ✅ **Uygulama kodunu APROM'a yükle**

---

**Not**: Eğer hazır bir bootloader'ınız yoksa, önce `nuvoton_bootloader_example.c` dosyasını Nuvoton SDK'ya göre uyarlayıp derlemeniz gerekiyor.

