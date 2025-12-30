# ISP_UART Klasörü - Detaylı Kod Analizi ve Sorun Tespiti

## 📋 Dosya Yapısı

```
ISP_UART/
├── main.c              # Ana program, bootloader akışı
├── isp_user.c          # ISP komutları ve paket işleme
├── isp_user.h          # ISP komut tanımları
├── uart_transfer.c     # UART haberleşme ve interrupt handler
├── uart_transfer.h     # UART tanımları
├── fmc_user.c          # Flash Memory Controller işlemleri
├── fmc_user.h          # FMC tanımları
└── targetdev.h         # Target device tanımları
```

---

## 🔍 ADIM 1: main.c - Bootloader Başlangıç Akışı

### Sistem Başlatma (Satır 24-73)

1. **Clock Ayarları:**
   - HIRC (High-speed Internal RC) aktif ediliyor
   - PLL 128MHz'e ayarlanıyor
   - SystemCoreClock = 64MHz (PLL/2)
   - UART0 clock HIRC'den alınıyor

2. **UART Pin Ayarları:**
   - UART0_RXD: PB12
   - UART0_TXD: PB13

3. **UART Başlatma:**
   - `UART_Init()` çağrılıyor (uart_transfer.c)

### Ana Akış (Satır 78-156)

```c
int32_t main(void)
{
    // 1. Sistem başlatma
    SYS_UnlockReg();
    SYS_Init();
    UART_Init();
    
    // 2. ISP modunu aktif et
    CLK->AHBCLK |= CLK_AHBCLK_ISPCKEN_Msk;
    FMC->ISPCTL |= FMC_ISPCTL_ISPEN_Msk;
    
    // 3. APROM boyutunu al
    g_u32ApromSize = BL_EnableFMC();
    g_u32DataFlashAddr = SCU->FNSADDR;
    
    // 4. 300ms timeout ayarla
    SysTick->LOAD = 300000 * CyclesPerUs;  // 300ms
    SysTick->VAL = 0;
    SysTick->CTRL = ... | SysTick_CTRL_ENABLE_Msk;
    
    // 5. CMD_CONNECT bekle (300ms içinde)
    while (1)
    {
        if ((g_u8bufhead >= 4) || (g_u8bUartDataReady == TRUE))
        {
            uint32_t u32lcmd = inpw(g_au8uart_rcvbuf);
            
            if (u32lcmd == CMD_CONNECT)  // 0x000000AE
            {
                goto _ISP;  // ISP moduna geç
            }
            else
            {
                // Yanlış komut, buffer'ı temizle
                g_u8bUartDataReady = FALSE;
                g_u8bufhead = 0;
            }
        }
        
        // Timeout kontrolü
        if (SysTick->CTRL & SysTick_CTRL_COUNTFLAG_Msk)
        {
            goto _APROM;  // APROM'a geç
        }
    }
    
_ISP:
    // ISP modu: Komutları parse et ve yanıt gönder
    while (1)
    {
        if (g_u8bUartDataReady == TRUE)
        {
            g_u8bUartDataReady = FALSE;
            ParseCmd(g_au8uart_rcvbuf, 64);  // 64 byte paket parse et
            PutString();                      // 64 byte yanıt gönder
        }
    }
    
_APROM:
    // APROM'a geç ve reset at
    FMC_SetVectorPageAddr(FMC_APROM_BASE);
    NVIC_SystemReset();
    while(1);
}
```

**🔴 KRİTİK NOKTA 1:** Bootloader sadece **300ms** içinde CMD_CONNECT bekliyor!

---

## 🔍 ADIM 2: uart_transfer.c - UART Haberleşme

### UART Interrupt Handler (Satır 27-52)

```c
void UART0_IRQHandler(void)
{
    uint32_t u32IntSrc = UART0->INTSTS;
    
    // RDA (Receive Data Available) veya RXTO (RX Timeout) interrupt
    if (u32IntSrc & (UART_INTSTS_RXTOIF_Msk | UART_INTSTS_RDAIF_Msk))
    {
        // RX FIFO boşalana kadar oku
        while (((UART0->FIFOSTS & UART_FIFOSTS_RXEMPTY_Msk) == 0) && 
               (g_u8bufhead < MAX_PKT_SIZE))
        {
            g_au8uart_rcvbuf[g_u8bufhead++] = UART0->DAT;
        }
    }
    
    // Tam 64 byte alındıysa
    if (g_u8bufhead == MAX_PKT_SIZE)
    {
        g_u8bUartDataReady = TRUE;  // Paket hazır!
        g_u8bufhead = 0;
    }
    else if (u32IntSrc & UART_INTSTS_RXTOIF_Msk)
    {
        // Timeout oldu, buffer'ı sıfırla
        g_u8bufhead = 0;
    }
}
```

