# Nuvoton Bootloader Güncelleme

Raspberry Pi üzerinde Nuvoton işlemci ile UART üzerinden bootloader güncellemesi yapan Python scripti.

## Özellikler

- Binary dosyayı paket paket UART üzerinden gönderir
- Script başladıktan 10 saniye sonra otomatik gönderim başlar
- Her paket için checksum hesaplar
- Gönderim sırasında ilerleme gösterir
- Güncelleme sonrası karşı taraftan gelen yanıtları dinler

## Kurulum

1. Gerekli paketi yükleyin:
```bash
pip install -r requirements.txt
```

veya doğrudan:
```bash
pip install pyserial
```

## Kullanım

### Varsayılan Binary Dosya ile (NuvotonM26x-Bootloader-Test.bin)
```bash
# Otomatik port tespiti
python3 uart_receiver.py

# Manuel port belirtme
python3 uart_receiver.py /dev/ttyUSB0
```

### Özel Binary Dosya ile
```bash
python3 uart_receiver.py /dev/ttyUSB0 custom_bootloader.bin
```

## Paket Formatı

Her paket aşağıdaki formatta gönderilir:
- **START_BYTE** (0xAA): Paket başlangıç byte'ı
- **PACKET_NUM_H**: Paket numarası (yüksek byte)
- **PACKET_NUM_L**: Paket numarası (düşük byte)
- **DATA_SIZE**: Paket içindeki veri boyutu
- **DATA**: Gerçek veri (varsayılan 256 byte)
- **CHECKSUM**: Paket checksum'ı (byte toplamı)

## Ayarlar

Script içinde aşağıdaki parametreleri değiştirebilirsiniz:
- `BAUD_RATE`: Baud rate (varsayılan: 115200)
- `TIMEOUT`: Okuma timeout'u (varsayılan: 1 saniye)
- `WAIT_TIME`: Gönderim öncesi bekleme süresi (varsayılan: 10 saniye)
- `PACKET_SIZE`: Her paketteki byte sayısı (varsayılan: 256)

## Notlar

- Raspberry Pi'de genellikle kullanılan portlar:
  - `/dev/ttyUSB0`: USB-Serial dönüştürücü
  - `/dev/ttyAMA0`: GPIO UART (Raspberry Pi 3 ve öncesi)
  - `/dev/ttyS0`: GPIO UART (Raspberry Pi 4)
  - `/dev/ttyACM0`: USB CDC cihazlar

- Programı sonlandırmak için `Ctrl+C` tuşlarına basın.

- Paket formatı Nuvoton bootloader protokolüne göre özelleştirilebilir. Gerekirse `send_packet()` fonksiyonunu düzenleyin.

