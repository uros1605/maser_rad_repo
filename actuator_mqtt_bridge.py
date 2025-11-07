#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# actuator_mqtt_bridge.py - daljinska komanda preko MQTT/TLS.

import os, ssl, json, time, uuid, csv
from datetime import datetime
import paho.mqtt.client as mqtt
from pathlib import Path

TOPIC_CMD = os.getenv("ACT_TOPIC", "iot/actuator/servo/set")
BROKER = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "8883"))
TLS = os.getenv("MQTT_TLS", "1") == "1"
CA = os.getenv("MQTT_CA", "/etc/ssl/certs/ca-certificates.crt")
CERT = os.getenv("MQTT_CERT", "")
KEY = os.getenv("MQTT_KEY", "")
CLIENT_ID = f"act-bridge-{uuid.uuid4().hex[:8]}"
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

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        angle = int(data.get("angle", 90))
        reason = data.get("reason", "remote_cmd")
        set_servo_angle(angle)
        with LOG.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.utcnow().isoformat()+"Z", reason, angle, None, None])
    except Exception as e:
        print("Bad message:", e)

def main():
    ensure_log_header()
    c = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5)
    if TLS:
        ctx = ssl.create_default_context(cafile=CA if CA else None)
        if CERT and KEY:
            ctx.load_cert_chain(certfile=CERT, keyfile=KEY)
        c.tls_set_context(ctx)
    c.connect(BROKER, PORT, keepalive=60)
    c.subscribe(TOPIC_CMD, qos=1)
    c.on_message = on_message
    c.loop_forever()

if __name__ == "__main__":
    main()
