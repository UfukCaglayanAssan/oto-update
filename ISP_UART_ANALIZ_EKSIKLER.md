# ISP_UART Kod Analizi - Eksikler ve Kritik Noktalar

## 🔍 Kod Analizi

### main.c Analizi

**Akış:**
1. Sistem başlatma (UART, Clock)
2. **300ms timeout** ayarlanıyor (Satır 104)
3. CMD_CONNECT bekleniyor (Satır 117)
4. CMD_CONNECT gelirse → `_ISP` moduna geç
5. Timeout olursa → `_APROM` moduna geç

**Önemli:** 300ms içinde CMD_CONNECT gelmezse APROM'a geçiyor!

### isp_user.c - ParseCmd Fonksiyonu Analizi

#### 1. Paket Formatı (Satır 43-46)
```c
u32Lcmd = inpw(pu8Src);        // Byte 0-3: CMD
outpw(pu8Response + 4, 0);     // Yanıt Byte 4-7: 0
pu8Src += 8;                   // İlk 8 byte atlanıyor!
u32srclen -= 8;
```

**ÖNEMLİ:** İlk 8 byte her zaman atlanıyor!

#### 2. Config Verileri (Satır 48)
```c
ReadData(Config0, Config0 + 16, (unsigned int *)(pu8Response + 8));
```
Config verileri yanıtın Byte 8-23'üne yazılıyor.

#### 3. CMD_SYNC_PACKNO (Satır 50-53)
```c
if(u32Lcmd == CMD_SYNC_PACKNO)
{
    u32PackNo = inpw(pu8Src);  // pu8Src += 8 yapıldıktan sonra, yani Byte 8-11
}
```

**ÖNEMLİ:** CMD_SYNC_PACKNO gönderilirse paket numarası ayarlanıyor!

#### 4. CMD_CONNECT (Satır 77-82)
```c
else if(u32Lcmd == CMD_CONNECT)
{
    u32PackNo = 1;  // Paket numarasını 1 yap
    outpw(pu8Response + 8, g_u32ApromSize);
    outpw(pu8Response + 12, g_u32DataFlashAddr);
    goto out;
}
```

**ÖNEMLİ:** CMD_CONNECT sonrası paket numarası 1 yapılıyor!

#### 5. CMD_UPDATE_APROM - İlk Paket (Satır 106-108)
```c
u32StartAddress = inpw(pu8Src);      // Byte 8-11 (pu8Src += 8 sonrası)
u32TotalLen = inpw(pu8Src + 4);      // Byte 12-15
EraseAP(u32StartAddress, u32TotalLen);
```

**ÖNEMLİ:** İlk pakette Address ve TotalLen okunuyor, sonra silme yapılıyor!

#### 6. CMD_UPDATE_APROM - Veri Yazma (Satır 111-113)
```c
u32TotalLen = inpw(pu8Src + 4);  // Tekrar okunuyor (neden?)
pu8Src += 8;                      // Tekrar 8 byte atlanıyor!
u32srclen -= 8;
```

**ÖNEMLİ:** İlk pakette veri Byte 16'dan başlıyor (48 byte)!

#### 7. Devam Paketleri (Satır 145-158)
```c
if((u32Gcmd == CMD_UPDATE_APROM) || (u32Gcmd == CMD_UPDATE_DATAFLASH))
{
    // pu8Src += 8 yapıldıktan sonra, yani Byte 8'den başlıyor
    WriteData(u32StartAddress, u32StartAddress + u32srclen, (unsigned int *)pu8Src);
    u32StartAddress += u32srclen;
}
```

**ÖNEMLİ:** Devam paketlerinde veri Byte 8'den başlıyor (56 byte)!

#### 8. Yanıt Paketi (Satır 160-165)
```c
u16Lcksum = Checksum(pu8Buffer, u8len);
outps(pu8Response, u16Lcksum);        // Byte 0-1: Checksum
++u32PackNo;                          // Paket numarası artırılıyor
outpw(pu8Response + 4, u32PackNo);   // Byte 4-7: Paket No
u32PackNo++;                          // Tekrar artırılıyor (HATA?)
```

**ÖNEMLİ:** Paket numarası iki kez artırılıyor! (Satır 163 ve 165)

## ⚠️ Tespit Edilen Sorunlar

### 1. CMD_SYNC_PACKNO Eksik! (KRİTİK)

