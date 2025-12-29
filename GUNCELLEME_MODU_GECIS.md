# Güncelleme Moduna Geçiş Yöntemleri

## İki Seçenek Var

### Seçenek 1: Handshake Dışında Komutlar Göndermek

Handshake'den sonra başka komutlar göndermek gerekebilir.

### Seçenek 2: Kart Tarafında Bir Şey Yapmak

DIP switch, pin kombinasyonu, flash silme gibi fiziksel işlemler.

## Test: Her İkisini de Deneyelim

### Test 1: Handshake Sonrası Komutlar

`test_handshake_sequence.py` scriptini çalıştırın:
- Handshake gönderir
- Sonra farklı komutlar gönderir
- Hangi komut dizisinin çalıştığını bulur

### Test 2: Kart Tarafında İşlemler

1. **DIP Switch Ayarları**
2. **Flash Silme**
3. **Pin Kombinasyonu**

## Önerilen Test Sırası

### Adım 1: Handshake Sonrası Komutlar (Önce Bunu Deneyin)

```bash
python3 test_handshake_sequence.py /dev/ttyACM0
```

Bu test:
- Handshake gönderir
- Sonra farklı komutlar gönderir
- Hangi komut dizisinin güncelleme moduna geçirdiğini bulur

**Eğer çalışırsa:** ✅ Sadece komut göndermek yeterli
**Eğer çalışmazsa:** ❌ Kart tarafında bir şey yapmak gerekiyor

### Adım 2: Kart Tarafında İşlemler

Eğer komutlar çalışmazsa:

1. **DIP Switch Kontrolü**
   - VCOM, TXD, RXD switch'lerini farklı kombinasyonlarda deneyin
   - Kartın dokümantasyonuna bakın

2. **Flash Silme**
   - ISP Tool ile flash'ı silin
   - Flash boşsa bootloader güncelleme moduna geçebilir

3. **Pin Kombinasyonu**
   - Belirli pin'i GND'ye bağlayın
   - Reset yapın
   - Pin'i serbest bırakın

## Muhtemel Senaryo

**Çoğu bootloader için:**
- Handshake tek başına yeterli değil
- Handshake + başka komutlar gerekir
- VEYA kart tarafında bir işlem gerekir (DIP switch, flash silme)

## Hızlı Test

Önce komut dizisini test edin:
```bash
python3 test_handshake_sequence.py /dev/ttyACM0
```

Eğer çalışmazsa, kart tarafında işlem yapın (DIP switch, flash silme).

