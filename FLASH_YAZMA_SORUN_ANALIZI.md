# Flash Yazma Sorunu - Detaylı Analiz

## 🔴 SORUN: Flash'a Veri Yazılmıyor!

Kullanıcı raporu: "hiçbir değişiklik yok kartta. hem silinmemiş hem yazılmamış"

## 🔍 ISP_UART KOD ANALİZİ

### 1. Flash Yazma İşlemi Nerede Yapılıyor?

#### isp_user.c (Satır 145-158):
```c
if((u32Gcmd == CMD_UPDATE_APROM) || (u32Gcmd == CMD_UPDATE_DATAFLASH))
{
    if(u32TotalLen < u32srclen)
    {
        u32srclen = u32TotalLen; /* prevent last package from over writing */
    }

    u32TotalLen -= u32srclen;
    WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src); 
    memset(pu8Src, 0, u32srclen);
    ReadData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
    u32StartAddress += u32srclen;
    u32LastDataLen = u32srclen;
}
```

**KRİTİK:** `u32Gcmd` static değişkeni kullanılıyor!

#### isp_user.c (Satır 55-58):
```c
if((u32Lcmd) && (u32Lcmd != CMD_RESEND_PACKET))
{
    u32Gcmd = u32Lcmd;  // u32Gcmd static değişkeni!
}
```

**SORUN:** `u32Gcmd` sadece ilk pakette ayarlanıyor!

### 2. İlk Paket İşleme (Satır 89-116):
```c
if((u32Lcmd == CMD_UPDATE_APROM) || (u32Lcmd == CMD_UPDATE_DATAFLASH))
{
    if(u32Lcmd == CMD_UPDATE_DATAFLASH)
    {
        u32StartAddress = g_u32DataFlashAddr;
        if(g_u32DataFlashSize)    
        {
            EraseAP(g_u32DataFlashAddr, g_u32DataFlashSize);
        }
        else
        {
            goto out;  // ERKEN ÇIKIŞ!
        }
    }
    else
    {
        u32StartAddress = inpw(pu8Src);      // Byte 8-11: Address
        u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15: TotalLen
        EraseAP(u32StartAddress, u32TotalLen);  // FLASH SİLME
    }

    u32TotalLen = inpw(pu8Src + 4);  // TEKRAR OKUNUYOR!
    pu8Src += 8;
    u32srclen -= 8;
    u32StartAddress_bak = u32StartAddress;
    u32TotalLen_bak = u32TotalLen;
}
```

**ÖNEMLİ:** İlk pakette `EraseAP()` çağrılıyor ve `u32Gcmd` ayarlanıyor.

### 3. Devam Paketleri İşleme (Satır 145-158):
```c
if((u32Gcmd == CMD_UPDATE_APROM) || (u32Gcmd == CMD_UPDATE_DATAFLASH))
{
    // WriteData() çağrılıyor
    WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
}
```

**SORUN:** Devam paketlerinde `u32Lcmd` kontrol edilmiyor, sadece `u32Gcmd` kontrol ediliyor!

### 4. WriteData() Fonksiyonu (fmc_user.c):
```c
void WriteData(unsigned int addr_start, unsigned int addr_end, unsigned int *data)
{
    FMC_Proc(FMC_ISPCMD_PROGRAM, addr_start, addr_end, data);
    return;
}
```

### 5. FMC_Proc() Fonksiyonu (fmc_user.c):
```c
int FMC_Proc(unsigned int u32Cmd, unsigned int addr_start, unsigned int addr_end, unsigned int *data)
{
    for (u32Addr = addr_start; u32Addr < addr_end; data++) {
        FMC->ISPCMD = u32Cmd;
        FMC->ISPADDR = u32Addr;
        
        if (u32Cmd == FMC_ISPCMD_PROGRAM) {
            FMC->ISPDAT = *data;  // 32-bit word yazıyor!
        }
        
        FMC->ISPTRG = 0x1;
        __ISB();
        
        // Wait ISP cmd complete
        u32TimeOutCnt = FMC_TIMEOUT_WRITE;
        while (FMC->ISPTRG) {
            if(--u32TimeOutCnt == 0)
                return -1;  // HATA!
        }
        
        // Hata kontrolü
        Reg = FMC->ISPCTL;
        if (Reg & FMC_ISPCTL_ISPFF_Msk) {
            FMC->ISPCTL = Reg;
            return -1;  // HATA!
        }
        
        u32Addr += 4;  // Her 4 byte (word) için bir işlem
    }
    return 0;
}
```

