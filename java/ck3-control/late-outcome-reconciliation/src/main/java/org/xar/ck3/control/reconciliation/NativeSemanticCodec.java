package org.xar.ck3.control.reconciliation;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Semantic;
import org.xar.ck3.control.reconciliation.LateOutcome.WorldIdentity;

/** Selected view of existing ck3_take_semantic_snapshot_private_v1 structured_content.
 * Unrelated fields are retained in the original external receipt, not normalized through this view.
 */
public final class NativeSemanticCodec {
    public static final int MAXIMUM_READER_BYTES = 8 * 1024 * 1024;
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private NativeSemanticCodec() { }

    /** Caller supplies an actual lease bound. This parser does not enlarge shared map canonical JSON. */
    public static Semantic decode(byte[] rawStructuredContent, int maximumBytes) {
        StrictJson.require(maximumBytes >= 1 && maximumBytes <= MAXIMUM_READER_BYTES, "explicit reader byte budget");
        StrictJson.require(rawStructuredContent != null && rawStructuredContent.length >= 1
                && rawStructuredContent.length <= maximumBytes, "semantic receipt exceeds byte budget");
        JsonNode root;
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(rawStructuredContent)).toString();
            root = MAPPER.readTree(text);
        } catch (CharacterCodingException error) {
            throw new ContractViolationException("invalid semantic UTF-8", error);
        } catch (IOException error) {
            throw new ContractViolationException("invalid or duplicate semantic JSON", error);
        }
        object(root);
        StrictJson.require("native-headless".equals(StrictJson.text(root.get("backend_id")))
                && "injected-dll-named-pipe".equals(StrictJson.text(root.get("source"))), "native semantic producer required");
        JsonNode diagnostics = object(root.get("diagnostics"));
        StrictJson.require(StrictJson.integer(diagnostics.get("protocol_version"), 1, 1) == 1, "protocol version 1");
        JsonNode heartbeat = object(diagnostics.get("last_heartbeat"));
        StrictJson.require("heartbeat".equals(StrictJson.text(heartbeat.get("type"))), "actual heartbeat required");
        StrictJson.integer(heartbeat.get("protocol_version"), 1, 1);
        JsonNode owner = object(heartbeat.get("main_thread_query_mailbox_v1"));
        JsonNode played = object(root.get("played_character"));
        StrictJson.require("native".equals(StrictJson.text(played.get("source"))), "native played actor required");
        return new Semantic(SentinelCodec.i32(root.get("date_raw")), SentinelCodec.bool(root.get("paused")),
                SentinelCodec.bool(root.get("map_ready")), (int) StrictJson.integer(root.get("speed"), 1, 5),
                StrictJson.integer(root.get("native_revision"), 0, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(root.get("revision"), 0, StrictJson.MAX_SAFE_INTEGER), StrictJson.text(root.get("snapshot_id")),
                (int) StrictJson.integer(root.get("episode_character_id"), 1, Integer.MAX_VALUE),
                StrictJson.text(root.get("episode_run_id")), (int) StrictJson.integer(played.get("character_id"), 1, Integer.MAX_VALUE),
                SentinelCodec.bool(played.get("alive")), SentinelCodec.bool(root.get("one_life_terminal")),
                SentinelCodec.bool(root.get("episode_identity_pending")), SentinelCodec.bool(diagnostics.get("connected")),
                StrictJson.integer(diagnostics.get("connection_generation"), 1, StrictJson.MAX_SAFE_INTEGER),
                SentinelCodec.u32(diagnostics.get("bridge_pid")), SentinelCodec.nativeUInt64(heartbeat.get("sequence")),
                SentinelCodec.nativeUInt64(heartbeat.get("monotonic_ms")), SentinelCodec.u32(heartbeat.get("pid")),
                SentinelCodec.nativeUInt64(owner.get("pump_epochs")),
                SentinelCodec.nativeUInt64(owner.get("owner_verified_pump_epochs")),
                SentinelCodec.u32(owner.get("owner_tid")), SentinelCodec.u32(owner.get("current_tid")),
                new WorldIdentity(SentinelCodec.nativeUInt64(owner.get("game_state")),
                        SentinelCodec.nativeUInt64(owner.get("jomini_state"))),
                SentinelCodec.i32(owner.get("date_raw")), SentinelCodec.bool(owner.get("paused")),
                SentinelCodec.bool(owner.get("stamp_read_success")), SentinelCodec.bool(owner.get("stop")),
                SentinelCodec.u32(owner.get("failure")));
    }
    private static JsonNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "required semantic object missing/null"); return value;
    }
}
