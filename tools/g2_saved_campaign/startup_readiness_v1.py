"""Keep one startup readiness control pending across exact read-only loading errors.

The caller supplies its current text relay explicitly. No provider module is
selected implicitly. Every attempt is a new ClientSession.call_tool request. No camera, pause, advance
or business command is submitted here. Unknown errors/timeouts retain the halt.
"""
import asyncio
import json
import time

LOADING_ERROR = ("Error executing tool ck3_take_semantic_snapshot_private_v1: "
    "native game state is not available yet; CK3 may still be loading or may not have entered a map")


def exact_loading(row, semantic):
    request, result = row.get("request"), row.get("result")
    if (row.get("client_error") is not None or not isinstance(request, dict)
            or request.get("tool") != semantic or request.get("arguments") != {}
            or not isinstance(result, dict) or result.get("is_error") is not True
            or result.get("result_type") != "complete"
            or result.get("structured_content", result.get("structuredContent")) is not None):
        return False
    content = result.get("content")
    return (isinstance(content, list) and len(content) == 1
            and isinstance(content[0], dict) and content[0].get("type") == "text"
            and content[0].get("text") == LOADING_ERROR)


async def startup_readiness_call(queue, session, request, path, env, *, relay_compact, sleep=asyncio.sleep):
    semantic, q, outbox = env["SEMANTIC"], env["Q"], env["OUTBOX"]
    atomic, now, decoded = env["atomic"], env["now"], env["decoded"]
    if (request.get("tool") != semantic or request.get("arguments", {}) != {}
            or request.get("command") is not None
            or getattr(queue, "cold_readiness_verified", False)
            or queue.initial_camera is not None or queue.checkpoint_bootstrap_verified):
        raise ValueError("loading wait is only the first cold readiness semantic")
    queue.check_before(semantic, {})
    sequence = request.get("sequence")
    if type(sequence) is not int or sequence != queue.next_sequence:
        raise ValueError("one current unused readiness request required")
    response = outbox / f"{sequence:04d}-1-result.json"
    inflight = q / f"INFLIGHT-{sequence:04d}.json"
    if response.exists() or inflight.exists():
        raise FileExistsError("startup readiness already attempted")
    context = {"sequence": sequence, "tool": semantic, "arguments": {}, "request_file": str(path),
        "at_utc": now().isoformat(), "scope": "cold-start-readiness-only", "business_credit": 0,
        "outer_sequence_consumed": False, "original_P01_response_replayed": False}
    atomic(env["N"] / "CURRENT-REQUEST-P37.json", context, replace=True, limit=16384)
    atomic(inflight, context, limit=16384)
    attempt = 0
    while True:
        queue.guard()
        attempt += 1
        started, mono = now().isoformat(), time.monotonic()
        queue.current_attempt = None
        try:
            result = await session.call_tool(semantic, {}, read_timeout_seconds=queue.call_budget(semantic))
            dumped = result.model_dump(mode="json")
            client_error = None
        except Exception as error:
            dumped, client_error = None, repr(error)
        row = {"started_at_utc": started, "ended_at_utc": now().isoformat(),
            "elapsed_seconds": time.monotonic() - mono, "request": request, "result": dumped,
            "startup_readiness_attempt": attempt, "new_MCP_request_per_attempt": True,
            "jsonrpc_request_id": None, "jsonrpc_request_id_availability": "not exposed by CallToolResult",
            "mcp_result_projection_json_utf8_bytes": len(json.dumps(dumped, ensure_ascii=False,
                separators=(",", ":")).encode("utf-8"))}
        if client_error is not None:
            row["client_error"] = client_error
        attempt_path = q / f"READINESS-{sequence:04d}-{attempt:06d}-result.json"
        atomic(attempt_path, row)
        queue.current_attempt = {"request": request, "row": row, "response": str(attempt_path)}
        if exact_loading(row, semantic):
            atomic(q / f"READINESS-{sequence:04d}-{attempt:06d}-loading.json", {
                "status": "startup_readiness_unavailable", "source_response": str(attempt_path),
                "outer_sequence_consumed": False, "new_business_credit": 0,
                "retry_only_tool": semantic, "retry_delay_seconds": 5,
                "camera_pause_advance_business_calls": 0, "whole_session_deadline": None}, limit=16384)
            print("READINESS_LOADING", sequence, attempt, flush=True)
            await sleep(5)
            continue
        # Any other MCP error is decoded by the unchanged production function
        # and remains a genuine halt; it is never treated as loading/success.
        try:
            body = decoded(row)
            queue.check_after(semantic, {}, body)
        except Exception:
            # Match the ordinary queue's observable failure contract: Root gets
            # the actual failed outer response as well as its attempt receipt.
            atomic(response, row)
            queue.current_attempt = {"request": request, "row": row, "response": str(response)}
            raise
        queue.consume_sequence(request)  # Exactly once, only after real readiness qualifies.
        atomic(response, row)
        queue.current_attempt = {"request": request, "row": row, "response": str(response)}
        relay_compact(response, env["display_projection"](row, body))
        atomic(q / f"{sequence:04d}-after-result.json", {
            "at_utc": row["ended_at_utc"], "request": str(path), "response": str(response),
            "tool": semantic, "actual_status": "cold_readiness_verified",
            "loading_attempts": attempt - 1, "new_business_credit": 0}, limit=16384)
        print("DONE", sequence, semantic, "readiness attempts", attempt, flush=True)
        return body, response
