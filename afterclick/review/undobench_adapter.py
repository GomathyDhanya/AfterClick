"""Separate native-tool agent plugin for pinned UndoBench, no built-in network access.

An externally approved Supervisor transport must be injected. Default construction
fails closed. Official tasks/tools/scoring stay unchanged; interventions unavailable
in those tools cannot be silently emulated as staging.
"""

import json
import time
from pathlib import Path

from undobench import AgentResponse, AgentTurn, UndoBenchAgent


def validate_arguments(arguments, schema):
    import jsonschema

    jsonschema.validate(arguments, schema)


class AfterClickQwenAgent(UndoBenchAgent):
    def __init__(self, transport=None, journal=None, max_calls=8):
        if transport is None:
            raise ValueError("APPROVED_BUDGETED_TRANSPORT_REQUIRED: paid mode disabled")
        if not 1 <= max_calls <= 10:
            raise ValueError("Bounded generation cap required")
        self.transport = transport
        self.journal = Path(journal) if journal else None
        self.max_calls = max_calls

    def record(self, value):
        if self.journal:
            with self.journal.open("a") as f:
                f.write(json.dumps(value, allow_nan=False) + "\n")
                f.flush()

    def run(self, task, tools, context):
        began = time.monotonic()
        messages = [
            {"role": "system", "content": context.system_prompt},
            {"role": "user", "content": context.user_prompt},
        ]
        turns = []
        seen = set()
        inputs = outputs = invocations = 0
        error = None
        generation_requests = 0
        schemas = {
            t["function"]["name"]: t["function"]["parameters"] for t in task.tool_definitions
        }
        for turn in range(min(context.max_turns, self.max_calls)):
            request = dict(
                model="AfterClick",
                messages=messages,
                tools=task.tool_definitions,
                tool_choice="auto",
                temperature=0,
                max_tokens=512,
                stream=False,
                chat_template_kwargs={"enable_thinking": False},
            )
            self.record(dict(event="request", turn=turn, request=request))
            try:
                generation_requests += 1
                response = self.transport(
                    request
                )  # Only caller-supplied capped approved or mock transport.
                self.record(dict(event="response", turn=turn, response=response))
                message = response["choices"][0]["message"]
                usage = response.get("usage", {})
                inputs += usage.get("prompt_tokens", 0)
                outputs += usage.get("completion_tokens", 0)
                calls = message.get("tool_calls", [])
                messages.append(message)
                results = []
                if not calls:
                    turns.append(
                        AgentTurn(
                            turn_index=turn + 1, role="assistant", content=message.get("content")
                        )
                    )
                    break
                for call in calls:
                    identity = call["id"]
                    if identity in seen:
                        raise ValueError("Duplicate native tool-call ID")
                    seen.add(identity)
                    fn = call["function"]["name"]
                    arguments = json.loads(call["function"]["arguments"])
                    if fn not in tools or fn not in schemas:
                        raise ValueError("Unauthorized tool name")
                    validate_arguments(arguments, schemas[fn])
                    invocations += 1
                    try:
                        result = tools[fn](**arguments)
                    except Exception as exc:
                        result = dict(error_type=type(exc).__name__, error=str(exc))
                    messages.append(
                        dict(role="tool", tool_call_id=identity, content=json.dumps(result))
                    )
                    results.append(dict(tool_call_id=identity, result=result))
                turns.append(
                    AgentTurn(
                        turn_index=turn + 1,
                        role="assistant",
                        tool_calls=calls,
                        tool_results=results,
                    )
                )
            except Exception as exc:
                error = type(exc).__name__ + ": " + str(exc)
                break
        else:
            error = "Generation budget exhausted; no completion evidence"
        return AgentResponse(
            status="FAILED" if error else "SUCCESS",
            messages=messages,
            turns=turns,
            tool_invocations_count=invocations,
            llm_calls_count=generation_requests,
            prompt_tokens=inputs,
            completion_tokens=outputs,
            error=error,
            latency_ms=1000 * (time.monotonic() - began),
        )