**KRİTİK:** FMC her 4 byte (32-bit word) için bir işlem yapıyor!

## 🚨 TESPİT EDİLEN SORUNLAR

### Sorun 1: Veri Hizalaması
- FMC 32-bit word yazıyor (4 byte)
- Veri 4 byte'a hizalanmış olmalı
- `(unsigned int *)pu8Src` cast ediliyor - bu doğru mu?

### Sorun 2: u32Gcmd Kontrolü
- İlk pakette `u32Gcmd = u32Lcmd` yapılıyor
- Devam paketlerinde sadece `u32Gcmd` kontrol ediliyor
- Eğer ilk paket yanlış parse edilirse, `u32Gcmd` yanlış olabilir

### Sorun 3: EraseAP() Hata Kontrolü
- `EraseAP()` hata döndürüyorsa, yazma yapılmıyor olabilir
- Ama kod `EraseAP()` sonrası hata kontrolü yapmıyor!

### Sorun 4: WriteData() Hata Kontrolü
- `WriteData()` hata döndürüyorsa, yazma başarısız olabilir
- Ama kod `WriteData()` sonrası hata kontrolü yapmıyor!

## 🔧 OLASI ÇÖZÜMLER

### 1. Veri Hizalaması Kontrolü
- Veri 4 byte'a hizalanmış olmalı
- `pu8Src` adresi 4 byte'a hizalanmış olmalı

### 2. u32Gcmd Kontrolü
- İlk pakette `u32Gcmd` doğru ayarlanıyor mu?
- Devam paketlerinde `u32Gcmd` doğru mu?

### 3. Hata Kontrolü
- `EraseAP()` ve `WriteData()` hata döndürüyor mu?
- Bootloader hata mesajı gönderiyor mu?

### 4. Paket Formatı Kontrolü
- İlk paket formatı doğru mu?
- Devam paketleri formatı doğru mu?
- Veri doğru yere mi yazılıyor?

## 📊 KONTROL EDİLMESİ GEREKENLER

1. **İlk Paket Formatı:**
   - Byte 0-3: CMD_UPDATE_APROM (0x000000A0) ✓
   - Byte 4-7: (atlanıyor) ✓
   - Byte 8-11: Address (0x00000000) ✓
   - Byte 12-15: TotalLen (7128) ✓
   - Byte 16-63: Data (48 byte) ✓

2. **Devam Paketleri Formatı:**
   - Byte 0-3: CMD_UPDATE_APROM (0x000000A0) ✓
   - Byte 4-7: (atlanıyor) ✓
   - Byte 8-63: Data (56 byte) ✓

3. **WriteData() Parametreleri:**
   - `u32StartAddress`: 0x00000000 (doğru)
   - `u32StartAddress + u32srclen`: 0x00000038 (48 byte) -> 0x00000070 (56 byte)
   - `pu8Src`: Byte 16'dan başlıyor (ilk paket), Byte 8'den başlıyor (devam paketleri)

4. **FMC_Proc() Çağrısı:**
   - `addr_start`: 0x00000000
   - `addr_end`: 0x00000038 (ilk paket), 0x00000070 (devam paketleri)
   - `data`: `(unsigned int *)pu8Src` - 32-bit word pointer

## 🎯 SONUÇ

Flash yazma işlemi `WriteData()` fonksiyonu ile yapılıyor, ama:
1. Veri hizalaması sorunu olabilir
2. `u32Gcmd` yanlış ayarlanmış olabilir
3. Hata kontrolü yapılmıyor
4. Paket formatı yanlış olabilir

**Kontrol edilmesi gerekenler:**
- İlk paket doğru parse ediliyor mu?
- `u32Gcmd` doğru ayarlanıyor mu?
- `WriteData()` başarılı mı?
- Veri doğru adrese yazılıyor mu?

