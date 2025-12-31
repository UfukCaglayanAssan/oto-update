#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time
import struct
import sys
import os

# ===============================
# CONFIG
# ===============================
PORT = "/dev/ttyACM0"
BAUD = 115200
PACKET_SIZE = 64

# ===============================
# COMMANDS (ISP)
# ===============================
CMD_CONNECT        = 0xAE
CMD_SYNC_PACKNO    = 0xA4
CMD_GET_DEVICEID   = 0xB1
CMD_ERASE_ALL      = 0xA3
CMD_UPDATE_APROM   = 0xA0
CMD_RUN_APROM      = 0xAB

# ===============================
# UTILS
# ===============================
def u32(v):
    return struct.pack("<I", v)

def checksum(buf):
    return sum(buf) & 0xFFFF

def read_exact(ser, n, timeout=2):
    buf = b""
    t = time.time()
    while len(buf) < n:
        if ser.in_waiting:
            buf += ser.read(n - len(buf))
        elif time.time() - t > timeout:
            return None
    return buf

def send_packet(ser, pkt):
    if len(pkt) != 64:
        raise ValueError("Packet must be 64 bytes")
    ser.write(pkt)
    ser.flush()

def recv_packet(ser):
    return read_exact(ser, 64)

# ===============================
# PACKET BUILDERS
# ===============================
def pkt_simple(cmd, packno):
    p = bytearray(64)
    p[0:4] = u32(cmd)
    p[4:8] = u32(packno)
    return p

def pkt_update_first(addr, size, data, packno):
    p = bytearray(64)
    p[0:4]   = u32(CMD_UPDATE_APROM)
    p[4:8]   = u32(packno)
    p[8:12]  = u32(addr)
    p[12:16] = u32(size)
    p[16:16+len(data)] = data
    return p

def pkt_update_next(data, packno):
    p = bytearray(64)
    p[0:4] = u32(CMD_UPDATE_APROM)
    p[4:8] = u32(packno)
    p[8:8+len(data)] = data
    return p

# ===============================
# ISP CORE
# ===============================
def wait_bootloader(ser):
    print("[*] Bootloader bekleniyor (RESET at)...")
    while True:
        send_packet(ser, pkt_simple(CMD_CONNECT, 1))
        r = recv_packet(ser)
        if r:
            print("[OK] Bootloader bulundu!")
            return
        time.sleep(0.2)

def get_device_id(ser):
    send_packet(ser, pkt_simple(CMD_GET_DEVICEID, 2))
    r = recv_packet(ser)
    if not r:
        return None
    return struct.unpack("<I", r[8:12])[0]

def erase_flash(ser):
    print("[*] Flash siliniyor...")
    send_packet(ser, pkt_simple(CMD_ERASE_ALL, 3))
    recv_packet(ser)
    print("[OK] Flash silindi")

def program_flash(ser, fw):
    size = len(fw)
    print(f"[*] Yazılıyor: {size} byte")

    packno = 4
    offset = 0

    first = pkt_update_first(0x00000000, size, fw[:48], packno)
    send_packet(ser, first)
    recv_packet(ser)

    offset = 48
    packno += 1

    while offset < size:
        chunk = fw[offset:offset+56]
        pkt = pkt_update_next(chunk, packno)
        send_packet(ser, pkt)
        r = recv_packet(ser)
        if not r:
            print("❌ Yazma hatası")
            return False

        offset += len(chunk)
        packno += 1
        print(f"  → {offset}/{size}")

    print("[OK] Yazma tamamlandı")
    return True

def run_app(ser):
    print("[*] Uygulama başlatılıyor")
    send_packet(ser, pkt_simple(CMD_RUN_APROM, 0))
    time.sleep(0.5)

# ===============================
# MAIN
# ===============================
def main():
    fw_name = "NuvotonM26x-Bootloader-Test.bin"

    print("=== M263 UART ISP ===")

    with open(fw_name, "rb") as f:
        fw = f.read()

    ser = serial.Serial(
        PORT,
        BAUD,
        timeout=0.1,
        rtscts=False,
        dsrdtr=False
    )

    wait_bootloader(ser)

    dev = get_device_id(ser)
    print(f"[OK] Device ID: 0x{dev:08X}")

    erase_flash(ser)
    program_flash(ser, fw)
    run_app(ser)

    print("\n✅ Firmware başarıyla yüklendi")
    ser.close()

if __name__ == "__main__":
    main()
