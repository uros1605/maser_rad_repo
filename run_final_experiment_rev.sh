#!/usr/bin/env bash
# run_final_experiment_rev.sh - A/B/C/D obrnut redosled (tc/netem).
# Primer: IFACE=lo DURATION=600 ./run_final_experiment_rev.sh

set -euo pipefail

IFACE="${IFACE:-eth0}"
DURATION="${DURATION:-300}"
RATE="${RATE:-256kbit}"
DELAY_MS="${DELAY_MS:-200}"
LOSS_PCT="${LOSS_PCT:-2}"

echo "##### START FINAL EXPERIMENT (REVERSED) #####"
sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
sudo tc qdisc add dev "$IFACE" root handle 1: netem delay ${DELAY_MS}ms loss ${LOSS_PCT}% seed $(od -An -tu8 -N8 /dev/urandom | tr -d ' ')
sudo tc qdisc add dev "$IFACE" parent 1: handle 10: tbf rate $RATE burst 4Kb latency 3070ms

SCENARIOS=("D" "C" "B" "A")
for S in "${SCENARIOS[@]}"; do
  echo "=== RUN=$S | env: MQTT_QOS=0 FORCE_HIGH=0 | ${DURATION}s ==="
  case "$S" in
    A) export MQTT_QOS=0 FORCE_HIGH=0 MQTT_TLS=0 ;;
    B) export MQTT_QOS=1 FORCE_HIGH=0 MQTT_TLS=1 ;;
    C) export MQTT_QOS=0 FORCE_HIGH=1 MQTT_TLS=1 ;;
    D) export MQTT_QOS=1 FORCE_HIGH=1 MQTT_TLS=1 ;;
  esac
  timeout "${DURATION}"s python3 controller.py || true
done

sudo tc qdisc del dev "$IFACE" root 2>/dev/null || true
echo "##### DONE #####"
