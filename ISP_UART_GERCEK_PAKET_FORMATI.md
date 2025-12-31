# ISP_UART Gerçek Paket Formatı - Detaylı Analiz

## 🔍 ParseCmd Fonksiyonu Analizi (isp_user.c)

### 1. Paket Okuma Akışı:

```c
// Satır 41-46
pu8Src = pu8Buffer;              // Buffer başlangıcı
u32srclen = u8len;               // 64 byte
u32Lcmd = inpw(pu8Src);          // Byte 0-3: CMD okunuyor
outpw(pu8Response + 4, 0);       // Response Byte 4-7: 0 yazılıyor
pu8Src += 8;                     // ⚠️ İLK 8 BYTE ATLANIYOR! (Byte 0-7)
u32srclen -= 8;                  // Kalan: 56 byte
```

**SONUÇ:** Byte 4-7 **ATLANIYOR**, payload'dan okunmuyor!

### 2. CMD_UPDATE_APROM İlk Paket (Satır 104-115):

```c
if((u32Lcmd == CMD_UPDATE_APROM) || (u32Lcmd == CMD_UPDATE_DATAFLASH))
{
    else  // CMD_UPDATE_APROM için
    {
        u32StartAddress = inpw(pu8Src);      // Byte 8-11: Address
        u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15: Size
        EraseAP(u32StartAddress, u32TotalLen);
    }

    u32TotalLen = inpw(pu8Src + 4);          // Byte 12-15: Size (tekrar okunuyor)
    pu8Src += 8;                             // ⚠️ TEKRAR 8 BYTE ATLANIYOR! (Byte 8-15)
    u32srclen -= 8;                          // Kalan: 48 byte
}
```

**SONUÇ:** 
- Byte 8-11: Address
- Byte 12-15: Size
- Byte 16-63: Data (48 byte) - pu8Src artık Byte 16'da

### 3. Devam Paketleri (Satır 145-158):

```c
if((u32Gcmd == CMD_UPDATE_APROM) || (u32Gcmd == CMD_UPDATE_DATAFLASH))
{
    // pu8Src zaten Byte 8'de (ilk paket sonrası)
    // Devam paketlerinde pu8Src direkt Byte 8'den başlıyor
    WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
    // pu8Src: Byte 8-63 (56 byte data)
}
```

**SONUÇ:**
- Byte 0-3: CMD
- Byte 4-7: **ATLANIYOR** (pu8Src += 8 ile)
- Byte 8-63: Data (56 byte)

### 4. Paket Numarası (Satır 50-53, 163-165):

```c
// Sadece CMD_SYNC_PACKNO'da okunuyor:
if(u32Lcmd == CMD_SYNC_PACKNO)
{
    u32PackNo = inpw(pu8Src);  // Byte 8-11'den okunuyor (pu8Src += 8 sonrası)
}

// Response'da yazılıyor:
++u32PackNo;
outpw(pu8Response + 4, u32PackNo);  // Response Byte 4-7'ye yazılıyor
u32PackNo++;
```

**SONUÇ:**
- **Gelen paketlerde paket numarası YOK!**
- Paket numarası sadece **response'da** (Byte 4-7)
- Sadece `CMD_SYNC_PACKNO` komutunda Byte 8-11'den okunuyor

## 📋 GERÇEK PAKET FORMATI

### İlk Paket (CMD_UPDATE_APROM):
```
Byte 0-3:   CMD (0x000000A0)
Byte 4-7:   IGNORE (atlanıyor, pu8Src += 8)
Byte 8-11:  Address (0x00000000)
Byte 12-15: TotalLen (7128)
Byte 16-63: Data (48 byte)
```

### Devam Paketleri:
```
Byte 0-3:   CMD (0x000000A0)
Byte 4-7:   IGNORE (atlanıyor, pu8Src += 8)
Byte 8-63:  Data (56 byte)
```

### Response Formatı:
```
Byte 0-1:   Checksum (16-bit)
Byte 2-3:   (reserved)
Byte 4-7:   Packet Number (32-bit, bootloader kendi sayıyor)
Byte 8-63:  Response data
```

## ❌ Kullanıcının Önerdiği Format:

```
Byte 0-3:   CMD
Byte 4-7:   packno  ← ⚠️ BU YOK! Byte 4-7 atlanıyor!
Byte 8-11:  addr
Byte 12-15: size
Byte 16-63: data
```

## ✅ SONUÇ:

**ISP_UART kodunda:**
- ❌ Paket numarası payload'da YOK
- ✅ Byte 4-7 atlanıyor (pu8Src += 8)
- ✅ Paket numarası sadece response'da

**Kullanıcının önerdiği format:**
- ✅ Paket numarası Byte 4-7'de
- ❌ Ama ISP_UART kodu bunu okumuyor!

**İki olasılık:**
1. Bootloader farklı bir versiyon (paket numarasını okuyor)
2. Ya da önerilen format yanlış

**Test edilmeli:** Önerilen formatı test et, çalışmıyorsa eski formata dön.

