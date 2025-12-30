# Nuvoton M263 ISP_UART Bootloader - Detaylı Analiz

## 📋 İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Bellek Yapısı](#bellek-yapısı)
3. [Bootloader Akış Diyagramı](#bootloader-akış-diyagramı)
4. [Protokol Detayları](#protokol-detayları)
5. [Kritik Kod Bölümleri](#kritik-kod-bölümleri)
6. [Boot Pini ve Config0](#boot-pini-ve-config0)
7. [Python Script ile Entegrasyon](#python-script-ile-entegrasyon)

---

## 🎯 Genel Bakış

Nuvoton M263 serisinde ISP_UART, **ikincil bootloader** (secondary bootloader) mantığıyla çalışır. Sistem şu şekilde çalışır:

```
[Reset] → [LDROM Bootloader] → [300ms CMD_CONNECT Bekleme] → [ISP Modu veya APROM]
```

### Temel Mantık:
1. **LDROM (Loader ROM)**: ISP kodunun saklandığı yer (genellikle 0x00100000 adresinde)
2. **APROM (Application ROM)**: Ana uygulamanın çalıştığı yer (0x00000000 adresinde)
3. **Config0**: Boot seçimini yöneten özel Flash kaydı

---

## 💾 Bellek Yapısı

### LDROM (Loader ROM)
- **Adres**: Genellikle `0x00100000`
- **Boyut**: 4KB - 8KB (işlemciye göre değişir)
- **İçerik**: ISP_UART bootloader kodu
- **Amaç**: UART üzerinden firmware güncelleme

### APROM (Application ROM)
- **Adres**: `0x00000000`
- **Boyut**: 64KB - 512KB (işlemciye göre değişir)
- **İçerik**: Ana uygulama kodu
- **Amaç**: Normal çalışma modu

### Config0 (User Configuration)
- **Adres**: `0x00300000` (genellikle)
- **İçerik**: Boot seçimi, güvenlik ayarları, vb.
- **CBS (Chip Boot Selection) Bitleri**: LDROM/APROM seçimi

---

## 🔄 Bootloader Akış Diyagramı

```
┌─────────────────────────────────────────────────────────┐
│ 1. Reset / Power On                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Config0 Kontrolü                                     │
│    - CBS bitleri okunur                                 │
│    - LDROM mu APROM mu?                                 │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ LDROM Boot   │    │ APROM Boot   │
│ (ISP Modu)   │    │ (Normal)     │
└──────┬───────┘    └──────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 3. LDROM'dan Başlatma                                   │
│    - UART0 yapılandırılır (PB.12 RX, PB.13 TX)         │
│    - Baud Rate: 115200                                  │
│    - SysTick 300ms timeout ayarlanır                   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ 4. 300ms Bekleme Penceresi                              │
│    - UART interrupt handler aktif                       │
│    - Her 64 byte paket alındığında g_u8bUartDataReady  │
│    - CMD_CONNECT (0x000000AE) beklenir                  │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ CMD_CONNECT  │    │ Timeout      │
│ Alındı       │    │ (300ms)      │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ ISP Modu     │    │ APROM'a     │
│ (Güncelleme)│    │ Geçiş       │
└──────────────┘    └──────────────┘
```

---

## 📡 Protokol Detayları

### Paket Formatı

**Sabit Paket Boyutu: 64 byte**

#### 1. CMD_CONNECT (0x000000AE)
```
Byte 0-3:   CMD_CONNECT (0xAE 0x00 0x00 0x00) - Little-endian
Byte 4-63:  Padding (0x00)
```

**Yanıt:**
```
Byte 0-1:   Checksum (16-bit, little-endian)
Byte 2-3:   0x00 0x00
Byte 4-7:   Paket No (uint32_t, little-endian)
Byte 8-11:  APROM Size (uint32_t, little-endian)
Byte 12-15: DataFlash Address (uint32_t, little-endian)
Byte 16-31: Config Data (ReadData ile doldurulur)
Byte 32-63: Padding
```

#### 2. CMD_UPDATE_APROM (0x000000A0) - İlk Paket
```
Byte 0-3:   CMD_UPDATE_APROM (0xA0 0x00 0x00 0x00)
Byte 4-7:   Padding (0x00) - pu8Src += 8 ile atlanır
Byte 8-11:  Start Address (uint32_t, little-endian)
Byte 12-15: Total Size (uint32_t, little-endian)
Byte 16-63: Data (48 byte)
```

**İşlem:**
1. `inpw(pu8Src)` → Address okunur (Byte 8-11)
2. `inpw(pu8Src + 4)` → TotalLen okunur (Byte 12-15)
3. `EraseAP(u32StartAddress, u32TotalLen)` → Flash silinir
4. `pu8Src += 8` → Byte 16'ya geçilir
5. `WriteData(u32StartAddress, u32StartAddress + u32srclen, pu8Src)` → Veri yazılır

#### 3. CMD_UPDATE_APROM - Devam Paketleri
```
Byte 0-3:   CMD_UPDATE_APROM (0xA0 0x00 0x00 0x00)
Byte 4-7:   Padding (0x00) - pu8Src += 8 ile atlanır
Byte 8-63:  Data (56 byte)
```

**İşlem:**
1. `pu8Src += 8` → Byte 8'den başlar
2. `WriteData(u32StartAddress, u32StartAddress + u32srclen, pu8Src)` → Veri yazılır
3. `u32StartAddress += u32srclen` → Adres güncellenir

#### 4. CMD_RUN_APROM (0x000000AB)
```
Byte 0-3:   CMD_RUN_APROM (0xAB 0x00 0x00 0x00)
Byte 4-63:  Padding (0x00)
```

**İşlem:**
```c
FMC_SetVectorPageAddr(FMC_APROM_BASE);  // APROM'u boot adresi yap
NVIC_SystemReset();                       // Reset at
```

### Checksum Hesaplama

```c
static uint16_t Checksum(unsigned char *buf, int len)
{
    int i;
    uint16_t c;
    for(c = 0, i = 0 ; i < len; i++)
    {
        c += buf[i];  // Basit toplama checksum
    }
    return (c);
}
```

**Yanıt Paketi:**
- Checksum, gönderilen paketin tüm byte'larının toplamı
- 16-bit little-endian formatında yanıtın ilk 2 byte'ına yazılır

---

## 🔧 Kritik Kod Bölümleri

### 1. main.c - Ana Döngü

```c
int32_t main(void)
{
    // 1. Sistem başlatma
    SYS_UnlockReg();
    SYS_Init();              // Clock, UART yapılandırması
    UART_Init();            // UART0: PB.12 RX, PB.13 TX, 115200 baud
    
    // 2. ISP modunu aktif et
    CLK->AHBCLK |= CLK_AHBCLK_ISPCKEN_Msk;
    FMC->ISPCTL |= FMC_ISPCTL_ISPEN_Msk;
    
    // 3. APROM boyutunu al
    g_u32ApromSize = BL_EnableFMC();
    g_u32DataFlashAddr = SCU->FNSADDR;
    
    // 4. 300ms timeout ayarla
    SysTick->LOAD = 300000 * CyclesPerUs;
    SysTick->VAL = 0x00;
    SysTick->CTRL = SysTick_CTRL_CLKSOURCE_Msk | SysTick_CTRL_ENABLE_Msk;
    
    // 5. CMD_CONNECT bekleme döngüsü
    while (1)
    {
        if ((g_u8bufhead >= 4) || (g_u8bUartDataReady == TRUE))
        {
            uint32_t u32lcmd = inpw(g_au8uart_rcvbuf);
            if (u32lcmd == CMD_CONNECT)
            {
                goto _ISP;  // ISP moduna geç
            }
            else
            {
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
    // ISP modu - komutları işle
    while (1)
    {
        if (g_u8bUartDataReady == TRUE)
        {
            g_u8bUartDataReady = FALSE;
            ParseCmd(g_au8uart_rcvbuf, 64);  // Komutu işle
            PutString();                      // Yanıt gönder
        }
    }
    
_APROM:
    // APROM'a geçiş
    FMC_SetVectorPageAddr(FMC_APROM_BASE);
    NVIC_SystemReset();
    while (1);
}
```

### 2. uart_transfer.c - UART Interrupt Handler

```c
void UART0_IRQHandler(void)
{
    uint32_t u32IntSrc = UART0->INTSTS;
    
    // RX interrupt kontrolü
    if (u32IntSrc & (UART_INTSTS_RXTOIF_Msk | UART_INTSTS_RDAIF_Msk))
    {
        // RX FIFO'dan veri oku
        while (((UART0->FIFOSTS & UART_FIFOSTS_RXEMPTY_Msk) == 0) && 
               (g_u8bufhead < MAX_PKT_SIZE))
        {
            g_au8uart_rcvbuf[g_u8bufhead++] = UART0->DAT;
        }
    }
    
    // 64 byte tamamlandı mı?
    if (g_u8bufhead == MAX_PKT_SIZE)
    {
        g_u8bUartDataReady = TRUE;  // Paket hazır!
        g_u8bufhead = 0;
    }
    else if (u32IntSrc & UART_INTSTS_RXTOIF_Msk)
    {
        g_u8bufhead = 0;  // Timeout - buffer'ı temizle
    }
}
```

**Önemli Noktalar:**
- Her 64 byte paket alındığında `g_u8bUartDataReady = TRUE` olur
- Interrupt handler otomatik olarak çalışır
- Timeout interrupt ile yarım paketler temizlenir

### 3. isp_user.c - Komut İşleme

```c
int ParseCmd(uint8_t *pu8Buffer, uint8_t u8len)
{
    // 1. Komutu oku
    u32Lcmd = inpw(pu8Src);  // Byte 0-3: Komut
    
    // 2. İlk 8 byte'ı atla
    pu8Src += 8;
    u32srclen -= 8;
    
    // 3. Config verilerini oku (her komutta)
    ReadData(Config0, Config0 + 16, (unsigned int *)(pu8Response + 8));
    
    // 4. Komut tipine göre işle
    if (u32Lcmd == CMD_UPDATE_APROM)
    {
        // İlk paket: Address ve TotalLen oku
        u32StartAddress = inpw(pu8Src);      // Byte 8-11
        u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15
        
        // Flash'ı sil
        EraseAP(u32StartAddress, u32TotalLen);
        
        // Veri konumunu ayarla
        pu8Src += 8;  // Byte 16'ya geç
        u32srclen -= 8;
        
        // Veri yaz
        WriteData(u32StartAddress, u32StartAddress + u32srclen, pu8Src);
    }
    
    // 5. Yanıt hazırla
    u16Lcksum = Checksum(pu8Buffer, u8len);
    outps(pu8Response, u16Lcksum);        // Byte 0-1: Checksum
    outpw(pu8Response + 4, u32PackNo);     // Byte 4-7: Paket No
    
    return 0;
}
```

---

## 🔌 Boot Pini ve Config0

### Boot Pini Yok!

Nuvoton M263'te **fiziksel bir boot pini yoktur**. Boot seçimi **Config0** kaydı üzerinden yapılır.

### Config0 Yapısı

```
Config0 (0x00300000):
  - CBS (Chip Boot Selection) bitleri
  - LDROM Boot: CBS = 1
  - APROM Boot: CBS = 0
```

### Boot Seçimi Nasıl Yapılır?

#### 1. İlk Programlama (ICP Tool ile)
- Nu-Link veya ICP Tool kullanarak
- Config0'ı LDROM boot olarak ayarla
- ISP_UART kodunu LDROM'a yükle

#### 2. Yazılımsal Geçiş (APROM'dan LDROM'a)
```c
// APROM uygulamasından LDROM'a geçiş
SYS_UnlockReg();
FMC_Open();
FMC_SetVectorPageAddr(FMC_LDROM_BASE);  // LDROM'u boot adresi yap
NVIC_SystemReset();                       // Reset at
```

#### 3. Reset Sonrası 300ms Penceresi
- Reset sonrası bootloader 300ms boyunca CMD_CONNECT bekler
- Bu süre içinde CMD_CONNECT gelirse ISP moduna geçer
- Gelmezse APROM'a geçer

### Pin Bağlantıları

**UART0 (ISP için):**
- **RX**: PB.12 (Pin 12, Port B)
- **TX**: PB.13 (Pin 13, Port B)
- **Baud Rate**: 115200
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1

**Reset:**
- **nRESET**: Manuel reset butonu (opsiyonel)

---

## 🐍 Python Script ile Entegrasyon

### Mevcut Script Yapısı

`uart_receiver_nuvoton.py` scripti şu adımları izler:

1. **Port Açma**: `/dev/ttyACM0` (USB-UART dönüştürücü)
2. **Sürekli CMD_CONNECT Gönderme**: Reset sonrası 300ms penceresini yakalamak için
3. **Cihaz ID Alma**: CMD_GET_DEVICEID ile doğrulama
4. **Firmware Yükleme**: CMD_UPDATE_APROM ile paket paket gönderme
5. **Reset**: CMD_RUN_APROM ile APROM'a geçiş

### Protokol Uyumluluğu

✅ **Doğru:**
- 64 byte sabit paket boyutu
- Little-endian uint32_t formatı
- Checksum hesaplama
- İlk pakette Address + TotalLen (Byte 8-15)
- İlk pakette veri Byte 16'dan başlar (48 byte)
- Devam paketlerinde veri Byte 8'den başlar (56 byte)

⚠️ **Dikkat Edilmesi Gerekenler:**
- 300ms timeout penceresi çok kısa!
- Reset sonrası hemen CMD_CONNECT gönderilmeli
- Paket numaraları garip görünüyorsa yanıt parse hatası olabilir

---

## 📊 Özet Tablo

| Özellik | Değer |
|---------|-------|
| **LDROM Adresi** | 0x00100000 |
| **APROM Adresi** | 0x00000000 |
| **Paket Boyutu** | 64 byte (sabit) |
| **Baud Rate** | 115200 |
| **UART Pins** | PB.12 (RX), PB.13 (TX) |
| **Timeout** | 300ms (CMD_CONNECT için) |
| **Boot Pini** | Yok (Config0 ile yönetilir) |
| **Checksum** | Basit toplama (16-bit) |

---

## 🎯 Sonuç

Nuvoton M263 ISP_UART bootloader'ı:

1. **LDROM'da çalışır** (0x00100000)
2. **300ms timeout** ile CMD_CONNECT bekler
3. **64 byte sabit paket** formatı kullanır
4. **Little-endian** formatında veri alır/gönderir
5. **Fiziksel boot pini yok**, Config0 ile yönetilir

Python script'iniz bu protokole uygun çalışıyor. Sorun muhtemelen:
- Firmware'in doğru yazılmaması
- CMD_RUN_APROM'un çalışmaması
- Reset sonrası eski firmware'in çalışması

**Öneri:** ISP Tool ile APROM'u okuyup kontrol edin!

