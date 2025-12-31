# Paket Format Analizi - ISP_UART vs Önerilen Format

## 🔍 ISP_UART Kod Analizi

### Mevcut Kod (isp_user.c):

```c
// Satır 43-46
u32Lcmd = inpw(pu8Src);        // Byte 0-3: CMD
outpw(pu8Response + 4, 0);
pu8Src += 8;                    // İlk 8 byte atlanıyor!
u32srclen -= 8;

// Satır 106-107 (İlk paket için)
u32StartAddress = inpw(pu8Src);      // Byte 8-11: Address
u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15: Size

// Satır 112
pu8Src += 8;                    // Tekrar 8 byte atlanıyor
u32srclen -= 8;

// Satır 153 (Devam paketleri için)
WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
// pu8Src artık Byte 8'den başlıyor
```

### Mevcut Format (Şu anki Python kodu):

**İlk paket:**
- Byte 0-3: CMD
- Byte 4-7: (atlanıyor - bootloader kullanmıyor)
- Byte 8-11: Address
- Byte 12-15: Size
- Byte 16-63: Data (48 byte)

**Devam paketleri:**
- Byte 0-3: CMD
- Byte 4-7: (atlanıyor - bootloader kullanmıyor)
- Byte 8-63: Data (56 byte)

## 📋 Önerilen Format (Kullanıcı):

**İlk paket:**
- Byte 0-3: CMD
- Byte 4-7: **packno** (YENİ!)
- Byte 8-11: Address
- Byte 12-15: Size
- Byte 16-63: Data (48 byte)

**Devam paketleri:**
- Byte 0-3: CMD
- Byte 4-7: **packno** (YENİ!)
- Byte 8-63: Data (56 byte)

## ❓ Soru: Önerilen Format Doğru mu?

### ISP_UART Kodunda:
- **Byte 4-7 payload'dan OKUNMUYOR!**
- `pu8Src += 8` ile atlanıyor
- Paket numarası sadece **response'da** gönderiliyor (satır 164)

### Ama:
- Bazı Nuvoton ISP implementasyonlarında paket numarası payload'da olabilir
- Belki bu bootloader'ın özel bir versiyonu?
- Ya da kullanıcı farklı bir bootloader kullanıyor?

## 🔧 Sonuç:

**Mevcut ISP_UART kodu:**
- ❌ Paket numarası payload'da YOK
- ✅ Byte 4-7 atlanıyor
- ✅ Paket numarası sadece response'da

**Önerilen format:**
- ✅ Paket numarası payload'da VAR
- ❓ Ama ISP_UART kodu bunu okumuyor!

## 💡 Öneri:

1. **Test et:** Önerilen formatı dene, çalışıyorsa bootloader farklı bir versiyon olabilir
2. **Kontrol et:** Bootloader versiyonunu kontrol et (CMD_GET_FWVER)
3. **İki formatı destekle:** Hem mevcut hem önerilen formatı destekleyen kod yaz