**🔴 KRİTİK NOKTA 2:** Bootloader **tam 64 byte** bekliyor! Eksik veya fazla byte gelirse paket işlenmiyor!

### UART Başlatma (Satır 70-90)

```c
void UART_Init()
{
    UART0->FUNCSEL = UART_FUNCSEL_UART;
    UART0->LINE = UART_WORD_LEN_8 | UART_PARITY_NONE | UART_STOP_BIT_1;
    UART0->FIFO = UART_FIFO_RFITL_14BYTES | UART_FIFO_RTSTRGLV_14BYTES;
    UART0->BAUD = (UART_BAUD_MODE2 | UART_BAUD_MODE2_DIVIDER(__HIRC, 115200));
    UART0->TOUT = (UART0->TOUT & ~UART_TOUT_TOIC_Msk) | (0x40);  // Timeout ayarı
    NVIC_SetPriority(UART0_IRQn, 2);
    NVIC_EnableIRQ(UART0_IRQn);
    UART0->INTEN = (UART_INTEN_TOCNTEN_Msk | UART_INTEN_RXTOIEN_Msk | UART_INTEN_RDAIEN_Msk);
}
```

**Baud Rate:** 115200
**Data Format:** 8N1 (8 bit, No parity, 1 stop bit)
**FIFO Trigger:** 14 byte

### Yanıt Gönderme (Satır 55-68)

```c
void PutString(void)
{
    uint32_t i;
    
    // 64 byte yanıt gönder
    for (i = 0; i < MAX_PKT_SIZE; i++)
    {
        // TX FIFO dolu mu bekle
        while ((UART0->FIFOSTS & UART_FIFOSTS_TXFULL_Msk));
        
        // Byte gönder
        UART0->DAT = g_au8ResponseBuff[i];
    }
}
```

**🔴 KRİTİK NOKTA 3:** Yanıt **her zaman 64 byte** gönderiliyor!

---

## 🔍 ADIM 3: isp_user.c - Komut İşleme

### ParseCmd Fonksiyonu - Genel Yapı

```c
int ParseCmd(uint8_t *pu8Buffer, uint8_t u8len)
{
    static uint32_t u32PackNo = 1;  // Paket numarası (static!)
    uint8_t *pu8Response = g_au8ResponseBuff;
    uint8_t *pu8Src = pu8Buffer;
    uint32_t u32srclen = u8len;  // 64
    
    // 1. Komutu oku (Byte 0-3)
    u32Lcmd = inpw(pu8Src);  // pu8Src[0-3] -> uint32_t (little-endian)
    
    // 2. Yanıt buffer'ını hazırla
    outpw(pu8Response + 4, 0);  // Byte 4-7: 0 yaz
    
    // 3. İlk 8 byte'ı atla!
    pu8Src += 8;
    u32srclen -= 8;  // 64 - 8 = 56
    
    // 4. Config verilerini oku (yanıta yazılacak)
    ReadData(Config0, Config0 + 16, (unsigned int *)(pu8Response + 8));
    
    // 5. Komut işleme...
    
out:
    // 6. Checksum hesapla
    u16Lcksum = Checksum(pu8Buffer, u8len);  // Tüm 64 byte'ın checksum'ı
    
    // 7. Yanıt paketini oluştur
    outps(pu8Response, u16Lcksum);           // Byte 0-1: Checksum (16-bit)
    ++u32PackNo;                             // Paket numarasını artır
    outpw(pu8Response + 4, u32PackNo);       // Byte 4-7: Paket No (32-bit)
    u32PackNo++;                             // Tekrar artır (2 artıyor!)
    
    return 0;
}
```

**🔴 KRİTİK NOKTA 4:** 
- İlk 8 byte **her zaman atlanıyor**!
- Paket numarası **her yanıtta 2 artıyor** (`++u32PackNo; u32PackNo++;`)

### CMD_CONNECT İşleme (Satır 77-82)

```c
else if(u32Lcmd == CMD_CONNECT)  // 0x000000AE
{
    u32PackNo = 1;  // Paket numarasını 1 yap
    outpw(pu8Response + 8, g_u32ApromSize);      // Byte 8-11: APROM boyutu
    outpw(pu8Response + 12, g_u32DataFlashAddr);  // Byte 12-15: DataFlash adresi
    goto out;
}
```

