# NuMaker-M263KI DIP Switch Kullanımı

## Kartınızda Gördüğüm Önemli Detaylar

### DIP Switch (Sol Üstte)

Kartınızın sol üstünde **DIP switch** var ve üzerinde şunlar yazıyor:
- **VCOM**
- **TXD** 
- **RXD**

Bu switch'ler **UART bağlantısı ve ISP modu** için kullanılır!

## DIP Switch Ayarları

### ISP Bootloader Modu İçin

**ISP Tool ile bağlanmak için:**

1. **DIP switch'leri kontrol edin**
   - VCOM: Açık (ON) olmalı (UART haberleşmesi için)
   - TXD/RXD: UART pinlerini seçmek için

2. **Kartı resetleyin**
   - **NRESET** butonuna basın
   - Veya kartı USB'den çıkarıp takın

3. **ISP Tool'da Connect'e tıklayın**
   - Reset sonrası hemen (1-2 saniye içinde)

### Normal UART Kullanımı İçin

**Python scripti ile haberleşmek için:**

1. **DIP switch'leri ayarlayın**
   - VCOM: Açık (ON)
   - TXD/RXD: UART pinlerini seçin

2. **USB kablosunu bağlayın**
   - Üstteki micro-USB port (Nu-Link2-Me)
   - Veya alttaki USB OTG portu

## USB Portları

Kartınızda **iki USB port** var:

1. **Üstteki micro-USB** (Nu-Link2-Me)
   - Programlayıcı için
   - VCOM (Virtual COM) portu sağlar
   - ISP Tool ile kullanılabilir

2. **Alttaki USB OTG**
   - USB On-The-Go için
   - Genellikle uygulama için

## ISP Tool Bağlantısı İçin Adımlar

### Adım 1: DIP Switch Ayarları

1. **VCOM switch'ini AÇIK (ON) yapın**
2. **TXD/RXD switch'lerini kontrol edin**
   - Hangi UART pinlerini kullanacağınızı belirler

### Adım 2: USB Bağlantısı

1. **Üstteki micro-USB portuna** kabloyu takın
2. Bilgisayara bağlayın
3. Port'u kontrol edin (COM18 veya başka)

### Adım 3: Kartı Resetleyin

1. **NRESET butonuna basın**
2. Veya USB kablosunu çıkarıp takın

### Adım 4: ISP Tool'da Bağlanın

1. **ISP Tool'u açın**
2. **UART** modunu seçin
3. **Port'u seçin** (COM18)
4. **Connect** butonuna tıklayın
5. **Hemen** tıklayın (reset sonrası 1-2 saniye içinde)

## DIP Switch Konumları

Kartınızda DIP switch'in hangi konumda olduğunu kontrol edin:

- **VCOM**: Açık (ON) → UART haberleşmesi aktif
- **TXD/RXD**: UART pin seçimi için

## Sorun Giderme

### Hala "Waiting for device connection" Hatası

1. **DIP switch'leri kontrol edin**
   - VCOM açık mı?
   - TXD/RXD doğru ayarlanmış mı?

2. **Reset yaptınız mı?**
   - NRESET butonuna basın
   - Veya USB kablosunu çıkarıp takın

3. **Timing doğru mu?**
   - Reset sonrası **hemen** Connect'e tıklayın
   - 1-2 saniye içinde

4. **Port doğru mu?**
   - Device Manager'da hangi port görünüyor?
   - ISP Tool'da doğru port seçili mi?

### Python Scripti ile Test

DIP switch'leri ayarladıktan sonra:

```bash
python3 uart_receiver.py COM18
# veya
python3 uart_receiver.py /dev/ttyACM0
```

## Özet

✅ **DIP switch'leri kontrol edin** (VCOM açık olmalı)
✅ **Kartı resetleyin** (NRESET butonu)
✅ **Hemen Connect'e tıklayın** (1-2 saniye içinde)
✅ **Port doğru mu kontrol edin**

## Not

DIP switch ayarları kartın dokümantasyonunda detaylı olarak açıklanmıştır. Eğer hala bağlanamıyorsanız, kartın User Manual'ına bakın.

