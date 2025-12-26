# Nuvoton UART Haberleşme

Raspberry Pi üzerinde Nuvoton işlemci ile UART üzerinden haberleşme için Python scripti.

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

### Otomatik Port Tespiti
```bash
python3 uart_receiver.py
```

### Manuel Port Belirtme
```bash
python3 uart_receiver.py /dev/ttyUSB0
```

## Ayarlar

Script içinde aşağıdaki parametreleri değiştirebilirsiniz:
- `BAUD_RATE`: Baud rate (varsayılan: 115200)
- `TIMEOUT`: Okuma timeout'u (varsayılan: 1 saniye)

## Notlar

- Raspberry Pi'de genellikle kullanılan portlar:
  - `/dev/ttyUSB0`: USB-Serial dönüştürücü
  - `/dev/ttyAMA0`: GPIO UART (Raspberry Pi 3 ve öncesi)
  - `/dev/ttyS0`: GPIO UART (Raspberry Pi 4)
  - `/dev/ttyACM0`: USB CDC cihazlar

- Programı sonlandırmak için `Ctrl+C` tuşlarına basın.

