#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# controller.py - adaptivna politika (TLS/DTLS, QoS, interval), ping probe, log exp_log.csv, opcioni FORCE_HIGH.

import os, csv, time, json, subprocess
from datetime import datetime
from pathlib import Path

LOG = Path(os.getenv("EXP_LOG", "exp_log.csv"))
INTERVAL_BASE = float(os.getenv("BASE_INTERVAL", "5"))
FORCE_HIGH = os.getenv("FORCE_HIGH", "0") == "1"
RTT_BAD_MS = float(os.getenv("RTT_BAD_MS", "150"))
LUX_PRIVACY_LUX = float(os.getenv("PRIVACY_LUX", "10"))

def classify_privacy(snap):
    motion = snap.get("motion", 0) or 0
    lux = snap.get("lux", 100.0) or 100.0
    return "sensitive" if (motion and lux <= LUX_PRIVACY_LUX) else "normal"

def measure_mqtt_rtt():
    try:
        out = subprocess.check_output(["python3", "mqtt_client.py"], timeout=8).decode("utf-8").strip()
        js = json.loads(out.splitlines()[-1])
        return js.get("rtt_ms")
    except Exception:
        return None

def measure_coap_rtt():
    try:
        out = subprocess.check_output(["python3", "coap_client.py"], timeout=8).decode("utf-8").strip()
        js = json.loads(out.splitlines()[-1])
        return js.get("rtt_ms")
    except Exception:
        return None

def choose_policy(snap, rtt_mqtt, rtt_coap):
    privacy = classify_privacy(snap)
    net_rtt = min([v for v in [rtt_mqtt, rtt_coap] if v is not None], default=None)

    if FORCE_HIGH:
        return {"proto": "MQTT", "secure": True, "qos": 1, "interval": 1.0, "reason": "FORCE_HIGH", "privacy": privacy}

    secure = (privacy == "sensitive")
    qos = 1 if secure else 0

    if net_rtt is None:
        interval = INTERVAL_BASE
        proto = "MQTT"
        reason = "fallback"
    else:
        if net_rtt > RTT_BAD_MS:
            interval = INTERVAL_BASE * 3
            proto = "CoAP"
            qos = max(qos, 1)
            reason = "bad_net"
        else:
            interval = INTERVAL_BASE
            proto = "MQTT"
            reason = "good_net"

    return {"proto": proto, "secure": secure, "qos": qos, "interval": interval, "reason": reason, "privacy": privacy}

def send_payload(policy, snap):
    return True

def ensure_log_header():
    if not LOG.exists():
        with LOG.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ts","proto","secure","qos","interval","reason","privacy","mqtt_rtt_ms","coap_rtt_ms","temperature","humidity","lux","motion"])

def main_loop():
    ensure_log_header()
    while True:
        snap = json.loads(subprocess.check_output(["python3", "sensors.py"]).decode("utf-8"))
        rtt_mqtt = measure_mqtt_rtt()
        rtt_coap = measure_coap_rtt()
        pol = choose_policy(snap, rtt_mqtt, rtt_coap)
        send_payload(pol, snap)
        row = [datetime.utcnow().isoformat()+"Z", pol["proto"], int(pol["secure"]), pol["qos"], pol["interval"], pol["reason"], pol.get("privacy",""),
               rtt_mqtt, rtt_coap, snap.get("temperature"), snap.get("humidity"), snap.get("lux"), snap.get("motion")]
        with LOG.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
        time.sleep(pol["interval"])

if __name__ == "__main__":
    main_loop()
