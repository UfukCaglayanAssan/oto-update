# Nuvoton ISP Bootloader - Çözüm Önerileri

## 🔍 TESPİT EDİLEN SORUNLAR

### 1. ⚠️ Garip Yanıt Değerleri
- Paket No: 542462019 (normalde 1, 2, 3... olmalı)
- APROM Boyutu: 875962432 byte (çok büyük!)
- Bu değerler yanıt paketlerinin yanlış parse edildiğini gösteriyor

### 2. ⚠️ LED Yanıp Sönmüyor
- Firmware yazılıyor gibi görünüyor ama çalışmıyor
- CMD_RUN_APROM gönderiliyor ama reset atılmıyor olabilir

## 🎯 ÇÖZÜM ADIMLARI

### Adım 1: APROM Doğrulama (EN ÖNEMLİ!)

**ISP Tool ile kontrol edin:**
1. ISP Tool'u açın
2. Port'u seçin (/dev/ttyACM0)
3. "Read" tab'ına gidin
4. APROM'u okuyun (0x00000000'dan başlayarak)
5. Okunan veriyi kaydedin
6. Binary dosya ile karşılaştırın:
   ```bash
   diff -u <(hexdump -C NuvotonM26x-Bootloader-Test.bin) <(hexdump -C okunan_aprom.bin)
   ```

**Sonuç:**
- Eğer farklılık varsa → Firmware yazılmıyor!
- Eğer aynıysa → Firmware yazılıyor ama çalışmıyor!

### Adım 2: Reset Sonrası Kontrol

**UART mesajlarını dinleyin:**
```bash
python3 uart_listener.py /dev/ttyACM0
```

Reset sonrası:
- Yeni firmware'den mesaj geliyor mu?
- Eski firmware'den mesaj geliyor mu?
- Hiç mesaj gelmiyor mu?

### Adım 3: Paket Formatı Debug

**İlk paketi hex olarak yazdırın:**
```python
# uart_receiver_nuvoton.py'ye ekleyin:
print(f"İlk paket hex: {first_packet.hex()}")
```

**Beklenen format:**
```
Byte 0-3:   A0 00 00 00 (CMD_UPDATE_APROM)
Byte 4-7:   00 00 00 00 (atlanıyor)
Byte 8-11:  00 00 00 00 (Address: 0x00000000)
Byte 12-15: B8 1B 00 00 (TotalLen: 7128 = 0x00001BB8)
Byte 16-63: [48 byte firmware verisi]
```

### Adım 4: CMD_RUN_APROM Kontrolü

**CMD_RUN_APROM gönderildikten sonra:**
- Port kapanıyor mu? (Reset atılırsa port kapanır)
- Reset sonrası bootloader moduna geçiyor mu?

**Test:**
```python
# CMD_RUN_APROM gönder
# Port'u kapat
# 1 saniye bekle
# Port'u tekrar aç
# CMD_CONNECT gönder
# Yanıt geliyor mu? (Geliyorsa bootloader modunda)
```

### Adım 5: Firmware Doğrulama

**Binary dosyanın doğru olduğundan emin olun:**
1. Binary dosyayı hex olarak kontrol edin
2. İlk 4 byte: Stack pointer (genellikle 0x2000xxxx)
3. İkinci 4 byte: Reset handler adresi (genellikle 0x0000xxxx)
4. Bu değerler doğru mu?

## 🔧 HIZLI TESTLER

### Test 1: Basit LED Blink Firmware
LED yanıp sönen basit bir firmware yükleyin:
- Daha küçük dosya
- Daha basit kod
- Çalışıyor mu?

### Test 2: ISP Tool ile Manuel Yükleme
ISP Tool ile aynı firmware'i yükleyin:
- Çalışıyor mu?
- Çalışıyorsa → Python script sorunu
- Çalışmıyorsa → Firmware sorunu

### Test 3: Farklı Binary Dosya
Farklı bir binary dosya deneyin:
- Bilinen çalışan bir firmware
- Çalışıyor mu?

## 📋 DEBUG KODU EKLEMELERİ

### 1. Paket Hex Yazdırma
```python
print(f"Gönderilen paket: {packet.hex()}")
print(f"Alınan yanıt: {response.hex()}")
```

### 2. Yanıt Parse Detayları
```python
print(f"Yanıt byte 0-1 (checksum): {response[0]:02X} {response[1]:02X}")
print(f"Yanıt byte 2-3: {response[2]:02X} {response[3]:02X}")
print(f"Yanıt byte 4-7 (packet_no): {response[4:8].hex()}")
print(f"Yanıt byte 8-11 (aprom_size): {response[8:12].hex()}")
```

### 3. WriteData Sonrası Doğrulama
ISP_UART kodunda WriteData sonrası ReadData yapılıyor:
```c
WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
memset(pu8Src, 0, u32srclen);
ReadData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
```

Bu, yazılan veriyi okuyup kontrol ediyor. Eğer farklıysa hata var demektir.

## 🎯 EN MUHTEMEL SORUN

**Firmware yazılıyor ama CMD_RUN_APROM çalışmıyor veya reset sonrası eski firmware çalışıyor!**

**Çözüm:**
1. ISP Tool ile APROM'u okuyup kontrol edin
2. Reset sonrası UART mesajlarını dinleyin
3. CMD_RUN_APROM sonrası port kapanıyor mu kontrol edin

