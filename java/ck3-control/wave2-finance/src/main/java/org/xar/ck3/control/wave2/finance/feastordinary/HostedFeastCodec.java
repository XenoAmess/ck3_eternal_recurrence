package org.xar.ck3.control.wave2.finance.feastordinary;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.Activity;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.CompletionStamp;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampAbsent;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampObserved;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampUnobserved;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.Terminal;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.TerminalAbsent;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.TerminalObserved;

/** Strict raw-token codec for the pure hosted_activities leaf; it grants no native provenance. */
public final class HostedFeastCodec {
    // A valid 64-row leaf with all optional fields and 63 escaped astral codepoints
    // per activity key can exceed 64 KiB. Keep the byte guard independent of row count.
    public static final int MAX_BYTES = 131_072;
    private static final Set<String> IDENTITY = Set.of("activity_id", "host_character_id", "activity_type_key");
    private static final Set<String> TERMINAL = Set.of("terminal_flags_observed", "native_completed", "native_invalidated");
    private static final Set<String> STAMP = Set.of("native_completion_stamp_observed", "native_completion_stamp_raw");
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(12).maxNumberLength(128).build()).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    private HostedFeastCodec() { }

    public static HostedFeastActivities decode(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > MAX_BYTES) throw new IllegalArgumentException("hosted activities byte budget exceeded or empty");
        final JsonNode root;
        try {
            String source = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            root = JSON.readTree(source);
        } catch (IOException exception) {
            throw new IllegalArgumentException("hosted activities are not strict UTF-8 JSON", exception);
        }
        return decodeTree(root);
    }

    /** Boundary-only reuse after another strict JSON parser; token kinds are never re-encoded. */
    public static HostedFeastActivities decodeTree(JsonNode root) {
        if (root == null || !root.isArray() || root.size() > HostedFeastActivities.MAX_ACTIVITIES) {
            throw new IllegalArgumentException("private feast hosted identities malformed");
        }
        ArrayList<Activity> rows = new ArrayList<>(root.size());
        for (JsonNode row : root) {
            if (!row.isObject()) throw new IllegalArgumentException("private feast hosted identity malformed");
            Set<String> keys = new HashSet<>(); row.fieldNames().forEachRemaining(keys::add);
            boolean hasTerminal = keys.contains("terminal_flags_observed");
            boolean hasStamp = keys.contains("native_completion_stamp_observed");
            Set<String> expected = new HashSet<>(IDENTITY);
            if (hasTerminal) expected.addAll(TERMINAL);
            if (hasStamp) expected.addAll(STAMP);
            if (!keys.equals(expected)) throw new IllegalArgumentException("private feast hosted identity malformed");
            long activityId = positiveU32(row.get("activity_id"), "activity_id");
            long actorId = positiveU32(row.get("host_character_id"), "host_character_id");
            JsonNode type = row.get("activity_type_key");
            if (!type.isTextual()) throw new IllegalArgumentException("private feast hosted identity malformed");
            Terminal terminal = new TerminalAbsent();
            if (hasTerminal) {
                if (!bool(row.get("terminal_flags_observed"), "terminal_flags_observed")) {
                    throw new IllegalArgumentException("private feast hosted terminal flags malformed");
                }
                terminal = new TerminalObserved(bool(row.get("native_completed"), "native_completed"),
                        bool(row.get("native_invalidated"), "native_invalidated"));
            }
            CompletionStamp stamp = new StampAbsent();
            if (hasStamp) {
                boolean observed = bool(row.get("native_completion_stamp_observed"), "native_completion_stamp_observed");
                JsonNode raw = row.get("native_completion_stamp_raw");
                if (observed) {
                    if (!raw.isIntegralNumber()) throw new IllegalArgumentException("private feast native completion stamp malformed");
                    stamp = new StampObserved(raw.bigIntegerValue());
                } else {
                    if (!raw.isNull()) throw new IllegalArgumentException("private feast native completion stamp malformed");
                    stamp = new StampUnobserved();
                }
            }
            rows.add(new Activity(activityId, actorId, type.textValue(), terminal, stamp));
        }
        return new HostedFeastActivities(rows);
    }

    public static byte[] encode(HostedFeastActivities value) {
        ArrayNode root = JSON.createArrayNode();
        for (Activity activity : value.activities()) {
            ObjectNode row = root.addObject();
            row.put("activity_id", activity.activityId()); row.put("host_character_id", activity.hostCharacterId());
            row.put("activity_type_key", activity.activityTypeKey());
            if (activity.terminal() instanceof TerminalObserved terminal) {
                row.put("terminal_flags_observed", true); row.put("native_completed", terminal.completed());
                row.put("native_invalidated", terminal.invalidated());
            }
            if (activity.completionStamp() instanceof StampObserved stamp) {
                row.put("native_completion_stamp_observed", true); row.put("native_completion_stamp_raw", stamp.raw());
            } else if (activity.completionStamp() instanceof StampUnobserved) {
                row.put("native_completion_stamp_observed", false); row.putNull("native_completion_stamp_raw");
            }
        }
        try {
            byte[] result = JSON.writeValueAsBytes(root);
            if (result.length > MAX_BYTES) throw new IllegalArgumentException("hosted activities output byte budget exceeded");
            return result;
        } catch (IOException exception) {
            throw new IllegalStateException("hosted activities encoding failed", exception);
        }
    }

    private static boolean bool(JsonNode value, String name) {
        if (value == null || !value.isBoolean()) throw new IllegalArgumentException(name + " must be boolean");
        return value.booleanValue();
    }
    private static long positiveU32(JsonNode value, String name) {
        if (value == null || !value.isIntegralNumber()) throw new IllegalArgumentException(name + " must be a positive uint32 integer");
        BigInteger raw = value.bigIntegerValue();
        if (raw.signum() <= 0 || raw.compareTo(BigInteger.valueOf(HostedFeastActivities.MAX_U32)) > 0) {
            throw new IllegalArgumentException(name + " must be a positive uint32 integer");
        }
        return raw.longValueExact();
    }
}
