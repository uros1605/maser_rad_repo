#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# servo_smart_blind.py - pametna žaluzina (PIR+lux-ugao), log actuator_log.csv.

import os, time, csv, json
from datetime import datetime
from pathlib import Path
import subprocess

LOG = Path(os.getenv("ACT_LOG", "actuator_log.csv"))
FAKE = os.getenv("FAKE_SERVO", "0") == "1"

def ensure_log_header():
    if not LOG.exists():
        with LOG.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["ts","reason","angle","lux","motion"])

def set_servo_angle(angle_deg, pin=18, freq=50):
    if FAKE:
        return True
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, freq)
        pwm.start(0)
        duty = 2 + (angle_deg/18.0)
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)
        pwm.stop()
        GPIO.cleanup()
        return True
    except Exception as e:
        print("Servo error:", e)
        return False

def decide_angle(lux, motion):
    if not motion:
        return 90, "no_presence"
    if lux is None:
        return 90, "no_lux"
    if lux < 50:
        return 30, "dark_open"
    if lux > 300:
        return 150, "bright_close"
    angle = 30 + (lux - 50) * (120.0 / 250.0)
    return int(max(0, min(180, angle))), "linear_map"

def read_snapshot():
    try:
        snap = json.loads(subprocess.check_output(["python3", "sensors.py"]).decode("utf-8"))
        return snap
    except Exception:
        return {"lux": None, "motion": 0}

def loop():
    ensure_log_header()
    while True:
        s = read_snapshot()
        lux = s.get("lux")
        motion = s.get("motion") or 0
        angle, reason = decide_angle(lux, motion)
        set_servo_angle(angle)
        with LOG.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.utcnow().isoformat()+"Z", reason, angle, lux, motion])
        time.sleep(2)

if __name__ == "__main__":
    loop()
