# Nuvoton ISP - Kritik Düzeltmeler

## 🔧 Yapılan Kritik Düzeltmeler

### 1. ✅ CMD_SYNC_PACKNO Eklendi (ÖNEMLİ!)

**Sorun:** Paket numarası senkronizasyonu eksikti. Bootloader paket numarasını 1'den başlatmıyordu.

**Çözüm:**
```python
# CMD_CONNECT sonrası hemen paket numarasını senkronize et
sync_packet = create_packet(CMD_SYNC_PACKNO, 1)  # Paket numarasını 1 yap
send_packet(ser, sync_packet)
```

**Neden Önemli:**
- Bootloader paket numarasını takip ediyor
- Senkronizasyon olmazsa paketler "almış" gibi görünür ama belleğe yazılmaz
- ISP_UART kodunda: `if(u32Lcmd == CMD_SYNC_PACKNO) { u32PackNo = inpw(pu8Src); }`

### 2. ✅ CMD_ERASE_ALL Eklendi (Opsiyonel ama Önerilen)

**Sorun:** Flash üzerine yazma yapmadan önce sayfa silinmeli.

**Çözüm:**
```python
# Güncelleme öncesi tam silme
erase_packet = create_packet(CMD_ERASE_ALL)
send_packet(ser, erase_packet)
time.sleep(1.0)  # Silme işlemi zaman alır
```

**Neden Önemli:**
- Flash üzerine yazma yapmadan önce sayfa silinmeli
- CMD_UPDATE_APROM içinde otomatik silme var ama tam silme daha güvenli
- ⚠️ **UYARI:** Tüm APROM'u siler!

### 3. ✅ CMD_RUN_APROM İyileştirildi

**Sorun:** Reset sonrası firmware çalışıp çalışmadığı kontrol edilmiyordu.

**Çözüm:**
- Port durumu kontrolü
- Reset sonrası mesaj kontrolü
- Yeni firmware tespiti

**Kod:**
```python
if ser.is_open:
    # Reset sonrası mesaj kontrolü
    if "CPU @" in ascii_text:
        print("→ Yeni firmware çalışıyor!")
```

## 📋 Komut Sırası (Doğru Akış)

```
1. CMD_CONNECT (0xAE)
   ↓
2. CMD_SYNC_PACKNO (0xA4) ← YENİ EKLENDİ!
   ↓
3. CMD_GET_DEVICEID (0xB1) [Opsiyonel]
   ↓
4. CMD_ERASE_ALL (0xA3) [Opsiyonel ama önerilen]
   ↓
5. CMD_UPDATE_APROM (0xA0) - İlk paket
   ↓
6. CMD_UPDATE_APROM (0xA0) - Devam paketleri
   ↓
7. CMD_RUN_APROM (0xAB) - Reset ve APROM'a geçiş
```

## ⚠️ Config Bitleri (Nuvoton Tarafında)

**Not:** Bu Python tarafında yapılamaz, Nuvoton tarafında kontrol edilmeli:

1. **APROM Update Enable:**
   - Config0 register'ında APROM güncelleme izni açık olmalı
   - ISP Tool ile kontrol edilebilir

2. **Boot Seçeneği:**
   - CBS (Config Boot Selection) LDROM olmalı
   - Veya ISP pin çekilmiş olmalı

3. **Security Lock:**
   - Security Lock bit aktifse yazma engellenir
   - Mass Erase gerekebilir

## 🔍 Sorun Giderme

### Sorun: "Güncelleme tamamlandı" ama cihaz değişmiyor

**Olası Nedenler:**
1. Config bitleri yazma koruması uyguluyor
2. CMD_SYNC_PACKNO gönderilmedi (paketler yazılmadı)
3. CMD_RUN_APROM çalışmadı (reset atılmadı)
4. Firmware linker script'i yanlış (başlangıç adresi yanlış)

**Çözümler:**
1. ISP Tool ile Config0'ı kontrol et
2. CMD_SYNC_PACKNO eklendi mi kontrol et
3. CMD_RUN_APROM sonrası port kapandı mı kontrol et
4. Firmware'in başlangıç adresini kontrol et (0x00000000)

### Sorun: Paketler gönderiliyor ama yazılmıyor

**Olası Neden:**
- CMD_SYNC_PACKNO eksik
- Paket numarası uyumsuz

**Çözüm:**
- CMD_CONNECT sonrası CMD_SYNC_PACKNO gönder
- Paket numarası kontrolü yap

## 📊 Test Senaryoları

### Test 1: Paket Numarası Senkronizasyonu
```python
# CMD_CONNECT sonrası
sync_packet = create_packet(CMD_SYNC_PACKNO, 1)
send_packet(ser, sync_packet)
# Yanıt kontrolü
```

### Test 2: Tam Silme
```python
# Güncelleme öncesi
erase_packet = create_packet(CMD_ERASE_ALL)
send_packet(ser, erase_packet)
time.sleep(1.0)  # Silme için bekle
```

### Test 3: Reset Sonrası Kontrol
```python
# CMD_RUN_APROM sonrası
if ser.is_open:
    response = ser.read(ser.in_waiting)
    if "CPU @" in response.decode('ascii', errors='ignore'):
        print("✓ Yeni firmware çalışıyor!")
```

## 🎯 Sonuç

Bu düzeltmelerle:
1. ✅ Paket numarası senkronizasyonu yapılıyor
2. ✅ Güncelleme öncesi tam silme seçeneği var
3. ✅ Reset sonrası firmware kontrolü yapılıyor
4. ✅ Daha güvenilir güncelleme süreci

**Önemli:** Config bitleri Python tarafında kontrol edilemez, Nuvoton tarafında (ISP Tool ile) kontrol edilmeli!

