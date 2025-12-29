# Nuvoton Bootloader Geliştirme Notları

## Genel Bakış

Bu doküman, Nuvoton işlemcide bootloader geliştirmek için gerekli bilgileri içerir.

## Protokol

### Handshake Paketi

Python scripti başlangıçta şu paketi gönderir:
```
[0x55, 0x5A]
```

Bootloader bu paketi alınca yanıt olarak `0xAA` göndermelidir.

### Veri Paketi Formatı

Her paket şu formattadır:
```
[START_BYTE] [PACKET_NUM_H] [PACKET_NUM_L] [DATA_SIZE_H] [DATA_SIZE_L] [DATA...] [CHECKSUM]
```

- **START_BYTE**: 0xAA (paket başlangıcı)
- **PACKET_NUM_H/L**: Paket numarası (2 byte, big-endian)
- **DATA_SIZE_H/L**: Veri boyutu (2 byte, big-endian, maksimum 256)
- **DATA**: Gerçek veri (0-256 byte)
- **CHECKSUM**: Tüm paket byte'larının toplamı (mod 256)

### Örnek Paket

Paket 1, 256 byte veri içeriyorsa:
```
[0xAA] [0x00] [0x01] [0x01] [0x00] [256 byte data...] [checksum]
```

## Bootloader Geliştirme Adımları

### 1. UART Başlatma

```c
// UART'ı 115200 baud ile başlat
UART_Open(UART0, 115200);
```

### 2. Handshake İşlemi

```c
uint8_t cmd1, cmd2;
UART_ReadByte(&cmd1);  // 0x55 beklenir
UART_ReadByte(&cmd2);  // 0x5A beklenir
UART_WriteByte(0xAA);  // Yanıt gönder
```

### 3. Paket Alma

1. Start byte (0xAA) bekle
2. Paket numarasını oku (2 byte)
3. Veri boyutunu oku (2 byte)
4. Veriyi oku
5. Checksum'ı oku
6. Checksum kontrolü yap
7. Flash'a yaz

### 4. Flash Yazma

```c
// Flash'ı sil (gerekirse)
FMC_Erase(flash_address, size);

// Flash'a yaz
FMC_Write(flash_address, data, size);
```

### 5. Application'a Geçiş

Güncelleme tamamlandıktan sonra:

```c
// Application adresine atla
void (*application_entry)(void) = (void(*)(void))0x00010000;
application_entry();
```

## Önemli Notlar

### Timeout Mekanizması

Her paket için timeout eklenmelidir. Örneğin:
- Handshake için: 5 saniye
- Paket alma için: 1 saniye

### Hata Yönetimi

- Checksum hatası: Paketi tekrar iste veya hata mesajı gönder
- Flash yazma hatası: Hata mesajı gönder ve durdur
- Timeout: Yeniden başlat veya hata mesajı gönder

### Flash Bölümleme

Örnek flash bölümleme:
- **0x00000000 - 0x0000FFFF**: Bootloader (64 KB)
- **0x00010000 - 0x0007FFFF**: Application (448 KB)
- **0x00080000 - 0x000FFFFF**: Backup/Config (512 KB)

### Watchdog Timer

Sistem donmasını önlemek için watchdog timer kullanın:

```c
SYS_UnlockReg();
WDT_Open(WDT_TIMEOUT_2POW4, WDT_RESET_DELAY_1026CLK, TRUE, FALSE);
SYS_LockReg();
```

### Güvenlik

- Bootloader'ı korumalı bölgede saklayın
- Application'ın bootloader'ı yazmasını engelleyin
- CRC kontrolü ekleyin (sadece checksum yeterli olmayabilir)

## Test Senaryoları

1. **Normal Güncelleme**: Tüm paketler başarıyla alınır ve yazılır
2. **Checksum Hatası**: Yanlış checksum ile paket gönderilir
3. **Timeout**: Paket gönderilmez, timeout kontrol edilir
4. **Kesinti**: Güncelleme yarıda kesilir, sistem recovery yapar
5. **Yanlış Boyut**: Yanlış boyutta paket gönderilir

## Debug İpuçları

- UART üzerinden debug mesajları gönderin
- Her paket için LED yanıp sönsün
- Paket numarasını ve durumu gösterin
- Hata kodlarını UART üzerinden gönderin

## Nuvoton SDK Kaynakları

- Nuvoton M26x Series User Manual
- Nuvoton Standard Peripheral Library (SPL)
- Nuvoton BSP (Board Support Package)
- UART ve FMC (Flash Memory Controller) örnek kodları


