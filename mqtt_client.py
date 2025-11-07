#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mqtt_client.py - MQTT(TLS) klijent sa merenjem RTT poruke.

import os, ssl, time, json, uuid
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "8883"))
TOPIC_PUB = os.getenv("MQTT_TOPIC_PUB", "iot/edge/ping")
TOPIC_ECHO = os.getenv("MQTT_TOPIC_ECHO", "iot/edge/echo")
CLIENT_ID = f"edge-mqtt-{uuid.uuid4().hex[:8]}"
TLS = os.getenv("MQTT_TLS", "1") == "1"
CA = os.getenv("MQTT_CA", "/etc/ssl/certs/ca-certificates.crt")
CERT = os.getenv("MQTT_CERT", "")
KEY = os.getenv("MQTT_KEY", "")
QOS = int(os.getenv("MQTT_QOS", "0"))
TIMEOUT = float(os.getenv("MQTT_TIMEOUT", "5"))

rtt_store = {}

def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe(TOPIC_ECHO, qos=QOS)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        return
    corr = data.get("corr")
    t0 = rtt_store.pop(corr, None)
    if t0 is not None:
        rtt = (time.perf_counter() - t0) * 1000.0
        print(json.dumps({"ts": datetime.utcnow().isoformat()+"Z",
                          "proto": "MQTT",
                          "qos": QOS,
                          "rtt_ms": rtt,
                          "corr": corr}, ensure_ascii=False))

def build_client():
    client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_message = on_message
    if TLS:
        ctx = ssl.create_default_context(cafile=CA if CA else None)
        if CERT and KEY:
            ctx.load_cert_chain(certfile=CERT, keyfile=KEY)
        client.tls_set_context(ctx)
    return client

def main():
    client = build_client()
    client.connect(BROKER, PORT, keepalive=30)
    client.loop_start()
    corr = uuid.uuid4().hex
    payload = {"ts": datetime.utcnow().isoformat()+"Z", "corr": corr, "ping": 1}
    rtt_store[corr] = time.perf_counter()
    client.publish(TOPIC_PUB, json.dumps(payload), qos=QOS)
    t_end = time.time() + TIMEOUT
    while time.time() < t_end and corr in rtt_store:
        time.sleep(0.01)
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
