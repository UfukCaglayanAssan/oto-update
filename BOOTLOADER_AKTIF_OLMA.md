# Bootloader Otomatik Aktif Olur mu?

## Mevcut Durumunuz

Reset sonrası şu mesaj geliyor:
```
Bootloader NOT Used
```

Bu, bootloader'ın **çalıştığını** ama **henüz kullanılmadığını** gösterir!

## Cevap: Evet, Otomatik Aktif Olur! ✅

**NuMaker-M263KI kartında:**

1. **Reset sonrası bootloader otomatik başlar**
   - NRESET butonuna basınca bootloader çalışmaya başlar
   - "Bootloader NOT Used" mesajı bunu gösterir

2. **Ama bootloader modunda değil!**
   - Bootloader çalışıyor ama normal uygulama modunda
   - Güncelleme moduna geçmek için komut göndermeniz gerekir

## Bootloader Modları

### Mod 1: Normal Uygulama Modu (Şu anki durum)
- Reset sonrası bootloader başlar
- "Bootloader NOT Used" mesajı gösterir
- Normal uygulama çalışır
- Güncelleme yapılamaz

### Mod 2: Bootloader/ISP Modu (Güncelleme için)
- Bootloader güncelleme moduna geçer
- Komut bekler
- Paket alabilir ve flash'a yazabilir

## Bootloader Moduna Geçirme Yöntemleri

### Yöntem 1: Komut Gönderme (En Yaygın)

Reset sonrası **hemen** (1-2 saniye içinde) doğru komutu gönderin:

```python
# Örnek: Handshake komutu
handshake = bytes([0x55, 0x5A])
ser.write(handshake)
```

**Test scriptiniz bunu yapacak:**
```bash
python3 test_handshake_types.py /dev/ttyACM0
```

### Yöntem 2: DIP Switch (Kartınızda Var)

Kartınızın sol üstünde **DIP switch** var:
- **VCOM**: Açık (ON) olmalı
- **TXD/RXD**: UART pin seçimi

Bazı kartlarda DIP switch ile bootloader moduna geçilebilir.

### Yöntem 3: Pin Kombinasyonu

Bazı kartlarda:
- Belirli bir pin'i GND'ye bağlayın
- Reset yapın
- Pin'i serbest bırakın
- Bootloader moduna geçer

### Yöntem 4: Otomatik Mod (Bazı Bootloader'larda)

Reset sonrası belirli süre (1-5 saniye) içinde komut gelmezse:
- Normal uygulamaya geçer
- Komut gelirse bootloader moduna geçer

## Sizin Durumunuz İçin

**"Bootloader NOT Used" mesajı geldiğine göre:**

1. ✅ Bootloader çalışıyor
2. ✅ Reset sonrası otomatik başlıyor
3. ❌ Ama henüz güncelleme modunda değil

**Yapmanız gereken:**

1. **Reset yapın** (NRESET butonu)
2. **Hemen** (1-2 saniye içinde) doğru handshake komutunu gönderin
3. Bootloader yanıt verirse → Moduna geçti ✅
4. Yanıt vermezse → Farklı komut deneyin

## Test Senaryosu

```bash
# 1. Dinleme scriptini çalıştırın
python3 uart_listener.py /dev/ttyACM0

# 2. Reset yapın
# 3. "Bootloader NOT Used" mesajını görün
# 4. Bu, bootloader'ın çalıştığını gösterir

# 5. Şimdi handshake test scriptini çalıştırın
python3 test_handshake_types.py /dev/ttyACM0

# 6. Reset yapın
# 7. Hemen testler başlar
# 8. Hangi komut yanıt veriyor bulun
```

## Özet

**Soru:** Reset sonrası bootloader otomatik aktif olur mu?

**Cevap:** 
- ✅ **Evet, otomatik başlar** (çalışır)
- ❌ **Ama güncelleme modunda değil**
- ✅ **Güncelleme moduna geçmek için komut göndermeniz gerekir**

**Yapmanız gereken:**
1. Reset yapın
2. Hemen (1-2 saniye içinde) doğru handshake komutunu gönderin
3. Bootloader yanıt verirse moduna geçti demektir

## Not

"Bootloader NOT Used" mesajı aslında iyi bir işaret:
- Bootloader çalışıyor ✅
- UART haberleşmesi çalışıyor ✅
- Sadece doğru komutu bulmanız gerekiyor ✅

Test scriptiniz (`test_handshake_types.py`) hangi komutun çalıştığını bulacak!

