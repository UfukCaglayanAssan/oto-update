# Başlangıç Adresi Belirleme - ISP_UART Kod Analizi

## 📋 ISP_UART Kodunda Başlangıç Adresi Nasıl Belirleniyor?

### 1. ParseCmd Fonksiyonu (isp_user.c Satır 31-116)

```c
int ParseCmd(uint8_t *pu8Buffer, uint8_t u8len)
{
    // ...
    pu8Src = pu8Buffer;  // Gelen paketin başlangıcı
    u32Lcmd = inpw(pu8Src);        // Byte 0-3: Komut (CMD_UPDATE_APROM)
    outpw(pu8Response + 4, 0);
    pu8Src += 8;                    // ⚠️ İLK 8 BYTE ATLANIYOR!
    u32srclen -= 8;
    
    // ...
    
    if((u32Lcmd == CMD_UPDATE_APROM) || (u32Lcmd == CMD_UPDATE_DATAFLASH))
    {
        if(u32Lcmd == CMD_UPDATE_DATAFLASH)
        {
            u32StartAddress = g_u32DataFlashAddr;  // DataFlash için sabit adres
        }
        else  // CMD_UPDATE_APROM
        {
            u32StartAddress = inpw(pu8Src);        // ⚠️ Byte 8-11'den okunuyor!
            u32TotalLen = inpw(pu8Src + 4);        // ⚠️ Byte 12-15'ten okunuyor!
            EraseAP(u32StartAddress, u32TotalLen);
        }
        
        u32TotalLen = inpw(pu8Src + 4);            // Tekrar okunuyor (Byte 12-15)
        pu8Src += 8;                                // Byte 16'ya geçiliyor
        u32srclen -= 8;
        // ...
    }
}
```

### 2. Paket Formatı (ISP_UART Beklentisi)

**CMD_UPDATE_APROM İlk Paket:**
```
Byte 0-3:   CMD_UPDATE_APROM (0x000000A0)
Byte 4-7:   ATLANIYOR (pu8Src += 8 sonrası)
Byte 8-11:  Başlangıç Adresi (u32StartAddress) ← BURADAN OKUNUYOR!
Byte 12-15: Toplam Boyut (u32TotalLen) ← BURADAN OKUNUYOR!
Byte 16-63: Veri (48 byte)
```

**ÖNEMLİ:** 
- `pu8Src += 8;` → İlk 8 byte atlanıyor
- `u32StartAddress = inpw(pu8Src);` → Byte 8-11'den okunuyor
- `u32TotalLen = inpw(pu8Src + 4);` → Byte 12-15'ten okunuyor

---

## 🔍 Python Script'te Başlangıç Adresi Nasıl Gönderiliyor?

### 1. pkt_update_first Fonksiyonu (uart_receiver_nuvoton.py Satır 174-196)

```python
def pkt_update_first(addr, size, data, packno):
    """İlk CMD_UPDATE_APROM paketi
    
    Format:
    - Byte 0-3: CMD_UPDATE_APROM
    - Byte 4-7: packno (kullanıcı önerisi, ama ISP_UART kodunda atlanıyor)
    - Byte 8-11: addr ← BAŞLANGIÇ ADRESİ BURADA!
    - Byte 12-15: size ← TOPLAM BOYUT BURADA!
    - Byte 16-63: data (48 byte)
    """
    p = bytearray(64)
    p[0:4] = uint32_to_bytes(CMD_UPDATE_APROM)
    p[4:8] = uint32_to_bytes(packno)      # Byte 4-7: packno (atlanıyor)
    p[8:12] = uint32_to_bytes(addr)       # Byte 8-11: BAŞLANGIÇ ADRESİ ✅
    p[12:16] = uint32_to_bytes(size)      # Byte 12-15: TOPLAM BOYUT ✅
    if data:
        data_len = min(len(data), 48)
        p[16:16+data_len] = data[:data_len]  # Byte 16-63: Veri
    return p
```

### 2. send_update_aprom Fonksiyonu (uart_receiver_nuvoton.py Satır 592-596)

