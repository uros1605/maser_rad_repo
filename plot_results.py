#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# plot_results.py - osnovni grafici p50/p95 (MQTT/CoAP), png.

import csv, statistics
import matplotlib.pyplot as plt

def read_rows(path="exp_log.csv"):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def median(vals):
    s = [v for v in vals if v is not None]
    return statistics.median(s) if s else None

def pctl(vals, p):
    s = sorted([v for v in vals if v is not None])
    if not s: return None
    k = int(round((p/100.0)*(len(s)-1)))
    return s[k]

rows = read_rows()
def series(proto, col):
    out = []
    for r in rows:
        if r["proto"] == proto and r[col]:
            out.append(float(r[col]))
    return out

mqtt = series("MQTT", "mqtt_rtt_ms")
coap = series("CoAP", "coap_rtt_ms")

labels = ["MQTT p50", "MQTT p95", "CoAP p50", "CoAP p95"]
values = [pctl(mqtt,50) or 0, pctl(mqtt,95) or 0, pctl(coap,50) or 0, pctl(coap,95) or 0]

plt.figure()
plt.bar(labels, values)
plt.ylabel("RTT (ms)")
plt.title("Osnovni RTT rezultati")
plt.tight_layout()
plt.savefig("proto_p95.png", dpi=120)

plt.figure()
plt.bar(["p50","p95"], [pctl(mqtt,50) or 0, pctl(mqtt,95) or 0])
plt.ylabel("RTT (ms)")
plt.title("MQTT RTT")
plt.tight_layout()
plt.savefig("mqtt_p95.png", dpi=120)

plt.figure()
plt.bar(["median"], [median(mqtt) or 0])
plt.ylabel("RTT (ms)")
plt.title("MQTT median")
plt.tight_layout()
plt.savefig("mqtt_p50.png", dpi=120)
