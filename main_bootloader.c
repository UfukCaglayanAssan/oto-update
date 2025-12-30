/******************************************************************************
 * @file     main.c
 * @version  V3.00
 * @brief    Bootloader Main - Handshake Dinleyen ve APROM'a Güncelleme Yapan
 *
 * @copyright SPDX-License-Identifier: Apache-2.0
 * @copyright Copyright (C) 2022 Nuvoton Technology Corp. All rights reserved.
*****************************************************************************/
#include <stdio.h>
#include "NuMicro.h"
#include "bootloader_handshake.h"

void SYS_Init(void)
{
    /*---------------------------------------------------------------------------------------------------------*/
    /* Init System Clock                                                                                       */
    /*---------------------------------------------------------------------------------------------------------*/
    /* Enable HIRC clock */
    CLK_EnableXtalRC(CLK_PWRCTL_HIRCEN_Msk);

    /* Wait for HIRC clock ready */
    CLK_WaitClockReady(CLK_STATUS_HIRCSTB_Msk);

    /* Set core clock to 72MHz */
    CLK_SetCoreClock(72000000);

    /* Enable UART1 module clock (PA.3/PA.2 için UART1) */
    CLK_EnableModuleClock(UART1_MODULE);

    /* Select UART1 module clock source as HIRC and UART1 module clock divider as 1 */
    CLK_SetModuleClock(UART1_MODULE, CLK_CLKSEL2_UART1SEL_HIRC, CLK_CLKDIV0_UART1(1));

    /*---------------------------------------------------------------------------------------------------------*/
    /* Init I/O Multi-function                                                                                 */
    /*---------------------------------------------------------------------------------------------------------*/
    /* Set multi-function pins for UART1 RXD and TXD (PA.2/PA.3) */
    SYS->GPA_MFPL = (SYS->GPA_MFPL & (~(UART1_RXD_PA2_Msk | UART1_TXD_PA3_Msk))) | (UART1_RXD_PA2 | UART1_TXD_PA3);
}

int32_t main(void)
{
    /* Unlock protected registers */
    SYS_UnlockReg();

    /* Init System, peripheral clock and multi-function I/O */
    SYS_Init();

    /* Lock protected registers */
    SYS_LockReg();

    /* Bootloader'ı başlat */
    /* Handshake dinler (0x55 0x5A), yanıt verir (0xAA), paketleri alır, APROM'a yazar */
    bootloader_main();

    /* Bootloader'dan çıkıldıysa normal uygulamaya geç */
    /* Güncelleme tamamlandıktan sonra application'a atla */
    // ((void(*)())0x00000000)(); // Application'a atla

    return 0;
}


