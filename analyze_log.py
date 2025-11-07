#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# analyze_log.py - p50/p95 agregati iz exp_log.csv

import csv, sys

f = sys.argv[1] if len(sys.argv) > 1 else "exp_log.csv"

def pctl(vals, p):
    if not vals: return None
    s = sorted(vals)
    k = int(round((p/100.0)*(len(s)-1)))
    return s[k]

rtts = {}
with open(f, newline="", encoding="utf-8") as fh:
    rd = csv.DictReader(fh)
    for row in rd:
        key = f"{row['proto']}|{row['reason']}"
        v = None
        if row['proto']=="MQTT" and row.get('mqtt_rtt_ms'):
            v = float(row['mqtt_rtt_ms'])
        if row['proto']=="CoAP" and row.get('coap_rtt_ms'):
            v = float(row['coap_rtt_ms'])
        if v is None: continue
        rtts.setdefault(key, []).append(v)

print("key,count,p50_ms,p95_ms")
for k, vals in rtts.items():
    print(f"{k},{len(vals)},{pctl(vals,50):.2f},{pctl(vals,95):.2f}")




FAKE = os.getenv("FAKE_SENSORS", "0") == "1"