```python
def send_update_aprom(ser, bin_data, start_address=0x00000000, erase_before_update=True):
    # ...
    # İlk paket: CMD_UPDATE_APROM + adres + boyut
    print(f"\n[1/3] CMD_UPDATE_APROM (baslangic) gonderiliyor...")
    first_data = bin_data[:48] if len(bin_data) >= 48 else bin_data
    packno = 1
    first_packet = pkt_update_first(start_address, total_size, first_data, packno)
    #                                 ^^^^^^^^^^^^^^ ← BAŞLANGIÇ ADRESİ BURADAN GELİYOR!
```

**Varsayılan:** `start_address=0x00000000` (APROM başlangıç adresi)

---

## ✅ UYUMLULUK KONTROLÜ

### ISP_UART Kodu vs Python Script

| Özellik | ISP_UART Kodu | Python Script | Durum |
|---------|---------------|---------------|-------|
| **Komut Konumu** | Byte 0-3 | Byte 0-3 | ✅ UYUMLU |
| **Atlanan Byte** | Byte 4-7 (pu8Src += 8) | Byte 4-7 (packno) | ✅ UYUMLU |
| **Başlangıç Adresi** | Byte 8-11 (inpw(pu8Src)) | Byte 8-11 (uint32_to_bytes(addr)) | ✅ UYUMLU |
| **Toplam Boyut** | Byte 12-15 (inpw(pu8Src + 4)) | Byte 12-15 (uint32_to_bytes(size)) | ✅ UYUMLU |
| **Veri** | Byte 16-63 (48 byte) | Byte 16-63 (48 byte) | ✅ UYUMLU |

### Paket Yapısı Karşılaştırması

**ISP_UART Beklentisi:**
```
[0-3]   CMD_UPDATE_APROM
[4-7]   (atlanıyor)
[8-11]  Başlangıç Adresi ← OKUNUYOR
[12-15] Toplam Boyut ← OKUNUYOR
[16-63] Veri (48 byte)
```

**Python Script Gönderimi:**
```
[0-3]   CMD_UPDATE_APROM
[4-7]   packno (atlanıyor)
[8-11]  start_address ← GÖNDERİLİYOR ✅
[12-15] total_size ← GÖNDERİLİYOR ✅
[16-63] data (48 byte) ← GÖNDERİLİYOR ✅
```

**SONUÇ:** ✅ **TAM UYUMLU!**

---

## 📊 Örnek Paket Analizi

### Python Script'ten Gönderilen İlk Paket

**Başlangıç Adresi:** `0x00000000` (APROM başlangıç)
**Toplam Boyut:** `7128` byte (0x00001BD8)

**Paket İçeriği (ilk 16 byte):**
```
Byte 0-3:   A0 00 00 00  (CMD_UPDATE_APROM)
Byte 4-7:   01 00 00 00  (packno = 1, atlanıyor)
Byte 8-11:  00 00 00 00  (start_address = 0x00000000) ✅
Byte 12-15: D8 1B 00 00  (total_size = 0x00001BD8 = 7128) ✅
```

**ISP_UART Kodu Okuma:**
```c
pu8Src += 8;                    // Byte 8'a geç
u32StartAddress = inpw(pu8Src); // Byte 8-11: 0x00000000 ✅
u32TotalLen = inpw(pu8Src + 4); // Byte 12-15: 0x00001BD8 ✅
```

**Doğrulama:** ✅ **DOĞRU!**

---

## 🎯 Sonuç

### ✅ Başlangıç Adresi Doğru Belirleniyor!

1. **Python Script:** Başlangıç adresi `start_address=0x00000000` olarak gönderiliyor
2. **Paket Formatı:** Byte 8-11'de gönderiliyor (ISP_UART koduna uygun)
3. **ISP_UART Kodu:** Byte 8-11'den okuyor (`pu8Src += 8` sonrası)
4. **Uyumluluk:** ✅ Tam uyumlu!

### 📝 Notlar

- **Varsayılan Adres:** `0x00000000` (APROM başlangıç adresi)
- **Değiştirilebilir:** `send_update_aprom(ser, bin_data, start_address=0x00001000)` şeklinde değiştirilebilir
- **DataFlash:** `CMD_UPDATE_DATAFLASH` için adres otomatik olarak `g_u32DataFlashAddr` kullanılıyor

### 🔧 Kullanım

```python
# Varsayılan (APROM başlangıç: 0x00000000)
send_update_aprom(ser, bin_data)

# Özel adres
send_update_aprom(ser, bin_data, start_address=0x00001000)
```

**Her şey doğru çalışıyor!** ✅


