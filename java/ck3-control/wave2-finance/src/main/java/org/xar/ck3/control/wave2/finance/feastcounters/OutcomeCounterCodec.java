package org.xar.ck3.control.wave2.finance.feastcounters;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterValues.Delta;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterValues.Observed;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterValues.Presence;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterValues.Projection;

/** Strict counter leaf and the exact six-field pure consumer value projection. */
public final class OutcomeCounterCodec {
    public static final int MAX_BYTES = 16_384;
    private static final Set<String> COUNTERS = Set.of("prestige_raw", "stress_points", "reveler_present", "reveler_xp_raw");
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(8).maxNumberLength(128).build()).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private OutcomeCounterCodec() { }

    public static OutcomeCounterValues decodeCounters(byte[] raw) { return counters(parse(raw)); }
    /** Strict new field-only projection, never an entire extensible SDK payload/envelope. */
    public static Optional<OutcomeCounterValues> decodeNativeCounterFieldProjection(byte[] raw) {
        JsonNode root = parse(raw);
        if (!root.isObject()) throw new IllegalArgumentException("native counter field projection requires an object");
        if (root.size() != 0) fields(root, Set.of("outcome_values"));
        if (!root.has("outcome_values")) return Optional.empty();
        // _parse_payload calls _outcome_values whenever the key exists: explicit null is invalid here.
        return Optional.of(counters(root.get("outcome_values")));
    }
    public static byte[] encodeNativeCounterFieldProjection(Optional<OutcomeCounterValues> values) {
        ObjectNode root = JSON.createObjectNode(); values.ifPresent(value -> root.set("outcome_values", counterNode(value)));
        return bytes(root);
    }
    /** Legacy pre_outcome_values null must stay distinct from an observed four-null map. */
    public static Optional<OutcomeCounterValues> decodeStoredSeed(byte[] raw) { return group(parse(raw)); }
    public static byte[] encodeStoredSeed(Optional<OutcomeCounterValues> values) {
        return bytes(values.isPresent() ? counterNode(values.orElseThrow()) : JSON.getNodeFactory().nullNode());
    }
    public static Projection decodeProjection(byte[] raw) {
        JsonNode root = parse(raw); fields(root, Set.of("before", "after"));
        return new Projection(group(root.get("before")), group(root.get("after")));
    }
    public static byte[] encodeCounters(OutcomeCounterValues values) { return bytes(counterNode(values)); }
    public static byte[] encodeProjectionInput(Projection projection) {
        ObjectNode root = JSON.createObjectNode();
        root.set("before", projection.before().isPresent() ? counterNode(projection.before().orElseThrow()) : JSON.getNodeFactory().nullNode());
        root.set("after", projection.after().isPresent() ? counterNode(projection.after().orElseThrow()) : JSON.getNodeFactory().nullNode());
        return bytes(root);
    }
    public static byte[] encodeProjection(Projection projection) {
        ObjectNode root = JSON.createObjectNode();
        root.set("pre_start_outcome_values", counterNode(projection.beforeValues())); root.set("outcome_values", counterNode(projection.afterValues()));
        Delta delta = projection.changes(); ObjectNode changes = root.putObject("counter_changes");
        putBig(changes, "prestige_raw", delta.prestigeRaw()); putBig(changes, "stress_points", delta.stressPoints());
        putBig(changes, "reveler_xp_raw", delta.revelerXpRaw());
        if (projection.presenceTransition().isPresent()) {
            var transition = projection.presenceTransition().orElseThrow(); ObjectNode presence = root.putObject("reveler_presence_transition");
            presence.put("before", transition.before()); presence.put("after", transition.after());
        } else root.putNull("reveler_presence_transition");
        Observed flags = projection.observed(); ObjectNode observed = root.putObject("counter_values_observed");
        observed.put("prestige_raw", flags.prestigeRaw()); observed.put("stress_points", flags.stressPoints());
        observed.put("reveler_present", flags.revelerPresent()); observed.put("reveler_xp_raw", flags.revelerXpRaw());
        root.put("counter_changes_attributed_to_feast", false);
        return bytes(root);
    }

    private static Optional<OutcomeCounterValues> group(JsonNode value) {
        if (value == null) throw new IllegalArgumentException("counter group is required, null means unobserved");
        return value.isNull() ? Optional.empty() : Optional.of(counters(value));
    }
    private static OutcomeCounterValues counters(JsonNode root) {
        fields(root, COUNTERS);
        Optional<Long> prestige = signed64(root.get("prestige_raw"));
        Optional<Long> xp = signed64(root.get("reveler_xp_raw"));
        JsonNode stressRaw = root.get("stress_points");
        Optional<Integer> stress = stressRaw.isNull() ? Optional.empty()
                : Optional.of(Math.toIntExact(integer(stressRaw, Integer.MIN_VALUE, Integer.MAX_VALUE)));
        JsonNode presentRaw = root.get("reveler_present"); Presence presence;
        if (presentRaw.isNull()) presence = Presence.UNKNOWN;
        else {
            if (!presentRaw.isBoolean()) throw new IllegalArgumentException("private feast reveler presence malformed");
            presence = presentRaw.booleanValue() ? Presence.PRESENT : Presence.ABSENT;
        }
        return new OutcomeCounterValues(prestige, stress, presence, xp);
    }
    private static ObjectNode counterNode(OutcomeCounterValues values) {
        ObjectNode node = JSON.createObjectNode();
        if (values.prestigeRaw().isPresent()) node.put("prestige_raw", values.prestigeRaw().orElseThrow()); else node.putNull("prestige_raw");
        if (values.stressPoints().isPresent()) node.put("stress_points", values.stressPoints().orElseThrow()); else node.putNull("stress_points");
        switch (values.revelerPresent()) { case UNKNOWN -> node.putNull("reveler_present"); case ABSENT -> node.put("reveler_present", false); case PRESENT -> node.put("reveler_present", true); }
        if (values.revelerXpRaw().isPresent()) node.put("reveler_xp_raw", values.revelerXpRaw().orElseThrow()); else node.putNull("reveler_xp_raw");
        return node;
    }
    private static Optional<Long> signed64(JsonNode value) {
        return value.isNull() ? Optional.empty() : Optional.of(integer(value, Long.MIN_VALUE, Long.MAX_VALUE));
    }
    private static long integer(JsonNode value, long low, long high) {
        if (!value.isIntegralNumber()) throw new IllegalArgumentException("counter must be an integer token");
        BigInteger raw = value.bigIntegerValue();
        if (raw.compareTo(BigInteger.valueOf(low)) < 0 || raw.compareTo(BigInteger.valueOf(high)) > 0) throw new IllegalArgumentException("counter outside original native width");
        return raw.longValueExact();
    }
    private static void fields(JsonNode root, Set<String> expected) {
        if (root == null || !root.isObject()) throw new IllegalArgumentException("counter object malformed");
        Set<String> actual = new HashSet<>(); root.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(expected)) throw new IllegalArgumentException("counter fields malformed");
    }
    private static JsonNode parse(byte[] raw) {
        if (raw == null || raw.length == 0 || raw.length > MAX_BYTES) throw new IllegalArgumentException("counter input byte budget exceeded or empty");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode root = JSON.readTree(text);
            if (root == null) throw new IllegalArgumentException("counter input empty");
            return root;
        } catch (IOException exception) { throw new IllegalArgumentException("counter input is not strict UTF-8 JSON", exception); }
    }
    private static void putBig(ObjectNode node, String key, Optional<BigInteger> value) {
        if (value.isPresent()) node.put(key, value.orElseThrow()); else node.putNull(key);
    }
    private static byte[] bytes(JsonNode node) {
        try {
            byte[] result = JSON.writeValueAsBytes(node);
            if (result.length > MAX_BYTES) throw new IllegalArgumentException("counter output byte budget exceeded");
            return result;
        } catch (IOException exception) { throw new IllegalStateException("counter output failed", exception); }
    }
}