**Sorun:** Python kodunda CMD_SYNC_PACKNO gönderilmiyor!

**Neden Önemli:**
- CMD_CONNECT sonrası paket numarası 1 yapılıyor (Satır 79)
- Ama eğer bootloader daha önce bir işlem yaptıysa paket numarası farklı olabilir
- CMD_SYNC_PACKNO ile paket numarasını garanti altına almak gerekiyor

**Çözüm:**
```python
# CMD_CONNECT sonrası hemen CMD_SYNC_PACKNO gönder
sync_packet = create_packet(CMD_SYNC_PACKNO, 1)  # Byte 8-11'de 1
send_packet(ser, sync_packet)
```

### 2. Paket Numarası İki Kez Artırılıyor (HATA?)

**Sorun:** `isp_user.c` Satır 163-165:
```c
++u32PackNo;
outpw(pu8Response + 4, u32PackNo);
u32PackNo++;
```

**Açıklama:** Bu muhtemelen bir hata değil, belki bir sonraki paket için hazırlık. Ama yanıtta gönderilen paket numarası doğru olmalı.

### 3. CMD_UPDATE_APROM İlk Paket Formatı

**Doğru Format:**
- Byte 0-3: CMD_UPDATE_APROM
- Byte 4-7: Padding (atlanır)
- Byte 8-11: Address
- Byte 12-15: TotalLen
- Byte 16-63: Data (48 byte)

**Python Kodu:** ✅ Doğru!

### 4. CMD_UPDATE_APROM Devam Paketleri

**Doğru Format:**
- Byte 0-3: CMD_UPDATE_APROM
- Byte 4-7: Padding (atlanır)
- Byte 8-63: Data (56 byte)

**Python Kodu:** ✅ Doğru!

## 📋 Eksik Komutlar

### 1. CMD_SYNC_PACKNO (KRİTİK!)

**Durum:** Python kodunda yok!

**Eklenmeli:**
```python
# CMD_CONNECT sonrası
sync_packet = create_packet(CMD_SYNC_PACKNO, 1)
# Byte 8-11'de paket numarası (1)
```

### 2. CMD_ERASE_ALL (Opsiyonel)

**Durum:** Python kodunda var ama kullanılmıyor!

**Kullanım:**
```python
erase_packet = create_packet(CMD_ERASE_ALL)
send_packet(ser, erase_packet)
time.sleep(1.0)  # Silme zaman alır
```

### 3. CMD_RESEND_PACKET (Hata Durumunda)

**Durum:** Python kodunda yok!

**Kullanım:** Paket kaybı durumunda aynı paketi yeniden göndermek için.

## 🎯 Önerilen Komut Sırası

```
1. CMD_CONNECT (0xAE)
   ↓
2. CMD_SYNC_PACKNO (0xA4) ← EKSİK! EKLENMELİ!
   ↓
3. CMD_GET_DEVICEID (0xB1) [Opsiyonel]
   ↓
4. CMD_ERASE_ALL (0xA3) [Opsiyonel]
   ↓
5. CMD_UPDATE_APROM (0xA0) - İlk paket
   ↓
6. CMD_UPDATE_APROM (0xA0) - Devam paketleri
   ↓
7. CMD_RUN_APROM (0xAB) - Reset
```

## 🔧 Yapılması Gerekenler

1. ✅ **CMD_SYNC_PACKNO ekle** - CMD_CONNECT sonrası
2. ✅ **CMD_ERASE_ALL seçeneği** - Güncelleme öncesi (opsiyonel)
3. ⚠️ **CMD_RESEND_PACKET desteği** - Hata durumunda (opsiyonel)

## 📊 Paket Formatı Özeti

### CMD_SYNC_PACKNO
```
Byte 0-3: CMD_SYNC_PACKNO (0xA4)
Byte 4-7: Padding (atlanır)
Byte 8-11: Paket Numarası (uint32_t)
```

### CMD_UPDATE_APROM - İlk Paket
```
Byte 0-3: CMD_UPDATE_APROM (0xA0)
Byte 4-7: Padding (atlanır)
Byte 8-11: Address (uint32_t)
Byte 12-15: TotalLen (uint32_t)
Byte 16-63: Data (48 byte)
```

### CMD_UPDATE_APROM - Devam Paketleri
```
Byte 0-3: CMD_UPDATE_APROM (0xA0)
Byte 4-7: Padding (atlanır)
Byte 8-63: Data (56 byte)
```

