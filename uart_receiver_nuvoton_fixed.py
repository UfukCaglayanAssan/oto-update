#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuvoton ISP Bootloader - Resmi Protokol Uyumlu
Raspberry Pi'de calisir ve Nuvoton'un resmi ISP protokolunu kullanir
"""

import serial
import serial.tools.list_ports
import sys
import time
import os

# UART ayarlari
BAUD_RATE = 115200
TIMEOUT = 2
WRITE_TIMEOUT = 5
MAX_PKT_SIZE = 64  # Nuvoton protokolu: SABIT 64 byte

# Nuvoton ISP Komutlari (isp_user.h'den)
CMD_UPDATE_APROM = 0x000000A0
CMD_UPDATE_CONFIG = 0x000000A1
CMD_READ_CONFIG = 0x000000A2
CMD_ERASE_ALL = 0x000000A3
CMD_SYNC_PACKNO = 0x000000A4
CMD_GET_FWVER = 0x000000A6
CMD_RUN_APROM = 0x000000AB
CMD_RUN_LDROM = 0x000000AC
CMD_RESET = 0x000000AD
CMD_CONNECT = 0x000000AE
CMD_DISCONNECT = 0x000000AF
CMD_GET_DEVICEID = 0x000000B1
CMD_UPDATE_DATAFLASH = 0x000000C3
CMD_RESEND_PACKET = 0x000000FF

