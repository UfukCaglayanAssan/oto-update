# Nuvoton ISP Bootloader Sorun Analizi

## 🔍 TESPİT EDİLEN SORUNLAR

### 1. ⚠️ Paket Numaraları Garip
- Paket No: 542462019, 757935405, 1701736047...
- Bu değerler normal değil! Normalde 1, 2, 3... olmalı
- **Sorun:** Yanıt paketlerini yanlış parse ediyoruz olabilir

### 2. ⚠️ APROM Boyutu Garip
- APROM Boyutu: 875962432 byte (0x34362040)
- Bu çok büyük! Normalde 64KB-512KB arası olmalı
- **Sorun:** Yanıt paketini yanlış okuyoruz

### 3. ⚠️ DataFlash Adresi Garip
- DataFlash Adresi: 0x30303030
- Bu ASCII "0000" gibi görünüyor
- **Sorun:** Yanıt paketini yanlış parse ediyoruz

### 4. ⚠️ Cihaz ID Garip
- Cihaz ID: 0x7C0A0D2B
- Bu değer de garip görünüyor
- **Sorun:** Yanıt paketini yanlış okuyoruz

## 📋 ISP_UART KOD ANALİZİ

### Paket Formatı (ParseCmd fonksiyonu):

```c
u32Lcmd = inpw(pu8Src);        // Byte 0-3: Komut
outpw(pu8Response + 4, 0);
pu8Src += 8;                    // İlk 8 byte atlanır
u32srclen -= 8;

// CMD_UPDATE_APROM için:
u32StartAddress = inpw(pu8Src);      // Byte 8-11: Address
u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15: TotalLen
u32TotalLen = inpw(pu8Src + 4);      // Tekrar okunur (satır 111)
pu8Src += 8;                         // Byte 16'ya geçilir
u32srclen -= 8;

// Veri yazma:
WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
// pu8Src artık byte 16'da, yani Byte 16-63 = 48 byte veri
```

### Yanıt Formatı:

```c
out:
    u16Lcksum = Checksum(pu8Buffer, u8len);
    outps(pu8Response, u16Lcksum);        // Byte 0-1: Checksum (16-bit)
    ++u32PackNo;
    outpw(pu8Response + 4, u32PackNo);     // Byte 4-7: Paket No (uint32_t)
    u32PackNo++;
```

**Yanıt Paketi:**
- Byte 0-1: Checksum (16-bit, little-endian)
- Byte 2-3: 0x00 0x00 (outpw ile 0 yazılmış)
- Byte 4-7: Paket No (uint32_t, little-endian)
- Byte 8-63: Diğer veriler

## 🔧 SORUNLAR

### Sorun 1: Yanıt Paketi Parse Hatası

Python kodumuzda:
```python
checksum = (response[1] << 8) | response[0]  # 16-bit little-endian ✓
packet_no = bytes_to_uint32(response, 4)      # Byte 4-7 ✓
aprom_size = bytes_to_uint32(response, 8)      # Byte 8-11 ✓
```

Ama ISP_UART kodunda:
- Line 48: `ReadData(Config0, Config0 + 16, (unsigned int *)(pu8Response + 8));`
- Bu her komutta çalışıyor ve response + 8'e config yazıyor!
- CMD_CONNECT'te bu üzerine yazılıyor (line 80-81)

**CMD_CONNECT yanıtı:**
- Byte 0-1: Checksum
- Byte 2-3: 0x00 0x00
- Byte 4-7: Paket No
- Byte 8-11: APROM Size (outpw ile yazılıyor, config üzerine)
- Byte 12-15: DataFlash Addr (outpw ile yazılıyor)
- Byte 16-31: Config verileri (ReadData ile doldurulmuş)

### Sorun 2: Devam Paketlerinde Veri Konumu

Devam paketleri için:
- Byte 0-3: CMD
- pu8Src += 8 yapılıyor
- Byte 8-63: Veri (56 byte)

**DOĞRU!**

### Sorun 3: İlk Pakette Veri Konumu

İlk paket için:
- Byte 0-3: CMD
- pu8Src += 8
- Byte 8-11: Address
- Byte 12-15: TotalLen
- pu8Src += 8
- Byte 16-63: Veri (48 byte)

**DOĞRU!**

## 🎯 ASIL SORUN

Yanıt paketlerini yanlış parse ediyoruz! Garip değerler bunun göstergesi.

Ayrıca:
- Firmware yazılıyor mu kontrol edilmeli
- CMD_RUN_APROM çalışıyor mu kontrol edilmeli
- Reset sonrası firmware çalışıyor mu kontrol edilmeli

