#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt

b = json.load(open('policy_baseline.json'))
q = json.load(open('policy_quantum_inspired.json'))

labels = ['p95 (s) ↓','ok% ↑','median tx (bps) ↓']
bvals  = [b.get('p95',0), b.get('ok%',0), b.get('med_tx',0)]
qvals  = [q.get('p95',0), q.get('ok%',0), q.get('med_tx',0)]

x = range(len(labels))
plt.figure()
plt.bar([i-0.15 for i in x], bvals, width=0.3, label='Baseline')
plt.bar([i+0.15 for i in x], qvals, width=0.3, label='Quantum-inspired')
plt.xticks(list(x), labels)
plt.title('Policy comparison: baseline vs quantum-inspired')
plt.legend()
plt.tight_layout()
plt.savefig('policy_compare.png')
print('Generated: policy_compare.png')
