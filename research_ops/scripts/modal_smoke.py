"""Optional *billable* private Modal endpoint smoke: run only with approved cap.

Requires `pip install openai`. Reads endpoint+auth from env; does not touch FlowBoard.
    MODAL_ENDPOINT_URL=https://<actual-host>
    MODAL_MODEL_NAME=<actual-model-id-from-v1/models>
    MODAL_PROXY_TOKEN_ID=<id>
    MODAL_PROXY_TOKEN_SECRET=<secret>
    AFTERCLICK_SMOKE_MAX_CALLS=1
This does not impose a server-side dollar limit; obtain approval and monitor billing.
"""

import json
import os
import time
from openai import OpenAI


def main():
    url = os.environ["MODAL_ENDPOINT_URL"].rstrip("/")
    model = os.environ["MODAL_MODEL_NAME"]
    key = f'{os.environ["MODAL_PROXY_TOKEN_ID"]}.{os.environ["MODAL_PROXY_TOKEN_SECRET"]}'
    max_calls = int(os.environ.get("AFTERCLICK_SMOKE_MAX_CALLS", "1"))
    if not 1 <= max_calls <= 20:
        raise ValueError("smoke call count must be between 1 and 20")
    client = OpenAI(base_url=f"{url}/v1", api_key=key, timeout=90.0, max_retries=0)
    # Deliberately innocuous short JSON task: no production or FlowBoard mutation.
    prompt = 'Return a JSON object exactly {"action":"finish","reason":"no browser action needed"}.'
    print(json.dumps({"target_hostname": url, "model": model, "planned_calls": max_calls}))
    for i in range(max_calls):
        start = time.monotonic()
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=128,
            )
            out = r.choices[0].message.content or ""
            try:
                parsed = json.loads(out)
                parse_ok = isinstance(parsed, dict) and parsed.get("action") == "finish"
            except (ValueError, TypeError):
                parse_ok = False
            usage = r.usage
            print(json.dumps({"call":i, "status":"returned", "latency_ms":round(1000*(time.monotonic()-start)),
                "json_expected_ok":parse_ok, "input_tokens":getattr(usage,"prompt_tokens",None),
                "output_tokens":getattr(usage,"completion_tokens",None),
                "model":r.model, "finish_reason":r.choices[0].finish_reason}))
        except Exception as exc:
            # Do not print exception string: some SDKs embed URLs or request metadata.
            print(json.dumps({"call":i, "status":"failed", "error_type":type(exc).__name__,
                "billing_uncertain": True}))
            break

if __name__ == "__main__":
    main()
