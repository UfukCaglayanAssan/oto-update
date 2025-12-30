# Nuvoton ISP Bootloader Protokol Analizi

## 🔍 BULGULAR

### ❌ MEVCUT PYTHON SCRIPTİ YANLIŞ!

**Sorunlar:**
1. **Handshake yok!** - `0x55 0x5A` gibi bir handshake protokolü YOK
2. **Yanlış paket formatı** - 256 byte değişken paket boyutu kullanıyor, ama Nuvoton **64 byte sabit** paket bekliyor
3. **Yanlış komut formatı** - `CMD_CONNECT` (0x000000AE) gönderilmesi gerekiyor

---

## ✅ DOĞRU PROTOKOL

### 1. BAĞLANTI (CONNECT)

**Komut:** `CMD_CONNECT = 0x000000AE`

**Paket Formatı (64 byte):**
```
Byte 0-3:   CMD_CONNECT (0xAE 0x00 0x00 0x00) - Little-endian
Byte 4-7:   0x00 0x00 0x00 0x00 (boş)
Byte 8-63:  0x00... (boş, toplam 64 byte)
```

**Yanıt (64 byte):**
```
Byte 0-1:   Checksum (16-bit, little-endian)
Byte 2-3:   0x00 0x00
Byte 4-7:   Paket numarası (uint32_t, little-endian)
Byte 8-11:  APROM boyutu (uint32_t, little-endian)
Byte 12-15: DataFlash adresi (uint32_t, little-endian)
Byte 16-63: Config verileri
```

**Timeout:** 300ms içinde CMD_CONNECT gelmezse bootloader APROM'a geçer!

---

### 2. GÜNCELLEME (UPDATE APROM)

**Komut:** `CMD_UPDATE_APROM = 0x000000A0`

**İlk Paket (64 byte):**
```
Byte 0-3:   CMD_UPDATE_APROM (0xA0 0x00 0x00 0x00)
Byte 4-7:   Başlangıç adresi (uint32_t, little-endian) - Genelde 0x00000000
Byte 8-11:  Toplam boyut (uint32_t, little-endian)
Byte 12-63: İlk veri paketi (52 byte)
```

**Devam Paketleri (64 byte):**
```
Byte 0-3:   CMD_UPDATE_APROM (0xA0 0x00 0x00 0x00) veya devam eden komut
Byte 4-7:   Paket numarası (uint32_t, little-endian)
Byte 8-63:  Veri (56 byte)
```

**Yanıt (64 byte):**
```
Byte 0-1:   Checksum (16-bit, little-endian)
Byte 2-3:   0x00 0x00
Byte 4-7:   Paket numarası (uint32_t, little-endian)
Byte 8-63:  Okunan veri (doğrulama için)
```

---

### 3. DİĞER KOMUTLAR

```c
#define CMD_UPDATE_APROM      0x000000A0
#define CMD_UPDATE_CONFIG     0x000000A1
#define CMD_READ_CONFIG       0x000000A2
#define CMD_ERASE_ALL         0x000000A3
#define CMD_SYNC_PACKNO       0x000000A4
#define CMD_GET_FWVER         0x000000A6
#define CMD_RUN_APROM         0x000000AB
#define CMD_RUN_LDROM         0x000000AC
#define CMD_RESET             0x000000AD
#define CMD_CONNECT           0x000000AE
#define CMD_DISCONNECT        0x000000AF
#define CMD_GET_DEVICEID      0x000000B1
#define CMD_UPDATE_DATAFLASH  0x000000C3
#define CMD_RESEND_PACKET     0x000000FF
```

---

## 📋 PROTOKOL ÖZELLİKLERİ

### Paket Boyutu
- **SABİT: 64 byte** (MAX_PKT_SIZE = 64)
- Değişken paket boyutu YOK!

### Checksum
- **16-bit checksum** (uint16_t)
- Tüm paket için hesaplanır
- Little-endian formatında

### Paket Numarası
- **uint32_t** (4 byte)
- Little-endian formatında
- Her yanıtta artırılır

### Timeout
- **300ms** - Reset sonrası CMD_CONNECT gelmezse APROM'a geçer
- Çok kısa süre! Reset sonrası HEMEN gönderilmeli

---

## 🔧 PYTHON SCRIPTİNDE YAPILMASI GEREKENLER

### 1. Handshake Kaldırılmalı
- `send_handshake()` fonksiyonu kaldırılmalı
- `0x55 0x5A` gönderilmemeli

### 2. CMD_CONNECT Gönderilmeli
- Reset sonrası HEMEN `CMD_CONNECT` (0x000000AE) gönderilmeli
- 64 byte paket formatında

### 3. Paket Formatı Değiştirilmeli
- **256 byte değişken paket** → **64 byte sabit paket**
- Her paket tam 64 byte olmalı
- Eksik kısımlar 0x00 ile doldurulmalı

### 4. Komut Formatı
- Her paketin ilk 4 byte'ı komut (uint32_t, little-endian)
- Sonraki 4 byte parametreler
- Sonraki 56 byte veri

### 5. Checksum Hesaplama
- 16-bit checksum (uint16_t)
- Tüm paket için toplam

---

## ⚠️ BOOTLOADER TARAFINDA SORUN VAR MI?

### ✅ Bootloader Kodu Doğru Görünüyor

**main.c:**
- Reset sonrası 300ms timeout ile CMD_CONNECT bekliyor ✓
- CMD_CONNECT gelirse ISP moduna geçiyor ✓
- Timeout olursa APROM'a geçiyor ✓

**isp_user.c:**
- CMD_CONNECT'i doğru işliyor ✓
- APROM boyutu ve DataFlash adresini döndürüyor ✓
- CMD_UPDATE_APROM ile güncelleme yapıyor ✓

**uart_transfer.c:**
- 64 byte sabit paket boyutu ✓
- UART interrupt ile veri alıyor ✓
- RX timeout interrupt var ✓

### ⚠️ Dikkat Edilmesi Gerekenler

1. **UART Pinleri:** 
   - Kod UART0, PB12/PB13 kullanıyor
   - Sizin kartınızda hangi UART kullanılıyor kontrol edin

2. **Baud Rate:**
   - Kod 115200 kullanıyor ✓ (Python scriptiyle uyumlu)

3. **Timeout:**
   - 300ms çok kısa! Reset sonrası HEMEN CMD_CONNECT gönderilmeli

---

## 📝 ÖZET

**Sorun:** Python scripti tamamen yanlış protokol kullanıyor!

**Çözüm:**
1. Handshake kaldırılmalı (`0x55 0x5A` yok)
2. CMD_CONNECT (0x000000AE) gönderilmeli
3. 64 byte sabit paket formatı kullanılmalı
4. Reset sonrası HEMEN (300ms içinde) gönderilmeli

**Bootloader tarafı:** Kod doğru görünüyor, sadece UART pinlerini kontrol edin.

