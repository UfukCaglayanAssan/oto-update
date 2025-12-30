/*
 * Nuvoton M263KI Bootloader - Handshake Dinleyen Versiyon
 * Python scripti ile uyumlu (uart_receiver.py)
 * 
 * Derleme: LDROM adresine (0x00100000) derlenmeli
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>

// Nuvoton BSP include'ları
#include "NuMicro.h"
#include "fmc.h"
#include "uart.h"

// Bootloader komutları (Python scripti ile aynı)
#define CMD_BOOTLOADER_ENTER  0x55
#define CMD_BOOTLOADER_ACK    0xAA
#define CMD_START_UPDATE      0x5A
#define PACKET_START_BYTE     0xAA

// UART ayarları
#define UART_BAUD_RATE        115200
#define UART_TIMEOUT_MS       1000
#define MAX_PACKET_SIZE       256

// Flash adresleri (M263KI için)
#define APROM_BASE_ADDRESS    0x00000000
#define LDROM_BASE_ADDRESS    0x00100000
#define FLASH_PAGE_SIZE       512

// Paket yapısı
typedef struct {
    uint8_t start_byte;      // 0xAA
    uint8_t packet_num_h;    // Paket numarası (yüksek byte)
    uint8_t packet_num_l;    // Paket numarası (düşük byte)
    uint8_t data_size_h;     // Veri boyutu (yüksek byte)
    uint8_t data_size_l;     // Veri boyutu (düşük byte)
    uint8_t data[MAX_PACKET_SIZE];  // Veri
    uint8_t checksum;        // Checksum
} bootloader_packet_t;

// UART fonksiyonları (Nuvoton BSP'ye göre uyarlayın)
// Örnek fonksiyonlar - gerçek BSP fonksiyonlarıyla değiştirin

uint8_t UART_ReadByte_Timeout(uint8_t *byte, uint32_t timeout_ms) {
    uint32_t start_time = CLK_GetTickCount();
    while ((CLK_GetTickCount() - start_time) < timeout_ms) {
        if (UART_IS_RX_READY(UART1)) {
            *byte = UART_READ(UART1);
            return 0; // Başarılı
        }
        CLK_SysTickDelay(100); // 0.1ms bekle
    }
    return 1; // Timeout
}

void UART_WriteByte(uint8_t byte) {
    UART_WRITE(UART1, byte);
}

uint32_t UART_Read(uint8_t *buffer, uint32_t size) {
    uint32_t bytes_read = 0;
    uint32_t start_time = CLK_GetTickCount();
    uint32_t timeout = 1000; // 1 saniye timeout
    
    while (bytes_read < size && (CLK_GetTickCount() - start_time) < timeout) {
        if (UART_IS_RX_READY(UART1)) {
            buffer[bytes_read++] = UART_READ(UART1);
            start_time = CLK_GetTickCount(); // Reset timeout
        }
        CLK_SysTickDelay(100); // 0.1ms bekle
    }
    return bytes_read;
}

void UART_Init(void) {
    // UART1'i 115200 baud ile başlat (PA.3/PA.2 için)
    UART_Open(UART1, UART_BAUD_RATE);
}

// Checksum hesaplama (Python scripti ile aynı)
uint8_t calculate_checksum(uint8_t *data, uint16_t length) {
    uint8_t sum = 0;
    for (uint16_t i = 0; i < length; i++) {
        sum += data[i];
    }
    return sum;
}

// Handshake işlemi - Python scriptinden gelen [0x55, 0x5A] paketini dinler
uint8_t bootloader_handshake(void) {
    uint8_t cmd1, cmd2;
    uint32_t timeout = 0;
    
    // İlk komutu bekle (0x55)
    timeout = 0;
    while (UART_ReadByte_Timeout(&cmd1, 100) != 0) {
        timeout++;
        if (timeout > (UART_TIMEOUT_MS / 100)) {
            return 0; // Timeout
        }
    }
    
    if (cmd1 != CMD_BOOTLOADER_ENTER) {
        return 0; // Yanlış komut
    }
    
    // İkinci komutu bekle (0x5A)
    timeout = 0;
    while (UART_ReadByte_Timeout(&cmd2, 100) != 0) {
        timeout++;
        if (timeout > (UART_TIMEOUT_MS / 100)) {
            return 0; // Timeout
        }
    }
    
    if (cmd2 != CMD_START_UPDATE) {
        return 0; // Yanlış komut
    }
    
    // Yanıt gönder (0xAA)
    UART_WriteByte(CMD_BOOTLOADER_ACK);
    
    return 1; // Başarılı
}

// Tek bir paket al - Python scriptinden gelen paket formatı
uint8_t receive_packet(bootloader_packet_t *packet, uint8_t *buffer) {
    uint8_t byte;
    uint16_t data_size;
    uint8_t calculated_checksum;
    uint32_t timeout = 0;
    
    // Start byte'ı bekle (0xAA)
    timeout = 0;
    do {
        if (UART_ReadByte_Timeout(&byte, 50) != 0) {
            timeout++;
            if (timeout > 20) { // 1 saniye timeout
                return 0; // Timeout
            }
            continue;
        }
        timeout = 0; // Reset timeout
    } while (byte != PACKET_START_BYTE);
    
    packet->start_byte = byte;
    
    // Paket numarası (2 byte)
    if (UART_ReadByte_Timeout(&packet->packet_num_h, 100) != 0) return 0;
    if (UART_ReadByte_Timeout(&packet->packet_num_l, 100) != 0) return 0;
    
    // Veri boyutu (2 byte)
    if (UART_ReadByte_Timeout(&packet->data_size_h, 100) != 0) return 0;
    if (UART_ReadByte_Timeout(&packet->data_size_l, 100) != 0) return 0;
    
    data_size = (packet->data_size_h << 8) | packet->data_size_l;
    
    // Veri boyutu kontrolü
    if (data_size > MAX_PACKET_SIZE) {
        return 0; // Çok büyük paket
    }
    
    // Veriyi oku
    uint32_t bytes_read = UART_Read(packet->data, data_size);
    if (bytes_read != data_size) {
        return 0; // Okuma hatası
    }
    
    // Checksum'ı oku
    if (UART_ReadByte_Timeout(&packet->checksum, 100) != 0) return 0;
    
    // Checksum kontrolü
    // Python scripti: START_BYTE dahil tüm paket üzerinden checksum hesaplıyor
    // [START_BYTE, PACKET_NUM_H, PACKET_NUM_L, DATA_SIZE_H, DATA_SIZE_L, DATA...]
    uint8_t checksum_data[5 + data_size];
    checksum_data[0] = packet->start_byte;
    checksum_data[1] = packet->packet_num_h;
    checksum_data[2] = packet->packet_num_l;
    checksum_data[3] = packet->data_size_h;
    checksum_data[4] = packet->data_size_l;
    memcpy(&checksum_data[5], packet->data, data_size);
    
    calculated_checksum = calculate_checksum(checksum_data, 5 + data_size);
    
    if (calculated_checksum != packet->checksum) {
        return 0; // Checksum hatası
    }
    
    // Veriyi buffer'a kopyala
    memcpy(buffer, packet->data, data_size);
    
    return data_size; // Başarılı, veri boyutunu döndür
}

// Flash'a yazma fonksiyonu
uint8_t write_to_flash(uint32_t address, uint8_t *data, uint16_t size) {
    FMC_Open();
    
    // 4 byte (word) olarak yaz
    for (uint16_t i = 0; i < size; i += 4) {
        uint32_t word;
        if (i + 4 <= size) {
            word = *(uint32_t*)(data + i);
        } else {
            // Son kısım 4 byte'tan küçükse, kalan byte'ları 0xFF ile doldur
            word = 0xFFFFFFFF;
            uint8_t remaining = size - i;
            memcpy(&word, data + i, remaining);
        }
        
        if (FMC_Write(address + i, word) != 0) {
            FMC_Close();
            return 0; // Yazma hatası
        }
    }
    
    FMC_Close();
    return 1; // Başarılı
}

// Flash silme fonksiyonu
uint8_t erase_flash(uint32_t address, uint32_t size) {
    FMC_Open();
    
    // Sayfa sayfa sil (FLASH_PAGE_SIZE = 512 byte)
    uint32_t pages = (size + FLASH_PAGE_SIZE - 1) / FLASH_PAGE_SIZE;
    for (uint32_t i = 0; i < pages; i++) {
        uint32_t page_addr = address + (i * FLASH_PAGE_SIZE);
        if (FMC_Erase(page_addr) != 0) {
            FMC_Close();
            return 0; // Silme hatası
        }
    }
    
    FMC_Close();
    return 1; // Başarılı
}

// Ana bootloader fonksiyonu
void bootloader_main(void) {
    bootloader_packet_t packet;
    uint8_t data_buffer[MAX_PACKET_SIZE];
    uint32_t flash_address = APROM_BASE_ADDRESS; // APROM başlangıç adresi
    uint16_t total_received = 0;
    uint16_t packet_count = 0;
    uint8_t data_size;
    uint8_t handshake_received = 0;
    
    // UART'ı başlat
    UART_Init();
    
    // Handshake bekle (sonsuz döngü - reset sonrası hemen dinlemeye başla)
    while (1) {
        if (bootloader_handshake()) {
            handshake_received = 1;
            break; // Handshake alındı, paketleri beklemeye başla
        }
        // Handshake gelene kadar bekle (kısa delay)
        CLK_SysTickDelay(1000); // 1ms bekle
    }
    
    if (!handshake_received) {
        // Handshake alınamadı, normal uygulamaya geç
        // ((void(*)())APROM_BASE_ADDRESS)(); // Application'a atla
        return;
    }
    
    // APROM'u sil (güncelleme öncesi)
    // erase_flash(APROM_BASE_ADDRESS, 0x80000); // 512KB sil (M263KI için)
    
    // Paketleri al ve flash'a yaz
    while (1) {
        data_size = receive_packet(&packet, data_buffer);
        
        if (data_size == 0) {
            // Paket hatası veya timeout
            // Hata yanıtı gönder (opsiyonel)
            UART_WriteByte(0xFF); // Hata kodu
            continue;
        }
        
        // Flash'a yaz
        if (write_to_flash(flash_address, data_buffer, data_size) != 1) {
            // Yazma hatası
            UART_WriteByte(0xFE); // Yazma hatası kodu
            break;
        }
        
        // Adresi güncelle
        flash_address += data_size;
        total_received += data_size;
        packet_count++;
        
        // Başarı yanıtı gönder
        UART_WriteByte(CMD_BOOTLOADER_ACK);
        
        // Son paket kontrolü (veri boyutu 256'dan küçükse son paket)
        if (data_size < MAX_PACKET_SIZE) {
            break; // Tüm paketler alındı
        }
    }
    
    // Güncelleme tamamlandı
    // Yeni firmware'i çalıştır
    // ((void(*)())APROM_BASE_ADDRESS)(); // Application'a atla
}

// main() fonksiyonu main.c dosyasında olacak
// Bu dosyada sadece bootloader_main() fonksiyonu var

/*
 * DERLEME NOTLARI:
 * 
 * 1. Bu kodu Nuvoton BSP ile derleyin
 * 2. Linker script'te LDROM adresini ayarlayın: 0x00100000
 * 3. UART fonksiyonlarını Nuvoton BSP'den import edin
 * 4. Flash yazma fonksiyonlarını implement edin
 * 5. Watchdog timer ekleyin
 * 6. Timeout mekanizmalarını iyileştirin
 * 
 * ÖNEMLİ:
 * - UART1 kullanıyorsanız (Chip Settings'te PA.3/PA.2 seçiliyse):
 *   UART_Open(UART1, 115200);
 * - UART0 kullanıyorsanız:
 *   UART_Open(UART0, 115200);
 * 
 * - Flash yazma için FMC_Open(), FMC_Write(), FMC_Close() kullanın
 * - Flash silme için FMC_Erase() kullanın
 */

