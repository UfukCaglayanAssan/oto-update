# Bootloader Yakalama Sorun Giderme

## 🔍 Sorun: Bootloader Yakalanamıyor

### Olası Nedenler

1. **Reset Yapılmadı veya Çok Geç Yapıldı**
   - Bootloader sadece reset sonrası 300ms içinde aktif
   - Reset butonuna basın ve HEMEN bırakın (basılı tutmayın!)

2. **Bootloader LDROM'da Değil**
   - Config0 ayarları LDROM boot olmalı
   - ISP Tool ile kontrol edin

3. **Port Bağlantısı Sorunlu**
   - TX → RX bağlantısı doğru mu?
   - GND bağlı mı?
   - Baud rate 115200 mi?

4. **Bootloader Yüklü Değil**
   - ISP Tool ile LDROM'a bootloader yüklenmeli
   - LDROM adresi: 0x00100000

5. **TX/RX Pinleri Ters**
   - TX → RX bağlantısı kontrol edin
   - Gerekirse ters bağlayın

## 🔧 Çözüm Adımları

### Adım 1: Reset Kontrolü
```bash
# Script çalışırken reset butonuna basın
# Reset yaptıktan HEMEN sonra script yakalayacak
```

### Adım 2: Port Bağlantısı Kontrolü
```bash
# Port'u kontrol et
ls -l /dev/ttyACM0

# Port izinlerini kontrol et
sudo chmod 666 /dev/ttyACM0
```

### Adım 3: ISP Tool ile Config0 Kontrolü
1. ISP Tool'u açın
2. Config tab'ına gidin
3. CBS (Chip Boot Selection) LDROM olmalı
4. APROM Update Enable açık olmalı

### Adım 4: Bootloader Yükleme
1. ISP Tool ile LDROM'a bootloader yükleyin
2. LDROM adresi: 0x00100000
3. Offset: 0x00000000

### Adım 5: Debug Modu
Script her 500 denemede bir debug bilgisi gösteriyor:
- Input buffer boyutu
- Gelen yanıt (hex)
- ASCII preview

## 📊 Test Senaryoları

### Test 1: Reset Timing
1. Script'i çalıştırın
2. Reset butonuna basın
3. Hemen bırakın
4. 300ms içinde yakalanmalı

### Test 2: Port Bağlantısı
1. UART listener ile test edin
2. Reset sonrası mesaj geliyor mu?
3. Mesaj geliyorsa port bağlantısı OK

### Test 3: Bootloader Kontrolü
1. ISP Tool ile bağlanın
2. LDROM'da bootloader var mı?
3. Config0 ayarları doğru mu?

## ⚠️ Önemli Notlar

1. **300ms Penceresi Çok Kısa!**
   - Reset sonrası hemen CMD_CONNECT gönderilmeli
   - Script sürekli gönderiyor ama reset yapmanız gerekiyor

2. **Reset Butonu**
   - Basın ve HEMEN bırakın
   - Basılı tutmayın!

3. **Port Bağlantısı**
   - TX → RX doğru bağlı olmalı
   - GND bağlı olmalı
   - Baud rate 115200 olmalı

4. **Bootloader Yükleme**
   - ISP Tool ile LDROM'a yüklenmeli
   - LDROM adresi: 0x00100000

## 🎯 Hızlı Kontrol Listesi

- [ ] Reset yapıldı mı?
- [ ] Port bağlantısı doğru mu? (TX/RX)
- [ ] GND bağlı mı?
- [ ] Baud rate 115200 mi?
- [ ] Bootloader LDROM'da mı?
- [ ] Config0 LDROM boot mu?
- [ ] APROM Update Enable açık mı?

