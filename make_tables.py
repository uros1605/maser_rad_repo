#!/usr/bin/env python3
# make_tables.py - pravi sazetke tabela iz exp_log.csv i actuator_log.csv
import pandas as pd
import numpy as np
from pathlib import Path

EXP = Path("exp_log.csv")
ACT = Path("actuator_log.csv")

def pct(xs, p):
    xs = np.sort(xs)
    if len(xs) == 0:
        return np.nan
    k = (len(xs) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)

def agg_tbl(sub):
    if len(sub) == 0:
        return pd.Series(dict(count=0, ok_pct=np.nan, p50=np.nan, p95=np.nan, mean=np.nan))
    l = sub["lat_s"].dropna().values
    return pd.Series(
        dict(
            count=len(sub),
            ok_pct=100 * sub["ok"].mean() if "ok" in sub else np.nan,
            p50=np.median(l) if len(l) else np.nan,
            p95=pct(l, 95) if len(l) else np.nan,
            mean=np.mean(l) if len(l) else np.nan,
        )
    )

def exp_tables():
    if not EXP.exists():
        print("No exp_log.csv found.")
        return
    df = pd.read_csv(EXP)
    # normalize types
    df["ok"] = df["ok"].astype(str).eq("True")
    for c in ["lat_s"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "mqtt_qos" in df.columns:
        df["mqtt_qos"] = df["mqtt_qos"].astype(str)
    else:
        df["mqtt_qos"] = "NA"

    # Table 1: RUN * {MQTT_Q0, MQTT_Q1, CoAPS}
    rows = []
    runs = sorted(df["run"].dropna().unique().tolist())
    for run in runs:
        combos = [
            ("MQTT_Q0", (df["run"].eq(run) & df["proto"].eq("mqtt_tls") & df["mqtt_qos"].eq("0"))),
            ("MQTT_Q1", (df["run"].eq(run) & df["proto"].eq("mqtt_tls") & df["mqtt_qos"].eq("1"))),
            ("CoAPS",   (df["run"].eq(run) & df["proto"].eq("coap_dtls"))),
        ]
        for name, mask in combos:
            sub = df[mask]
            s = agg_tbl(sub)
            s["run"] = run
            s["group"] = name
            rows.append(s)
    tbl1 = pd.DataFrame(rows)[["run", "group", "count", "ok_pct", "p50", "p95", "mean"]].sort_values(["run", "group"])
    tbl1.to_csv("table_run_proto.csv", index=False)
    tbl1_md = tbl1.copy()
    tbl1_md.columns = ["RUN", "Group", "Count", "OK (%)", "p50 (s)", "p95 (s)", "Mean (s)"]
    tbl1_md.to_markdown("table_run_proto.md", index=False)

    # Table 2: Globalno po protokolu/QoS
    rows = []
    for name, mask in [
        ("MQTT_Q0", (df["proto"].eq("mqtt_tls") & df["mqtt_qos"].eq("0"))),
        ("MQTT_Q1", (df["proto"].eq("mqtt_tls") & df["mqtt_qos"].eq("1"))),
        ("CoAPS",   (df["proto"].eq("coap_dtls"))),
    ]:
        sub = df[mask]
        s = agg_tbl(sub)
        s["group"] = name
        rows.append(s)
    tbl2 = pd.DataFrame(rows)[["group", "count", "ok_pct", "p50", "p95", "mean"]]
    tbl2.to_csv("table_global_proto.csv", index=False)
    tbl2_md = tbl2.copy()
    tbl2_md.columns = ["Group", "Count", "OK (%)", "p50 (s)", "p95 (s)", "Mean (s)"]
    tbl2_md.to_markdown("table_global_proto.md", index=False)

    print("Saved: table_run_proto.csv/.md, table_global_proto.csv/.md")

def act_tables():
    if not ACT.exists():
        print("Actuator table skipped (no actuator_log.csv).")
        return
    da = pd.read_csv(ACT)
    if "reason" in da.columns:
        share = da["reason"].value_counts(normalize=True) * 100.0
        share = share.rename("percent").to_frame()
        share.to_csv("table_actuator_reason_share.csv")
        share.to_markdown("table_actuator_reason_share.md")
        print("Saved: table_actuator_reason_share.csv/.md")
    else:
        print("Actuator table skipped (no 'reason' column).")

def main():
    exp_tables()
    act_tables()

if __name__ == "__main__":
    main()
