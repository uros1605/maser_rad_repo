#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# sensors.py - citanje DHT22 (temp, hum), BH1750 (lux), PIR (motion).
# Vraca snapshot kao dict i (opciono) snima JSON na STDOUT.
# Podrzava realne senzore i "fake" mod za razvoj.

import os, json, time, sys
from datetime import datetime

FAKE = os.getenv("FAKE_SENSORS", "0") == "1"

def read_dht22(pin=4):
    if FAKE:
        return {"temperature": 22.0 + (time.time() % 10)/10.0, "humidity": 45.0}
    try:
        import Adafruit_DHT
        sensor = Adafruit_DHT.DHT22
        hum, temp = Adafruit_DHT.read_retry(sensor, pin)
        return {"temperature": float(temp) if temp is not None else None,
                "humidity": float(hum) if hum is not None else None}
    except Exception as e:
        return {"temperature": None, "humidity": None, "error_dht22": str(e)}

def read_bh1750(bus_id=1, addr=0x23):
    if FAKE:
        return {"lux": 150.0 + (time.time() % 5)*10.0}
    try:
        import smbus2
        bus = smbus2.SMBus(bus_id)
        data = bus.read_i2c_block_data(addr, 0x20, 2)  # One-time high-res mode
        lux = (data[0] << 8 | data[1]) / 1.2
        return {"lux": float(lux)}
    except Exception as e:
        return {"lux": None, "error_bh1750": str(e)}

def read_pir(pin=17):
    if FAKE:
        return {"motion": int(time.time()) % 2}
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)
        val = GPIO.input(pin)
        GPIO.cleanup()
        return {"motion": int(val)}
    except Exception as e:
        return {"motion": None, "error_pir": str(e)}

def snapshot():
    ts = datetime.utcnow().isoformat() + "Z"
    dht = read_dht22()
    bh = read_bh1750()
    pir = read_pir()
    out = {"ts": ts, **dht, **bh, **pir}
    return out

if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False))
