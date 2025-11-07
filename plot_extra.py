#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# plot_extra.py - 15 dodatnih grafika iz exp_log.csv

import csv, statistics
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np

def read_rows(path="exp_log.csv"):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

rows = read_rows()

def colflt(row, name):
    try:
        return float(row[name]) if row[name] else None
    except:
        return None

def collect(proto, name):
    return [colflt(r, name) for r in rows if r["proto"]==proto and r.get(name)]

def cdf(vals):
    s = sorted([v for v in vals if v is not None])
    if not s: return [], []
    x, y = [], []
    n = len(s)
    for i, v in enumerate(s):
        x.append(v); y.append((i+1)/n)
    return x, y

def save(name):
    plt.tight_layout()
    plt.savefig(name, dpi=120)
    plt.clf()

# 1 CDF MQTT
x,y = cdf(collect("MQTT","mqtt_rtt_ms"))
plt.plot(x,y); plt.xlabel("RTT (ms)"); plt.ylabel("CDF"); plt.title("MQTT CDF")
save("extra_mqtt_cdf.png")

# 2 CDF CoAP
x,y = cdf(collect("CoAP","coap_rtt_ms"))
plt.plot(x,y); plt.xlabel("RTT (ms)"); plt.ylabel("CDF"); plt.title("CoAP CDF")
save("extra_coap_cdf.png")

# 3 boxplot MQTT vs CoAP
data = [collect("MQTT","mqtt_rtt_ms"), collect("CoAP","coap_rtt_ms")]
plt.boxplot([ [v for v in d if v is not None] for d in data ], labels=["MQTT","CoAP"])
plt.ylabel("RTT (ms)"); plt.title("Boxplot RTT")
save("extra_boxplot_proto.png")

# 4 OK% (<200ms)
def ok_rate(vals, thr=200.0):
    s = [v for v in vals if v is not None]
    if not s: return 0
    return 100.0*sum(1 for v in s if v<thr)/len(s)
mqtt_ok = ok_rate(collect("MQTT","mqtt_rtt_ms"))
coap_ok = ok_rate(collect("CoAP","coap_rtt_ms"))
plt.bar(["MQTT","CoAP"], [mqtt_ok, coap_ok]); plt.ylabel("OK%"); plt.title("OK% (<200ms)")
save("extra_ok_rate.png")

# 5 scatter lux vs mqtt_rtt
x = [colflt(r,"lux") for r in rows if r["proto"]=="MQTT"]
y = [colflt(r,"mqtt_rtt_ms") for r in rows if r["proto"]=="MQTT"]
x = [v for v in x if v is not None]; y = [v for v in y if v is not None]
plt.scatter(x, y); plt.xlabel("lux"); plt.ylabel("MQTT RTT (ms)"); plt.title("Lux vs MQTT RTT")
save("extra_scatter_lux_mqtt.png")

# 6 time-series RTT (index vs value)
rtt = [colflt(r,"mqtt_rtt_ms") if r["proto"]=="MQTT" else colflt(r,"coap_rtt_ms") for r in rows]
rtt = [v for v in rtt if v is not None]
plt.plot(rtt); plt.ylabel("RTT (ms)"); plt.title("RTT time-series")
save("extra_ts_rtt.png")

# 7 heatmap p50 po reason
reasons = sorted(set(r["reason"] for r in rows))
protos = ["MQTT","CoAP"]
grid = []
for proto in protos:
    row = []
    for reason in reasons:
        vals = [colflt(r,"mqtt_rtt_ms") if proto=="MQTT" else colflt(r,"coap_rtt_ms")
                for r in rows if r["proto"]==proto and r["reason"]==reason]
        vs = [v for v in vals if v is not None]
        p50 = sorted(vs)[int(0.5*(len(vs)-1))] if vs else 0
        row.append(p50)
    grid.append(row)
arr = np.array(grid)
plt.imshow(arr, aspect="auto")
plt.xticks(range(len(reasons)), reasons, rotation=45, ha="right"); plt.yticks(range(len(protos)), protos)
plt.colorbar(label="p50 RTT (ms)"); plt.title("Heatmap p50 po razlogu")
save("extra_heatmap_p50_reason.png")

# 8 heatmap p95 po reason
grid95 = []
for proto in protos:
    row = []
    for reason in reasons:
        vals = [colflt(r,"mqtt_rtt_ms") if proto=="MQTT" else colflt(r,"coap_rtt_ms")
                for r in rows if r["proto"]==proto and r["reason"]==reason]
        vs = [v for v in vals if v is not None]
        p95 = sorted(vs)[int(0.95*(len(vs)-1))] if vs else 0
        row.append(p95)
    grid95.append(row)
arr = np.array(grid95)
plt.imshow(arr, aspect="auto")
plt.xticks(range(len(reasons)), reasons, rotation=45, ha="right"); plt.yticks(range(len(protos)), protos)
plt.colorbar(label="p95 RTT (ms)"); plt.title("Heatmap p95 po razlogu")
save("extra_heatmap_p95_reason.png")

# 9 histogram MQTT
vals = [v for v in collect("MQTT","mqtt_rtt_ms") if v is not None]
plt.hist(vals, bins=30); plt.xlabel("RTT (ms)"); plt.ylabel("count"); plt.title("MQTT histogram")
save("extra_hist_mqtt.png")

# 10 histogram CoAP
vals = [v for v in collect("CoAP","coap_rtt_ms") if v is not None]
plt.hist(vals, bins=30); plt.xlabel("RTT (ms)"); plt.ylabel("count"); plt.title("CoAP histogram")
save("extra_hist_coap.png")

# 11 bar reason share
cnt = Counter(r["reason"] for r in rows)
plt.bar(list(cnt.keys()), list(cnt.values())); plt.xticks(rotation=45, ha="right"); plt.title("Reason share")
save("extra_reason_share.png")

# 12 violin plot RTT
vals_m = [v for v in collect("MQTT","mqtt_rtt_ms") if v is not None]
vals_c = [v for v in collect("CoAP","coap_rtt_ms") if v is not None]
plt.violinplot([vals_m, vals_c], showmeans=True); plt.xticks([1,2], ["MQTT","CoAP"]); plt.ylabel("RTT (ms)"); plt.title("Violin RTT")
save("extra_violin.png")

# 13 QQ-plot (requires scipy); fallback to skip if not installed
try:
    from scipy import stats
    vals = [v for v in collect("MQTT","mqtt_rtt_ms") if v is not None]
    if len(vals)>5:
        (osm, osr), (slope, intercept, r) = stats.probplot(vals, dist="norm")
        plt.scatter(osm, osr); plt.title("QQ MQTT"); save("extra_qq_mqtt.png")
except Exception:
    pass

# 14 scatter humidity vs coap_rtt
x = [colflt(r,"humidity") for r in rows if r["proto"]=="CoAP"]
y = [colflt(r,"coap_rtt_ms") for r in rows if r["proto"]=="CoAP"]
x = [v for v in x if v is not None]; y = [v for v in y if v is not None]
plt.scatter(x,y); plt.xlabel("humidity"); plt.ylabel("CoAP RTT (ms)"); plt.title("Humidity vs CoAP RTT")
save("extra_scatter_hum_coap.png")

# 15 QoS over index
qos = []
for r in rows:
    try:
        qos.append(int(r["qos"]))
    except:
        qos.append(0)
plt.plot(range(len(qos)), qos); plt.ylabel("QoS"); plt.title("QoS kroz vreme")
save("extra_qos_ts.png")
