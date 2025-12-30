# Nuvoton ISP Protokol Düzeltme Özeti

## 🔍 ANALİZ SONUÇLARI

### ❌ MEVCUT PYTHON SCRIPTİ (`uart_receiver.py`) YANLIŞ!

**Sorunlar:**
1. ❌ **Handshake yok!** - `0x55 0x5A` gibi bir handshake protokolü YOK
2. ❌ **Yanlış paket formatı** - 256 byte değişken paket, ama Nuvoton **64 byte sabit** paket bekliyor
3. ❌ **Yanlış komut formatı** - `CMD_CONNECT` (0x000000AE) gönderilmesi gerekiyor

---

## ✅ DOĞRU PROTOKOL

### 1. CMD_CONNECT (Bağlantı)

**Komut:** `0x000000AE` (4 byte, little-endian: `AE 00 00 00`)

**Paket Formatı (64 byte):**
```
Byte 0-3:   CMD_CONNECT (0xAE 0x00 0x00 0x00)
Byte 4-63:   0x00... (boş)
```

**Yanıt (64 byte):**
```
Byte 0-1:   Checksum (16-bit, little-endian)
Byte 2-3:   0x00 0x00
Byte 4-7:   Paket numarası (uint32_t)
Byte 8-11:  APROM boyutu (uint32_t)
Byte 12-15: DataFlash adresi (uint32_t)
Byte 16-63: Config verileri
```

**⚠️ ÖNEMLİ:** 300ms timeout! Reset sonrası HEMEN gönderilmeli!

---

### 2. CMD_UPDATE_APROM (Güncelleme)

**Komut:** `0x000000A0`

**İlk Paket (64 byte):**
```
Byte 0-3:   CMD_UPDATE_APROM (0xA0 0x00 0x00 0x00)
Byte 4-7:   Başlangıç adresi (uint32_t) - Genelde 0x00000000
Byte 8-11:  Toplam boyut (uint32_t)
Byte 12-63: İlk veri paketi (52 byte)
```

**Devam Paketleri (64 byte):**
```
Byte 0-3:   CMD_UPDATE_APROM (0xA0 0x00 0x00 0x00)
Byte 4-7:   Paket numarası (uint32_t)
Byte 8-63:  Veri (56 byte)
```

---

## 📝 YENİ DOSYALAR

### 1. `uart_receiver_nuvoton.py`
- ✅ Nuvoton'un resmi protokolüne uygun
- ✅ CMD_CONNECT kullanıyor
- ✅ 64 byte sabit paket formatı
- ✅ Doğru komut formatı (uint32_t little-endian)
- ✅ 16-bit checksum

### 2. `NUVOTON_ISP_PROTOKOL_ANALIZI.md`
- Detaylı protokol analizi
- Komut listesi
- Paket formatları

---

## 🔧 BOOTLOADER TARAFINDA SORUN VAR MI?

### ✅ Bootloader Kodu Doğru Görünüyor

**ISP_UART/main.c:**
- ✅ Reset sonrası 300ms timeout ile CMD_CONNECT bekliyor
- ✅ CMD_CONNECT gelirse ISP moduna geçiyor
- ✅ Timeout olursa APROM'a geçiyor

**ISP_UART/isp_user.c:**
- ✅ CMD_CONNECT'i doğru işliyor
- ✅ APROM boyutu ve DataFlash adresini döndürüyor
- ✅ CMD_UPDATE_APROM ile güncelleme yapıyor

**ISP_UART/uart_transfer.c:**
- ✅ 64 byte sabit paket boyutu
- ✅ UART interrupt ile veri alıyor
- ✅ RX timeout interrupt var

### ⚠️ Dikkat Edilmesi Gerekenler

1. **UART Pinleri:** 
   - Kod UART0, PB12/PB13 kullanıyor
   - Sizin kartınızda hangi UART kullanılıyor kontrol edin

2. **Baud Rate:**
   - Kod 115200 kullanıyor ✓ (Python scriptiyle uyumlu)

3. **Timeout:**
   - 300ms çok kısa! Reset sonrası HEMEN CMD_CONNECT gönderilmeli

---

## 🚀 KULLANIM

### Yeni Script ile:

```bash
python3 uart_receiver_nuvoton.py [port] [dosya.bin]
```

**Örnek:**
```bash
python3 uart_receiver_nuvoton.py /dev/ttyACM0 NuvotonM26x-Bootloader-Test.bin
```

**Adımlar:**
1. Scripti çalıştırın
2. Kartı RESET yapın
3. HEMEN ENTER'a basın (300ms içinde!)
4. Script CMD_CONNECT gönderecek
5. Güncelleme başlayacak

---

## 📋 ÖZET

**Sorun:** Python scripti tamamen yanlış protokol kullanıyordu!

**Çözüm:**
- ✅ `uart_receiver_nuvoton.py` - Yeni, doğru protokol
- ✅ Handshake kaldırıldı
- ✅ CMD_CONNECT kullanılıyor
- ✅ 64 byte sabit paket formatı
- ✅ Doğru komut formatı

**Bootloader tarafı:** Kod doğru görünüyor, sadece UART pinlerini kontrol edin.

