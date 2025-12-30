# Nuvoton ISP Bootloader - Detaylı Sorun Analizi

## 🔍 TESPİT EDİLEN SORUNLAR

### 1. ⚠️ Yanıt Paketi Parse Hatası

**Garip Değerler:**
- Paket No: 542462019 (normalde 1, 2, 3... olmalı)
- APROM Boyutu: 875962432 byte (0x34362040) - Çok büyük!
- DataFlash Adresi: 0x30303030 (ASCII "0000")
- Cihaz ID: 0x7C0A0D2B

**Neden:**
Yanıt paketlerini yanlış parse ediyoruz olabilir. ISP_UART kodunda:
- `outps(pu8Response, u16Lcksum)` - Byte 0-1: Checksum (16-bit)
- `outpw(pu8Response + 4, u32PackNo)` - Byte 4-7: Paket No (32-bit)

Ama biz:
- Checksum: Byte 0-1 ✓
- Paket No: Byte 4-7 ✓
- APROM Size: Byte 8-11 ✓

**Sorun:** Byte 2-3'te ne var? `outpw(pu8Response + 4, 0)` ile 0 yazılıyor ama...

### 2. ⚠️ Paket Formatı Kontrolü

**İlk Paket (CMD_UPDATE_APROM):**
```
Byte 0-3:   CMD_UPDATE_APROM (0x000000A0)
Byte 4-7:   (pu8Src += 8, atlanıyor)
Byte 8-11:  Address (0x00000000)
Byte 12-15: TotalLen (7128)
Byte 16-63: Data (48 byte)
```

**Devam Paketleri:**
```
Byte 0-3:   CMD_UPDATE_APROM (0x000000A0)
Byte 4-7:   (pu8Src += 8, atlanıyor)
Byte 8-63:  Data (56 byte)
```

**Kontrol:** Kodumuz doğru görünüyor!

### 3. ⚠️ Veri Yazma İşlemi

ISP_UART kodunda:
```c
WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
```

Bu fonksiyon:
- `FMC_Proc(FMC_ISPCMD_PROGRAM, addr_start, addr_end, data)` çağırıyor
- Her 4 byte'ı (32-bit word) yazıyor
- `u32Addr += 4` ile ilerliyor

**Sorun:** Veri 4 byte'a hizalanmış mı? Değilse yazma başarısız olabilir!

### 4. ⚠️ CMD_RUN_APROM Çalışmıyor Olabilir

ISP_UART kodunda:
```c
else if(u32Lcmd == CMD_RUN_APROM)
{
    FMC_SetVectorPageAddr(FMC_APROM_BASE);
    NVIC_SystemReset();
    while(1);
}
```

**Sorun:** CMD_RUN_APROM gönderiliyor ama reset atılmıyor olabilir.

## 🎯 OLASI ÇÖZÜMLER

### Çözüm 1: Yanıt Paketi Parse Düzeltmesi

Byte 2-3'ü kontrol et:
```python
# Şu an:
checksum = (response[1] << 8) | response[0]  # Byte 0-1

# Belki:
checksum = (response[0] << 8) | response[1]  # Big-endian?
```

### Çözüm 2: Veri Hizalama Kontrolü

Firmware 4 byte'a hizalanmış mı kontrol et:
```python
if len(bin_data) % 4 != 0:
    # 4 byte'a hizala
    padding = 4 - (len(bin_data) % 4)
    bin_data += bytes([0xFF] * padding)
```

### Çözüm 3: APROM Doğrulama

ISP Tool ile APROM'u okuyup kontrol et:
1. ISP Tool'u aç
2. APROM'u oku (Read tab)
3. Binary dosya ile karşılaştır
4. Farklılık var mı kontrol et

### Çözüm 4: Reset Sonrası Kontrol

Reset sonrası UART mesajlarını kontrol et:
```bash
python3 uart_listener.py /dev/ttyACM0
```

Yeni firmware'den mesaj geliyor mu?

## 📋 TEST ADIMLARI

1. **APROM Doğrulama:**
   - ISP Tool ile APROM'u oku
   - Binary dosya ile karşılaştır
   - Farklılık var mı?

2. **Reset Sonrası Kontrol:**
   - Reset sonrası UART mesajlarını dinle
   - Yeni firmware'den mesaj geliyor mu?

3. **Paket Formatı Testi:**
   - İlk paketi hex olarak yazdır
   - ISP_UART formatına uygun mu kontrol et

4. **CMD_RUN_APROM Testi:**
   - CMD_RUN_APROM gönderildikten sonra reset atılıyor mu?
   - Port kapanıyor mu? (Reset atılırsa port kapanır)

