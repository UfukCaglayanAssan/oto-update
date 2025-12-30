# Paket Format Kontrolü

## ISP_UART Kodundan Çıkarılan Format

### İlk Paket (CMD_UPDATE_APROM):
```
Byte 0-3:   CMD_UPDATE_APROM (0x000000A0)
Byte 4-7:   (pu8Src += 8 yapılıyor, yani atlanıyor)
Byte 8-11:  u32StartAddress (inpw(pu8Src))
Byte 12-15: u32TotalLen (inpw(pu8Src + 4))
Byte 16-63: Veri (48 byte) - pu8Src += 8 sonrası
```

### Devam Paketleri:
```
Byte 0-3:   CMD_UPDATE_APROM (0x000000A0)
Byte 4-7:   (pu8Src += 8 yapılıyor, yani atlanıyor)
Byte 8-63:  Veri (56 byte) - pu8Src += 8 sonrası
```

## Kod Analizi

```c
u32Lcmd = inpw(pu8Src);  // Byte 0-3: Komut okunur
outpw(pu8Response + 4, 0);
pu8Src += 8;  // İlk 8 byte atlanır!
u32srclen -= 8;

// CMD_UPDATE_APROM kontrolü:
u32StartAddress = inpw(pu8Src);      // Byte 8-11
u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15
pu8Src += 8;                         // Byte 16'ya geçilir
u32srclen -= 8;                      // 8 byte daha azalır

// Veri yazma:
WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
// pu8Src artık Byte 16'da, yani Byte 16-63 arası veri (48 byte)
```

## Sonuç

- İlk paket: Byte 16-63'e 48 byte veri
- Devam paketleri: Byte 8-63'e 56 byte veri

