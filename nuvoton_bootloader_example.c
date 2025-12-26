/*
 * Nuvoton Bootloader Örnek Kodu
 * UART üzerinden firmware güncellemesi yapar
 * 
 * Bu kod bir örnektir, Nuvoton SDK'nıza göre uyarlanmalıdır
 */

#include <stdint.h>
#include <string.h>

// Bootloader komutları (Python scripti ile aynı)
#define CMD_BOOTLOADER_ENTER  0x55
#define CMD_BOOTLOADER_ACK    0xAA
#define CMD_START_UPDATE      0x5A
#define PACKET_START_BYTE     0xAA

// Paket yapısı
typedef struct {
    uint8_t start_byte;      // 0xAA
    uint8_t packet_num_h;    // Paket numarası (yüksek byte)
    uint8_t packet_num_l;    // Paket numarası (düşük byte)
    uint8_t data_size_h;      // Veri boyutu (yüksek byte)
    uint8_t data_size_l;      // Veri boyutu (düşük byte)
    uint8_t data[256];        // Veri (maksimum 256 byte)
    uint8_t checksum;         // Checksum
} bootloader_packet_t;

// UART fonksiyonları (Nuvoton SDK'ya göre uyarlanmalı)
// Örnek: UART_ReadByte(), UART_WriteByte(), UART_Read(), UART_Write()

// Checksum hesaplama
uint8_t calculate_checksum(uint8_t *data, uint16_t length) {
    uint8_t sum = 0;
    for (uint16_t i = 0; i < length; i++) {
        sum += data[i];
    }
    return sum;
}

// Handshake işlemi
uint8_t bootloader_handshake(void) {
    uint8_t cmd1, cmd2;
    
    // İlk komutu bekle
    if (UART_ReadByte(&cmd1) != 0) return 0;
    if (cmd1 != CMD_BOOTLOADER_ENTER) return 0;
    
    // İkinci komutu bekle
    if (UART_ReadByte(&cmd2) != 0) return 0;
    if (cmd2 != CMD_START_UPDATE) return 0;
    
    // Yanıt gönder
    UART_WriteByte(CMD_BOOTLOADER_ACK);
    
    return 1; // Başarılı
}

// Tek bir paket al
uint8_t receive_packet(bootloader_packet_t *packet, uint8_t *buffer) {
    uint8_t byte;
    uint16_t data_size;
    uint8_t calculated_checksum;
    
    // Start byte'ı bekle
    do {
        if (UART_ReadByte(&byte) != 0) return 0;
    } while (byte != PACKET_START_BYTE);
    
    packet->start_byte = byte;
    
    // Paket numarası
    if (UART_ReadByte(&packet->packet_num_h) != 0) return 0;
    if (UART_ReadByte(&packet->packet_num_l) != 0) return 0;
    
    // Veri boyutu
    if (UART_ReadByte(&packet->data_size_h) != 0) return 0;
    if (UART_ReadByte(&packet->data_size_l) != 0) return 0;
    
    data_size = (packet->data_size_h << 8) | packet->data_size_l;
    
    // Veriyi oku
    if (UART_Read(packet->data, data_size) != data_size) return 0;
    
    // Checksum'ı oku
    if (UART_ReadByte(&packet->checksum) != 0) return 0;
    
    // Checksum kontrolü
    calculated_checksum = calculate_checksum((uint8_t*)packet, 
                                            5 + data_size); // Header + data
    
    if (calculated_checksum != packet->checksum) {
        return 0; // Checksum hatası
    }
    
    // Paket numarasını hesapla
    uint16_t packet_num = (packet->packet_num_h << 8) | packet->packet_num_l;
    
    // Veriyi buffer'a kopyala
    memcpy(buffer, packet->data, data_size);
    
    return data_size; // Başarılı, veri boyutunu döndür
}

// Flash'a yazma fonksiyonu (Nuvoton SDK'ya göre uyarlanmalı)
// Örnek: FMC_Write(addr, data, size)
uint8_t write_to_flash(uint32_t address, uint8_t *data, uint16_t size) {
    // Flash yazma işlemi
    // Nuvoton SDK fonksiyonlarını kullanın
    // Örnek: FMC_Write(address, data, size);
    return 1; // Başarılı
}

// Ana bootloader fonksiyonu
void bootloader_main(void) {
    bootloader_packet_t packet;
    uint8_t data_buffer[256];
    uint32_t flash_address = 0x00010000; // Firmware başlangıç adresi (örnek)
    uint16_t total_received = 0;
    uint16_t packet_count = 0;
    uint8_t data_size;
    
    // UART'ı başlat (115200 baud)
    UART_Open(UART0, 115200);
    
    // Handshake bekle
    while (!bootloader_handshake()) {
        // Handshake gelene kadar bekle
    }
    
    // Paketleri al ve flash'a yaz
    while (1) {
        data_size = receive_packet(&packet, data_buffer);
        
        if (data_size == 0) {
            // Paket hatası veya timeout
            // Hata yanıtı gönder (opsiyonel)
            continue;
        }
        
        // Flash'a yaz
        if (write_to_flash(flash_address, data_buffer, data_size) != 1) {
            // Yazma hatası
            // Hata yanıtı gönder (opsiyonel)
            break;
        }
        
        // Adresi güncelle
        flash_address += data_size;
        total_received += data_size;
        packet_count++;
        
        // Başarı yanıtı gönder (opsiyonel)
        UART_WriteByte(CMD_BOOTLOADER_ACK);
        
        // Son paket kontrolü (veri boyutu 256'dan küçükse son paket)
        if (data_size < 256) {
            break; // Tüm paketler alındı
        }
    }
    
    // Güncelleme tamamlandı
    // Yeni firmware'i çalıştır
    // Örnek: Jump to application
    // ((void(*)())0x00010000)(); // Application'a atla
}

/*
 * NOTLAR:
 * 
 * 1. Bu kod bir örnektir, Nuvoton SDK fonksiyonlarına göre uyarlanmalıdır
 * 2. UART fonksiyonları (UART_ReadByte, UART_WriteByte, vb.) Nuvoton SDK'dan gelmelidir
 * 3. Flash yazma fonksiyonları (FMC_Write) Nuvoton SDK'dan gelmelidir
 * 4. Timeout mekanizması eklenmelidir
 * 5. Hata yönetimi geliştirilmelidir
 * 6. Flash silme işlemi güncelleme öncesi yapılmalıdır
 * 7. Application'a geçiş için jump fonksiyonu eklenmelidir
 * 8. Watchdog timer kullanılmalıdır (sistem donmasını önlemek için)
 */

