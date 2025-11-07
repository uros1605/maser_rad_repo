#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# plot_actuator.py - grafici za servo.

import csv
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np

def read_rows(path="actuator_log.csv"):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

rows = read_rows()
angles = [int(r["angle"]) for r in rows if r.get("angle")]
lux = [float(r["lux"]) for r in rows if r.get("lux")]
reasons = [r["reason"] for r in rows]

plt.figure()
plt.plot(angles); plt.ylabel("angle (deg)"); plt.title("Servo angle time-series"); plt.tight_layout(); plt.savefig("act_ts_angle.png", dpi=120)

plt.figure()
lx = [float(r["lux"]) for r in rows if r.get("lux")]
an = [int(r["angle"]) for r in rows if r.get("lux")]
plt.scatter(lx, an); plt.xlabel("lux"); plt.ylabel("angle"); plt.title("Angle vs Lux"); plt.tight_layout(); plt.savefig("act_angle_vs_lux.png", dpi=120)

plt.figure()
plt.hist(angles, bins=18); plt.xlabel("angle"); plt.ylabel("count"); plt.title("Angle histogram"); plt.tight_layout(); plt.savefig("act_hist_angle.png", dpi=120)

rs = sorted(set(reasons))
vals = []
for rr in rs:
    ang = [int(r["angle"]) for r in rows if r["reason"]==rr and r.get("angle")]
    vals.append([sum(ang)/len(ang) if ang else 0])
arr = np.array(vals)
plt.figure()
plt.imshow(arr, aspect="auto"); plt.yticks(range(len(rs)), rs); plt.xticks([0], ["avg angle"]); plt.colorbar(label="deg"); plt.title("Reason → avg angle"); plt.tight_layout(); plt.savefig("act_heat_reason_angle.png", dpi=120)

cnt = Counter(reasons)
plt.figure()
plt.bar(list(cnt.keys()), list(cnt.values())); plt.xticks(rotation=45, ha="right"); plt.title("Reason share"); plt.tight_layout(); plt.savefig("act_reason_share.png", dpi=120)
