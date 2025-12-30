/***************************************************************************//**
 * @file     application_bootloader_switch.c
 * @brief    Application kodunda bootloader'a geçiş örneği
 * 
 * UART'tan özel komut gelince bootloader'a geçiş yapar
 * Böylece reset yapmadan bootloader'a geçilebilir
 ******************************************************************************/

#include "NuMicro.h"

// Bootloader'a geçiş komutu (UART'tan gelir)
#define CMD_SWITCH_TO_BOOTLOADER  0x42  // Özel komut

void SwitchToBootloader(void)
{
    // FMC'yi aktif et
    CLK->AHBCLK |= CLK_AHBCLK_ISPCKEN_Msk;
    FMC->ISPCTL |= FMC_ISPCTL_ISPEN_Msk;
    
    // Vector page'i LDROM'a ayarla
    FMC_SetVectorPageAddr(FMC_LDROM_BASE);
    
    // Reset yap (bootloader'a geçiş için)
    NVIC_SystemReset();
    
    // Buraya asla gelmez
    while(1);
}

// UART interrupt handler'ında kullanılabilir
void CheckBootloaderSwitch(void)
{
    uint8_t cmd;
    
    // UART'tan komut var mı kontrol et
    if (UART0->FIFOSTS & UART_FIFOSTS_RXEMPTY_Msk == 0)
    {
        cmd = UART0->DAT;
        
        if (cmd == CMD_SWITCH_TO_BOOTLOADER)
        {
            // Bootloader'a geç
            SwitchToBootloader();
        }
    }
}

// Main loop'ta veya interrupt'ta çağrılabilir
void ApplicationMain(void)
{
    // ... application kodunuz ...
    
    // Periyodik olarak kontrol et
    CheckBootloaderSwitch();
    
    // ... diğer işlemler ...
}

