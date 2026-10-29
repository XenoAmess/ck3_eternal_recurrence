package org.xar.ck3.control.wave2.runtime.clockreader;

import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Evidence;
import org.xar.ck3.control.reconciliation.LateOutcome.Read;
import org.xar.ck3.control.reconciliation.LateOutcome.ReadKind;
import org.xar.ck3.control.reconciliation.LateOutcome.SemanticRead;
import org.xar.ck3.control.reconciliation.LateOutcome.StatusRead;
import org.xar.ck3.control.reconciliation.LateOutcome.UnavailableRead;
import org.xar.ck3.control.reconciliation.NativeSemanticCodec;
import org.xar.ck3.control.reconciliation.SentinelCodec;

/** Consumes the preserved original Queue CallToolResult row, never an ACK as native stop evidence. */
public final class ClockMcpRowDecoder {
    public static final String STATUS_TOOL = "ck3_read_tactical_daily_sentinel_status_private_v1";
    public static final String SEMANTIC_TOOL = "ck3_take_semantic_snapshot_private_v1";
    public static final String STATUS_STEP = "research-query-tactical-daily-sentinel-v1";
    private ClockMcpRowDecoder() { }
    public static Read decode(byte[] rawRow, ReadKind kind, Evidence evidence, int maximumNativeBytes) {
        JsonNode row = ClockRawJson.parse(rawRow, 32 * 1024 * 1024);
        JsonNode request = object(row.get("request"));
        StrictJson.require(evidence.sequence() == StrictJson.integer(request.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER), "original Queue sequence mismatch");
        StrictJson.require(tool(kind).equals(StrictJson.text(request.get("tool"))), "fixed original tool mismatch");
        StrictJson.require(object(request.get("arguments")).isEmpty(), "fixed readers accept no arbitrary arguments");
        if (row.has("client_error")) {
            StrictJson.require(row.get("replay_allowed") != null && row.get("replay_allowed").isBoolean()
                    && !row.get("replay_allowed").booleanValue(), "unknown transport outcome must forbid replay");
            return new UnavailableRead(evidence, kind, bounded(StrictJson.text(row.get("client_error"))));
        }
        JsonNode result = object(row.get("result"));
        // The pinned model_dump producer always emits this discriminator, including completed errors.
        StrictJson.require("complete".equals(StrictJson.text(result.get("result_type"))), "completed original MCP result required");
        JsonNode isError = result.get("is_error");
        StrictJson.require(isError != null && isError.isBoolean(), "exact MCP is_error boolean");
        if (isError.booleanValue()) { return new UnavailableRead(evidence, kind, "original_mcp_error_preserved"); }
        JsonNode content = result.get("content");
        StrictJson.require(content != null && content.isArray() && content.size() == 1, "one original text body required");
        JsonNode text = object(content.get(0));
        StrictJson.require("text".equals(StrictJson.text(text.get("type"))), "native reader text content required");
        byte[] textBody = ClockRawJson.textJson(text.get("text"), maximumNativeBytes);
        // Raw slicing avoids DecimalNode -> toString silently changing malformed 1.0 to integer 1.
        byte[] structured = ClockRawJson.subtree(rawRow, "result", "structured_content");
        StrictJson.require(structured.length <= maximumNativeBytes, "native structured payload exceeds byte budget");
        if (kind == ReadKind.CURRENT_SEMANTIC_FRAME) {
            var first = NativeSemanticCodec.decode(structured, maximumNativeBytes);
            var second = NativeSemanticCodec.decode(textBody, maximumNativeBytes);
            StrictJson.require(first.equals(second), "MCP text and structured semantic facts disagree");
            return new SemanticRead(evidence, first);
        }
        JsonNode body = ClockRawJson.parse(structured, maximumNativeBytes);
        JsonNode textObject = ClockRawJson.parse(textBody, maximumNativeBytes);
        statusEnvelope(body); statusEnvelope(textObject);
        var first = SentinelCodec.decode(ClockRawJson.subtree(structured, "tactical_daily_sentinel"));
        var second = SentinelCodec.decode(ClockRawJson.subtree(textBody, "tactical_daily_sentinel"));
        StrictJson.require(first.equals(second), "MCP text and structured sentinel facts disagree");
        return new StatusRead(evidence, first);
    }
    public static String tool(ReadKind kind) {
        java.util.Objects.requireNonNull(kind);
        return kind == ReadKind.CURRENT_SENTINEL_STATUS ? STATUS_TOOL : SEMANTIC_TOOL;
    }
    private static void statusEnvelope(JsonNode body) {
        object(body); StrictJson.require(STATUS_STEP.equals(StrictJson.text(body.get("step"))), "fixed status step");
        StrictJson.trueValue(body.get("accepted"));
        StrictJson.require("available".equals(StrictJson.text(body.get("status"))), "actual available native status required");
    }
    private static JsonNode object(JsonNode value) { StrictJson.require(value != null && value.isObject(), "required legacy object"); return value; }
    private static String bounded(String text) {
        return text.codePointCount(0, text.length()) <= 512 ? text : text.substring(0, text.offsetByCodePoints(0, 512));
    }
}