**Yanıt Formatı:**
- Byte 0-1: Checksum
- Byte 2-3: 0x00 0x00
- Byte 4-7: Paket No (1, sonra 2 olacak)
- Byte 8-11: APROM Size (uint32_t, little-endian)
- Byte 12-15: DataFlash Addr (uint32_t, little-endian)
- Byte 16-63: Config verileri (16 byte)

### CMD_SYNC_PACKNO İşleme (Satır 50-53)

```c
if(u32Lcmd == CMD_SYNC_PACKNO)  // 0x000000A4
{
    u32PackNo = inpw(pu8Src);  // pu8Src += 8 sonrası, yani Byte 8-11
}
```

**🔴 KRİTİK NOKTA 5:** CMD_SYNC_PACKNO gönderilirse paket numarası ayarlanıyor!

**Paket Formatı:**
- Byte 0-3: CMD_SYNC_PACKNO (0x000000A4)
- Byte 4-7: (atlanıyor)
- Byte 8-11: Yeni paket numarası (uint32_t, little-endian)

### CMD_UPDATE_APROM İşleme (Satır 89-116)

#### İlk Paket:

```c
if((u32Lcmd == CMD_UPDATE_APROM) || (u32Lcmd == CMD_UPDATE_DATAFLASH))
{
    // İlk paket: Address ve TotalLen okunuyor
    u32StartAddress = inpw(pu8Src);      // Byte 8-11 (pu8Src += 8 sonrası)
    u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15
    EraseAP(u32StartAddress, u32TotalLen);  // Flash'ı sil
    
    // Tekrar TotalLen oku (neden?)
    u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15
    pu8Src += 8;                         // Byte 16'ya geç
    u32srclen -= 8;                      // 56 - 8 = 48 byte veri
    
    // Backup al
    u32StartAddress_bak = u32StartAddress;
    u32TotalLen_bak = u32TotalLen;
}
```

**İlk Paket Formatı:**
- Byte 0-3: CMD_UPDATE_APROM (0x000000A0)
- Byte 4-7: (atlanıyor)
- Byte 8-11: StartAddress (0x00000000)
- Byte 12-15: TotalLen (7128)
- Byte 16-63: Veri (48 byte)

#### Devam Paketleri:

```c
if((u32Gcmd == CMD_UPDATE_APROM) || (u32Gcmd == CMD_UPDATE_DATAFLASH))
{
    // Devam paketleri: Sadece veri var
    if(u32TotalLen < u32srclen)
    {
        u32srclen = u32TotalLen;  // Son paket için
    }
    
    u32TotalLen -= u32srclen;
    WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
    memset(pu8Src, 0, u32srclen);
    ReadData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
    u32StartAddress += u32srclen;
    u32LastDataLen = u32srclen;
}
```

**Devam Paket Formatı:**
- Byte 0-3: CMD_UPDATE_APROM (0x000000A0)
- Byte 4-7: (atlanıyor)
- Byte 8-63: Veri (56 byte)

**🔴 KRİTİK NOKTA 6:** 
- İlk paket: 48 byte veri (Byte 16-63)
- Devam paketleri: 56 byte veri (Byte 8-63)

### CMD_ERASE_ALL İşleme (Satır 84-87)

```c
else if(u32Lcmd == CMD_ERASE_ALL)  // 0x000000A3
{
    EraseAP(FMC_APROM_BASE, g_u32ApromSize);  // Tüm APROM'u sil
}
```

### CMD_RUN_APROM İşleme (Satır 69-76)

```c
else if(u32Lcmd == CMD_RUN_APROM)  // 0x000000AB
{
    FMC_SetVectorPageAddr(FMC_APROM_BASE);
    NVIC_SystemReset();  // Reset at ve APROM'dan başlat
    while(1);
}
```

---

## 🔍 ADIM 4: Makro Tanımları (inpw, outpw, outps)

Bu makrolar Nuvoton BSP'den geliyor (M261.h). Muhtemelen şöyle tanımlı:

```c
#define inpw(addr)  (*(volatile uint32_t *)(addr))           // 32-bit okuma (little-endian)
#define outpw(addr, val)  (*(volatile uint32_t *)(addr) = (val))  // 32-bit yazma (little-endian)
#define outps(addr, val)  (*(volatile uint16_t *)(addr) = (val))  // 16-bit yazma (little-endian)
```

**Byte Sıralaması (Little-Endian):**
- `inpw(pu8Src)` → `pu8Src[0] | (pu8Src[1] << 8) | (pu8Src[2] << 16) | (pu8Src[3] << 24)`
- `outpw(pu8Response + 4, u32PackNo)` → `pu8Response[4] = u32PackNo & 0xFF; pu8Response[5] = (u32PackNo >> 8) & 0xFF; ...`

