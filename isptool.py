#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time
import sys
import os

# ===============================
# CONFIG
# ===============================
BAUDRATE = 115200
PACKET_SIZE = 64
TIMEOUT = 2

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
    return bytes([
        v & 0xFF,
        (v >> 8) & 0xFF,
        (v >> 16) & 0xFF,
        (v >> 24) & 0xFF
    ])

def read_exact(ser, n, timeout=3):
    buf = b""
    start = time.time()
    while len(buf) < n:
        if ser.in_waiting:
            buf += ser.read(n - len(buf))
        elif time.time() - start > timeout:
            return None
        else:
            time.sleep(0.01)
    return buf

def send_packet(ser, data):
    if len(data) != 64:
        raise ValueError("Packet must be 64 bytes")
    ser.write(data)
    ser.flush()

def recv_packet(ser):
    return read_exact(ser, 64)

# ===============================
# PACKET BUILDERS
# ===============================

def pkt_simple(cmd):
    p = bytearray(64)
    p[0:4] = u32(cmd)
    return p

def pkt_sync(no):
    p = bytearray(64)
    p[0:4] = u32(CMD_SYNC_PACKNO)
    p[8:12] = u32(no)
    return p

def pkt_update_first(addr, size, data):
    p = bytearray(64)
    p[0:4] = u32(CMD_UPDATE_APROM)
    p[8:12] = u32(addr)
    p[12:16] = u32(size)
    p[16:16+len(data)] = data
    return p

def pkt_update_next(data):
    p = bytearray(64)
    p[0:4] = u32(CMD_UPDATE_APROM)
    p[8:8+len(data)] = data
    return p

# ===============================
# ISP CORE
# ===============================

def connect(ser):
    print("[*] CONNECT gönderiliyor...")
    send_packet(ser, pkt_simple(CMD_CONNECT))
    r = recv_packet(ser)
    if not r:
        return False
    print("[OK] Bootloader cevap verdi")
    return True

def sync_packno(ser):
    print("[*] PACKET NO sync...")
    send_packet(ser, pkt_sync(1))
    r = recv_packet(ser)
    return r is not None

def get_device_id(ser):
    print("[*] Device ID alınıyor...")
    send_packet(ser, pkt_simple(CMD_GET_DEVICEID))
    r = recv_packet(ser)
    if not r:
        return None
    dev = int.from_bytes(r[8:12], "little")
    print(f"[OK] Device ID: 0x{dev:08X}")
    return dev

def erase_chip(ser):
    print("[*] Flash siliniyor...")
    send_packet(ser, pkt_simple(CMD_ERASE_ALL))
    r = recv_packet(ser)
    if not r:
        print("!! ERASE timeout")
        return False
    print("[OK] Flash silindi")
    return True

def program_flash(ser, data):
    size = len(data)
    print(f"[*] Yazılıyor: {size} byte")

    # İlk paket
    first = pkt_update_first(0x00000000, size, data[:48])
    send_packet(ser, first)
    recv_packet(ser)

    offset = 48
    while offset < size:
        chunk = data[offset:offset+56]
        pkt = pkt_update_next(chunk)
        send_packet(ser, pkt)
        r = recv_packet(ser)
        if not r:
            print("!! Yazma hatası")
            return False
        offset += len(chunk)
        print(f"  → {offset}/{size}")

    print("[OK] Yazma tamamlandı")
    return True

def run_app(ser):
    print("[*] RUN_APROM")
    send_packet(ser, pkt_simple(CMD_RUN_APROM))

# ===============================
# MAIN
# ===============================

def main():

    port = "/dev/ttyACM0"
    fw = "NuvotonM26x-Bootloader-Test.bin"

    with open(fw, "rb") as f:
        data = f.read()

    ser = serial.Serial(
        port,
        BAUDRATE,
        timeout=0.1,
        rtscts=False,
        dsrdtr=False
    )

    print("\n=== M263 ISP ===")
    print("RESET'e bas → 1 saniye içinde başlar\n")

    time.sleep(0.5)

    if not connect(ser):
        print("Bootloader bulunamadı")
        return

    sync_packno(ser)
    get_device_id(ser)
    erase_chip(ser)
    program_flash(ser, data)
    run_app(ser)

    print("\n✔ Güncelleme tamamlandı")
    ser.close()

if __name__ == "__main__":
    main()
