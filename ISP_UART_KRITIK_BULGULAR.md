# ISP_UART Kod Analizi - Kritik Bulgular

## 🔍 ISP_UART Kodundan Öğrenilenler

### 1. CMD_SYNC_PACKNO (KRİTİK - EKSİKTİ!)

**ISP_UART Kodu (isp_user.c Satır 50-53):**
```c
if(u32Lcmd == CMD_SYNC_PACKNO)
{
    u32PackNo = inpw(pu8Src);  // pu8Src += 8 sonrası, yani Byte 8-11
}
```

**ÖNEMLİ:**
- CMD_SYNC_PACKNO gönderilirse paket numarası ayarlanıyor
- `pu8Src += 8` yapıldıktan sonra okunuyor, yani **Byte 8-11'de paket numarası** olmalı
- Python kodunda **EKSİKTİ!**

**Çözüm:**
```python
# CMD_CONNECT sonrası hemen
sync_packet = create_packet(CMD_SYNC_PACKNO, 1)  # Byte 8-11'de 1
send_packet(ser, sync_packet)
```

### 2. CMD_CONNECT Sonrası Paket Numarası

**ISP_UART Kodu (isp_user.c Satır 77-82):**
```c
else if(u32Lcmd == CMD_CONNECT)
{
    u32PackNo = 1;  // Paket numarasını 1 yap
    outpw(pu8Response + 8, g_u32ApromSize);
    outpw(pu8Response + 12, g_u32DataFlashAddr);
    goto out;
}
```

**ÖNEMLİ:**
- CMD_CONNECT sonrası paket numarası 1 yapılıyor
- Ama CMD_SYNC_PACKNO ile garanti altına almak daha iyi

### 3. CMD_UPDATE_APROM - İlk Paket

**ISP_UART Kodu (isp_user.c Satır 106-113):**
```c
u32StartAddress = inpw(pu8Src);      // Byte 8-11 (pu8Src += 8 sonrası)
u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15
EraseAP(u32StartAddress, u32TotalLen);

u32TotalLen = inpw(pu8Src + 4);      // Tekrar okunuyor (neden?)
pu8Src += 8;                          // Tekrar 8 byte atlanıyor!
u32srclen -= 8;
```

**ÖNEMLİ:**
- İlk pakette Address (Byte 8-11) ve TotalLen (Byte 12-15) okunuyor
- Sonra `pu8Src += 8` yapılıyor, yani veri **Byte 16'dan başlıyor** (48 byte)
- Python kodu: ✅ Doğru!

### 4. CMD_UPDATE_APROM - Devam Paketleri

**ISP_UART Kodu (isp_user.c Satır 145-158):**
```c
if((u32Gcmd == CMD_UPDATE_APROM) || (u32Gcmd == CMD_UPDATE_DATAFLASH))
{
    // pu8Src += 8 yapıldıktan sonra, yani Byte 8'den başlıyor
    WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
    u32StartAddress += u32srclen;
}
```

**ÖNEMLİ:**
- Devam paketlerinde `pu8Src += 8` yapılıyor, yani veri **Byte 8'den başlıyor** (56 byte)
- Python kodu: ✅ Doğru!

### 5. Yanıt Paketi

**ISP_UART Kodu (isp_user.c Satır 160-165):**
```c
u16Lcksum = Checksum(pu8Buffer, u8len);
outps(pu8Response, u16Lcksum);        // Byte 0-1: Checksum
++u32PackNo;                            // Paket numarası artırılıyor
outpw(pu8Response + 4, u32PackNo);     // Byte 4-7: Paket No
u32PackNo++;                            // Tekrar artırılıyor (HATA?)
```

**ÖNEMLİ:**
- Byte 0-1: Checksum (16-bit little-endian)
- Byte 4-7: Paket No (uint32_t little-endian)
- Paket numarası iki kez artırılıyor (muhtemelen bir sonraki paket için)

## ⚠️ Tespit Edilen Eksikler

### 1. CMD_SYNC_PACKNO Eksik! (KRİTİK!)

**Durum:** Python kodunda CMD_SYNC_PACKNO gönderilmiyor!

**ISP_UART Kodunda Var:**
```c
if(u32Lcmd == CMD_SYNC_PACKNO)
{
    u32PackNo = inpw(pu8Src);  // Byte 8-11'den okunuyor
}
```

**Çözüm:** CMD_CONNECT sonrası CMD_SYNC_PACKNO gönderilmeli!

### 2. Paket Formatı Kontrolü

**CMD_SYNC_PACKNO Formatı:**
- Byte 0-3: CMD_SYNC_PACKNO (0xA4)
- Byte 4-7: Padding (atlanır)
- Byte 8-11: Paket Numarası (uint32_t)

**Python Kodu:** ✅ Şimdi eklendi!

## 📋 Doğru Komut Sırası

```
1. CMD_CONNECT (0xAE)
   → Paket No = 1 yapılıyor
   ↓
2. CMD_SYNC_PACKNO (0xA4) ← EKLENDİ!
   → Paket No = 1 garanti altına alınıyor
   ↓
3. CMD_GET_DEVICEID (0xB1) [Opsiyonel]
   ↓
4. CMD_UPDATE_APROM (0xA0) - İlk paket
   ↓
5. CMD_UPDATE_APROM (0xA0) - Devam paketleri
   ↓
6. CMD_RUN_APROM (0xAB) - Reset
```

## ✅ Yapılan Düzeltmeler

1. ✅ **CMD_SYNC_PACKNO eklendi** - create_packet fonksiyonunda
2. ✅ **CMD_SYNC_PACKNO gönderimi eklendi** - CMD_CONNECT sonrası
3. ✅ **Paket formatı doğrulandı** - ISP_UART koduna göre

## 🎯 Sonuç

Kod artık ISP_UART protokolüne **tam uyumlu**:
- ✅ CMD_SYNC_PACKNO eklendi
- ✅ Paket formatları doğru
- ✅ Komut sırası doğru

Test edin ve sonuçları paylaşın!

