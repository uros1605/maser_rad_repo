#!/usr/bin/env python3
# policy_tuner.py - baseline vs quantum-inspired (SA) optimizacija pragova
import csv, json, random, math, statistics as stats

CSV="exp_log.csv"

def load_rows():
    rows=[]
    with open(CSV) as f:
        rd=csv.DictReader(f)
        for r in rd:
            try:
                rows.append({
                    "run": r["run"],
                    "proto": r["proto"],
                    "qos": int(r.get("mqtt_qos","1") or 1),
                    "ok": (r["ok"]=="True"),
                    "lat": float(r["lat_s"]),
                    "rtt": float(r["rt_avg_ms"]) if r.get("rt_avg_ms") not in [None,"","nan"] else None,
                    "loss": float(r["rt_loss_pct"]) if r.get("rt_loss_pct") not in [None,"","nan"] else None,
                    "tx": float(r["tx_rate_bps"]) if r.get("tx_rate_bps") not in [None,"","nan"] else None,
                })
            except:
                pass
    return [r for r in rows if r["rtt"] is not None and r["loss"] is not None]

def np_percentile(xs,p):
    xs=sorted(xs)
    if not xs: return float('nan')
    k=(len(xs)-1)*p/100; f=int(k); c=min(f+1,len(xs)-1)
    return xs[f] if f==c else xs[f]+(xs[c]-xs[f])*(k-f)

def evaluate_policy(rows, rtt_low, rtt_mid, loss_mid):
    """
    Pravilo (primer, u skladu sa controller idejom):
      - rtt<rtt_low i loss=0 → MQTT QoS0 (interval 1s)
      - rtt<rtt_mid i loss<=loss_mid → MQTT QoS1 (interval 2s)
      - else → MQTT QoS1 (interval 4s)  [teška mreža]
    U ovoj evaluaciji koristimo postojeće latencije/ok/tx iz loga kao proxy (replay).
    """
    lats=[]; oks=0; n=0; txs=[]
    for r in rows:
        n+=1
        lats.append(r["lat"])
        oks += 1 if r["ok"] else 0
        if r["tx"] is not None: txs.append(r["tx"])
    if not lats: return 1e9, {}

    p95 = np_percentile(lats,95)
    ok_rate = 100.0*oks/max(1,n)
    med_tx = stats.median(txs) if txs else 0.0

    # cilj: minimizuj (w1*p95 - w2*ok_rate + w3*med_tx)
    w1,w2,w3 = 1.0, 0.5, 1e-4
    J = w1*p95 - w2*ok_rate + w3*med_tx
    return J, {"p95":p95,"ok%":ok_rate,"med_tx":med_tx}

def baseline_search(rows):
    best=None
    for rtt_low in [20,40,60]:
        for rtt_mid in [80,120,180]:
            for loss_mid in [0.5,1.0,2.0,3.0]:
                J,metrics=evaluate_policy(rows,rtt_low,rtt_mid,loss_mid)
                cand={"rtt_low":rtt_low,"rtt_mid":rtt_mid,"loss_mid":loss_mid,"J":J,**metrics}
                if best is None or cand["J"]<best["J"]:
                    best=cand
    return best

def sa_optimize(rows, iters=2000, T0=2.0, alpha=0.995):
    choices = {
        "rtt_low": [20,30,40,50,60],
        "rtt_mid": [80,100,120,150,180,220],
        "loss_mid": [0.5,1.0,2.0,3.0,5.0],
    }
    state = {
        "rtt_low": random.choice(choices["rtt_low"]),
        "rtt_mid": random.choice(choices["rtt_mid"]),
        "loss_mid": random.choice(choices["loss_mid"]),
    }
    J,_ = evaluate_policy(rows, state["rtt_low"], state["rtt_mid"], state["loss_mid"])
    best = {**state, "J":J}
    T=T0
    for _ in range(iters):
        key = random.choice(list(choices.keys()))
        val = random.choice(choices[key])
        new = dict(state); new[key]=val
        J2,_ = evaluate_policy(rows, new["rtt_low"], new["rtt_mid"], new["loss_mid"])
        dE = J2 - J
        if dE < 0 or random.random() < math.exp(-dE/max(1e-6,T)):
            state, J = new, J2
            if J < best["J"]:
                best = {**state, "J":J}
        T *= alpha
    _,metrics = evaluate_policy(rows, best["rtt_low"], best["rtt_mid"], best["loss_mid"])
    best.update(metrics)
    return best

def main():
    rows = load_rows()
    if not rows:
        print("No rows with RTT/loss present in CSV.")
        return
    base = baseline_search(rows)
    sa   = sa_optimize(rows)

    with open("policy_baseline.json","w") as f: json.dump(base, f, indent=2)
    with open("policy_quantum_inspired.json","w") as f: json.dump(sa, f, indent=2)

    print("Baseline:", json.dumps(base, indent=2))
    print("Quantum-inspired (SA):", json.dumps(sa, indent=2))
    print("Saved: policy_baseline.json, policy_quantum_inspired.json")

if __name__=="__main__":
    main()
