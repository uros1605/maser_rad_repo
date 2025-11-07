#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coap_client.py - CoAP (DTLS) klijent sa merenjem RTT (echo resource).

import os, json, asyncio, time, uuid
from datetime import datetime

COAP_URL = os.getenv("COAP_URL", "coap://localhost/echo")
USE_DTLS = os.getenv("COAP_DTLS", "0") == "1"

async def coap_echo():
    import aiocoap
    proto = await aiocoap.Context.create_client_context()
    corr = uuid.uuid4().hex
    payload = json.dumps({"ts": datetime.utcnow().isoformat()+"Z", "corr": corr}).encode("utf-8")
    req = aiocoap.Message(code=aiocoap.POST, uri=COAP_URL, payload=payload)
    t0 = time.perf_counter()
    resp = await proto.request(req).response
    rtt = (time.perf_counter() - t0) * 1000.0
    if resp.code.is_successful():
        print(json.dumps({"ts": datetime.utcnow().isoformat()+"Z",
                          "proto": "CoAP",
                          "rtt_ms": rtt,
                          "corr": corr}, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(coap_echo())