---

## 🚨 TESPİT EDİLEN SORUNLAR

### Sorun 1: Paket Numarası Anormallikleri

**Gözlemlenen:**
- Paket No: 512, 1536, 131072, 393216...

**Neden:**
- Byte sıralaması sorunu olabilir
- `bytes_to_uint32()` fonksiyonu yanlış parse ediyor olabilir
- Bootloader'ın gönderdiği paket numarası doğru ama biz yanlış okuyoruz

**Çözüm:**
- Yanıt paketinin byte 4-7'sini doğru parse et
- Little-endian kontrolü yap

### Sorun 2: İlk CMD_UPDATE_APROM Yanıtı Alınamıyor

**Gözlemlenen:**
- `[!] Ilk paket yaniti alinamadi (devam ediliyor)`

**Neden:**
- Flash silme işlemi zaman alıyor (EraseAP)
- Timeout çok kısa (1.0 saniye)
- Bootloader flash yazarken yanıt göndermiyor

**Çözüm:**
- Timeout'u artır (2.0 saniye)
- Flash yazma işlemi tamamlanana kadar bekle

### Sorun 3: Devam Paketlerinde Timeout

**Gözlemlenen:**
- `[!] Yanit alinamadi (timeout)`

**Neden:**
- Her paket sonrası flash yazma işlemi zaman alıyor
- WriteData() fonksiyonu her 4 byte için FMC işlemi yapıyor
- 56 byte = 14 word = 14 FMC işlemi (her biri ~10-20ms)

**Çözüm:**
- Timeout'u artır (2.0 saniye)
- Flash yazma işlemi devam ederken timeout normal

### Sorun 4: Paket Formatı Uyumsuzluğu

**Kontrol Edilmesi Gerekenler:**

1. **İlk Paket:**
   - Byte 0-3: CMD_UPDATE_APROM ✓
   - Byte 4-7: (atlanıyor) ✓
   - Byte 8-11: Address ✓
   - Byte 12-15: TotalLen ✓
   - Byte 16-63: 48 byte veri ✓

2. **Devam Paketleri:**
   - Byte 0-3: CMD_UPDATE_APROM ✓
   - Byte 4-7: (atlanıyor) ✓
   - Byte 8-63: 56 byte veri ✓

3. **Yanıt Paketi:**
   - Byte 0-1: Checksum (16-bit) ✓
   - Byte 2-3: 0x00 0x00 ✓
   - Byte 4-7: Paket No (32-bit) ✓
   - Byte 8-63: Diğer veriler ✓

### Sorun 5: CMD_RUN_APROM Sonrası LED Yanmıyor

**Neden:**
- Firmware yanlış yazılmış olabilir
- Flash yazma başarısız olmuş olabilir
- Reset atılmamış olabilir
- Yeni firmware LED kodunu içermiyor olabilir

**Çözüm:**
- Flash içeriğini verify et (verify_aprom.py)
- CMD_RUN_APROM gönderimini kontrol et
- Reset sonrası UART mesajlarını dinle

---

## ✅ ÖNERİLEN DÜZELTMELER

1. **Timeout Artırma:**
   - İlk CMD_UPDATE_APROM yanıtı: 2.0 saniye
   - Devam paketleri: 2.0 saniye

2. **Paket Numarası Normalizasyonu:**
   - Byte 4-5'i kontrol et (16-bit little-endian)
   - Byte 6-7'yi kontrol et (alternatif)

3. **Flash Yazma Bekleme:**
   - Her paket sonrası yeterli bekleme süresi
   - Timeout toleransı (flash yazma devam ediyor olabilir)

4. **Verification:**
   - Güncelleme sonrası APROM'u verify et
   - CMD_RUN_APROM gönderimini kontrol et

---

## 📊 ÖZET

**Bootloader Akışı:**
1. Reset → 300ms içinde CMD_CONNECT bekle
2. CMD_CONNECT → ISP moduna geç
3. CMD_SYNC_PACKNO → Paket numarasını senkronize et
4. CMD_ERASE_ALL → APROM'u sil
5. CMD_UPDATE_APROM → Firmware yaz
6. CMD_RUN_APROM → Reset at ve APROM'dan başlat

**Paket Formatı:**
- Her paket: 64 byte (sabit)
- İlk 8 byte: Her zaman atlanıyor
- Yanıt: Her zaman 64 byte

**Paket Numarası:**
- Her yanıtta 2 artıyor
- CMD_CONNECT sonrası 1 yapılıyor
- CMD_SYNC_PACKNO ile ayarlanabiliyor

