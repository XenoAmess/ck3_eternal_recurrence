package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Original Character.GetPlayerHeir data only. Neither a modal permit nor a continuation writer. */
public final class NativePlayerHeirObservation12004 {
    public static final String EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final String COMPONENT = "player_heir_candidate_v1";
    public static final String GETTER_RVA = "0x289DCC0";
    public static final int MAX_BYTES = 1_048_576;

    public enum State { MISSING, EXPLICIT_NULL, UNBOUND, UNAVAILABLE, FIXTURE, OBSERVED_NULL, LIVING_CANDIDATE, DEAD_CANDIDATE }
    /** All Character/House/Dynasty identities are native signed32 bit patterns; only -1 is null. */
    public record Core(int dateRaw, boolean paused, int speed, int localPlayerId, boolean mapReady,
            boolean hasPlayedCharacter, int playedCharacterId, boolean playedCharacterAlive) {
        public Core { StrictJson.require(speed >= 0, "nonnegative native speed required"); }
    }
    public record Lineage(int houseId, int dynastyId) { }
    public record Observation(boolean available, String unavailableReason, boolean sourceFixture,
            boolean originalGetterSourceBound, Core before, Core after, boolean getterObserved,
            boolean candidatePresent, int actorCharacterId, int candidateCharacterId, boolean candidateAlive,
            boolean identityAndFrameStable, boolean lineageAvailable, Lineage candidateLineage,
            String lineageUnavailableReason) {
        public Observation {
            Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(candidateLineage);
            reason(unavailableReason); reason(lineageUnavailableReason);
        }
    }
    public record Component(BigInteger nativeRevision, boolean parentFrameBound, Observation observation) {
        public Component { positive(nativeRevision); Objects.requireNonNull(observation); }
    }
    /** Public and native revisions remain separate even when their usual values happen to coincide. */
    public record Frame(String snapshotId, BigInteger publicRevision, BigInteger nativeRevision,
            int dateRaw, int actorCharacterId, int localPlayerId) {
        public Frame {
            StrictJson.text(snapshotId); Objects.requireNonNull(publicRevision); positive(nativeRevision);
            StrictJson.require(publicRevision.signum() >= 0 && publicRevision.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "uint64 public revision required");
            StrictJson.require(actorCharacterId != -1 && localPlayerId >= 0, "actual local actor required");
        }
    }
    public record Parsed(State state, Component component) {
        public Parsed {
            Objects.requireNonNull(state);
            StrictJson.require((state == State.MISSING || state == State.EXPLICIT_NULL) == (component == null),
                    "component presence/state mismatch");
        }
    }
    public enum OptionalStatus { MISSING, PARSED, UNKNOWN }
    /** Optional root syntax status is deliberately separate from strict source/liveness qualification. */
    public record OptionalParsed(OptionalStatus status, String reason, Observation observation) {
        public OptionalParsed {
            Objects.requireNonNull(status); NativePlayerHeirObservation12004.reason(reason);
            StrictJson.require(status != OptionalStatus.PARSED || reason == null && observation != null,
                    "parsed optional component must retain its actual observation");
        }
    }

    private NativePlayerHeirObservation12004() { }

    /** Consumes the original existing root result; malformed optional data throws and never grants a fact. */
    public static Parsed parse(byte[] rootResult, Frame expected) {
        Objects.requireNonNull(expected);
        JsonNode result = StrictJson.parse(rootResult, MAX_BYTES);
        StrictJson.require("available".equals(text(result, "status")), "completed available root result required");
        JsonNode binding = field(result, "binding");
        StrictJson.require(expected.snapshotId().equals(text(binding, "snapshot_id"))
                && expected.publicRevision().equals(uint(binding, "revision", false))
                && expected.nativeRevision().equals(uint(binding, "native_revision", true))
                && expected.dateRaw() == signed(binding, "date_raw"), "original root/public frame mismatch");
        return parseRoot(result, expected);
    }

    /** Exact original C++ result token, with its real PlanningReadReceipt frame supplied independently by Root. */
    public static Parsed parseNativeResult(byte[] originalResult, Frame actualReceiptFrame) {
        Objects.requireNonNull(actualReceiptFrame);
        ObjectNode result = StrictJson.object(StrictJson.parse(originalResult, MAX_BYTES),
                Set.of("step", "accepted", "status", "query_sequence", "snapshot_revision", "campaign_root_context", "backend_id"));
        StrictJson.require("query-campaign-root-context-v1".equals(text(result, "step"))
                && bool(result, "accepted") && "available".equals(text(result, "status"))
                && "native-headless".equals(text(result, "backend_id"))
                && actualReceiptFrame.nativeRevision().equals(uint(result, "snapshot_revision", true)), "original native root token/frame differs");
        uint(result, "query_sequence", true);
        return parseRoot(result, actualReceiptFrame);
    }
    private static Parsed parseRoot(JsonNode result, Frame expected) {
        JsonNode root = field(result, "campaign_root_context");
        StrictJson.require("available".equals(text(root, "status"))
                && expected.nativeRevision().equals(uint(root, "snapshot_revision", true))
                && expected.dateRaw() == signed(root, "date_raw")
                && expected.actorCharacterId() == signed(root, "player_character_id")
                && expected.localPlayerId() == signed(root, "local_player_id")
                && bool(root, "player_character_alive"), "original native root/actor frame mismatch");
        StrictJson.trueValue(field(field(root, "readiness"), "same_frame_ready"));
        StrictJson.require(EXE_SHA256.equals(text(field(root, "provenance"), "executable_sha256")
                .toLowerCase(java.util.Locale.ROOT)), "exact .4 root source required");
        if (!root.has(COMPONENT)) return new Parsed(State.MISSING, null);
        if (root.get(COMPONENT).isNull()) return new Parsed(State.EXPLICIT_NULL, null);
        Component component = component(root.get(COMPONENT), root);
        return new Parsed(classify(component, expected), component);
    }

    /** Python's existing optional-root syntax producer: unavailable or unbound H never invalidates the whole root. */
    public static OptionalParsed parseOptionalComponent(JsonNode original, JsonNode normalizedRoot) {
        if (original == null || original.isNull())
            return new OptionalParsed(OptionalStatus.MISSING, "optional_component_not_produced", null);
        try {
            Component component = component(original, normalizedRoot); Observation observation = component.observation();
            if (!component.parentFrameBound() || !"available".equals(text(normalizedRoot, "status"))
                    || !optionalCoreBound(observation.before(), normalizedRoot)
                    || !optionalCoreBound(observation.after(), normalizedRoot)
                    || observation.actorCharacterId() != signed(normalizedRoot, "player_character_id"))
                return new OptionalParsed(OptionalStatus.UNKNOWN, "native_parent_frame_not_bound", observation);
            return new OptionalParsed(OptionalStatus.PARSED, null, observation);
        } catch (IllegalArgumentException failure) {
            String message = failure.getMessage() == null ? "malformed_native_candidate_observation" : failure.getMessage();
            int count = message.codePointCount(0, message.length());
            if (count > 1024) message = message.substring(0, message.offsetByCodePoints(0, 1024));
            return new OptionalParsed(OptionalStatus.UNKNOWN, message, null);
        }
    }

    /** Returns a detached original JSON value or the exact local SDK unknown diagnostic; never a source permit. */
    public static JsonNode normalizeOptionalComponent(JsonNode original, JsonNode normalizedRoot) {
        OptionalParsed parsed = parseOptionalComponent(original, normalizedRoot);
        if (original == null || original.isNull()) return com.fasterxml.jackson.databind.node.NullNode.instance;
        if (parsed.observation() != null) return original.deepCopy();
        return StrictJson.object().put("SDK_parse_status", "unknown").put("unavailable_reason", parsed.reason());
    }

    private static Component component(JsonNode raw, JsonNode root) {
        ObjectNode node;
        try {
            node = StrictJson.object(raw, Set.of("schema_version", "snapshot_revision", "query_kind", "executable_sha256",
                    "getter_rva", "parent_frame_bound", "observation"));
            StrictJson.require(StrictJson.integer(field(node, "schema_version"), 1, 1) == 1
                    && "campaign_root_context_v1".equals(text(node, "query_kind")) && GETTER_RVA.equals(text(node, "getter_rva"))
                    && EXE_SHA256.equals(text(node, "executable_sha256").toLowerCase(java.util.Locale.ROOT))
                    && uint(node, "snapshot_revision", true).equals(uint(root, "snapshot_revision", true))
                    && EXE_SHA256.equals(text(field(root, "provenance"), "executable_sha256").toLowerCase(java.util.Locale.ROOT)),
                    "component source/revision mismatch");
            bool(node, "parent_frame_bound");
        } catch (IllegalArgumentException failure) {
            throw new IllegalArgumentException("component_source_or_parent_revision_mismatch", failure);
        }
        return new Component(uint(node, "snapshot_revision", true), bool(node, "parent_frame_bound"), observation(field(node, "observation")));
    }
    private static boolean optionalCoreBound(Core core, JsonNode root) {
        return core.dateRaw() == signed(root, "date_raw") && core.localPlayerId() == signed(root, "local_player_id")
                && core.playedCharacterId() == signed(root, "player_character_id");
    }

    private static State classify(Component c, Frame f) {
        Observation o = c.observation();
        if (!c.parentFrameBound() || !matches(o.before(), f) || !matches(o.after(), f)
                || !o.before().equals(o.after()) || o.actorCharacterId() != f.actorCharacterId()) return State.UNBOUND;
        if (o.sourceFixture()) return State.FIXTURE;
        if (!o.available() || !o.originalGetterSourceBound() || !o.getterObserved()
                || !o.identityAndFrameStable() || o.unavailableReason() != null) return State.UNAVAILABLE;
        if (!o.candidatePresent()) {
            StrictJson.require(o.candidateCharacterId() == -1 && !o.candidateAlive() && !o.lineageAvailable(),
                    "observed-null candidate carried positive facts");
            return State.OBSERVED_NULL;
        }
        StrictJson.require(o.candidateCharacterId() != -1 && o.candidateCharacterId() != f.actorCharacterId(),
                "native selected candidate identity invalid");
        if (o.lineageAvailable()) {
            StrictJson.require(o.lineageUnavailableReason() == null
                    && (o.candidateLineage().houseId() != -1 || o.candidateLineage().dynastyId() == -1),
                    "native lineage known-none/reason mismatch");
        }
        return o.candidateAlive() ? State.LIVING_CANDIDATE : State.DEAD_CANDIDATE;
    }

    /** Round-trip preserves native wire types, flags and null; decoded data never acquires source custody. */
    public static byte[] encodeComponent(Component c) {
        Objects.requireNonNull(c);
        ObjectNode out = StrictJson.object(); out.put("schema_version", 1).put("snapshot_revision", c.nativeRevision())
                .put("query_kind", "campaign_root_context_v1").put("executable_sha256", EXE_SHA256)
                .put("getter_rva", GETTER_RVA).put("parent_frame_bound", c.parentFrameBound());
        Observation o = c.observation(); ObjectNode n = out.putObject("observation");
        n.put("available", o.available()).put("source_fixture", o.sourceFixture())
                .put("original_getter_source_bound", o.originalGetterSourceBound()).put("getter_observed", o.getterObserved())
                .put("candidate_present", o.candidatePresent()).put("actor_character_id", o.actorCharacterId())
                .put("candidate_character_id", o.candidateCharacterId()).put("candidate_alive", o.candidateAlive())
                .put("identity_and_frame_stable", o.identityAndFrameStable()).put("lineage_available", o.lineageAvailable());
        nullable(n, "unavailable_reason", o.unavailableReason()); nullable(n, "lineage_unavailable_reason", o.lineageUnavailableReason());
        n.set("before", coreNode(o.before())); n.set("after", coreNode(o.after()));
        n.putObject("candidate_lineage").put("house_id", o.candidateLineage().houseId()).put("dynasty_id", o.candidateLineage().dynastyId());
        return StrictJson.canonical(out, MAX_BYTES);
    }

    private static Observation observation(JsonNode raw) {
        ObjectNode o;
        try {
            o = StrictJson.object(raw, Set.of("available", "unavailable_reason", "source_fixture", "original_getter_source_bound",
                    "before", "after", "getter_observed", "candidate_present", "actor_character_id", "candidate_character_id",
                    "candidate_alive", "identity_and_frame_stable", "lineage_available", "candidate_lineage", "lineage_unavailable_reason"));
            for (String key : Set.of("available", "source_fixture", "original_getter_source_bound", "getter_observed",
                    "candidate_present", "candidate_alive", "identity_and_frame_stable", "lineage_available")) bool(o, key);
            signed(o, "actor_character_id"); signed(o, "candidate_character_id");
            nullable(o, "unavailable_reason"); nullable(o, "lineage_unavailable_reason");
        } catch (IllegalArgumentException failure) { throw new IllegalArgumentException("malformed_native_candidate_observation", failure); }
        ObjectNode lineage;
        try {
            lineage = StrictJson.object(field(o, "candidate_lineage"), Set.of("house_id", "dynasty_id"));
            signed(lineage, "house_id"); signed(lineage, "dynasty_id");
        } catch (IllegalArgumentException failure) { throw new IllegalArgumentException("malformed_native_candidate_lineage", failure); }
        return new Observation(bool(o, "available"), nullable(o, "unavailable_reason"), bool(o, "source_fixture"),
                bool(o, "original_getter_source_bound"), core(field(o, "before")), core(field(o, "after")), bool(o, "getter_observed"),
                bool(o, "candidate_present"), signed(o, "actor_character_id"), signed(o, "candidate_character_id"),
                bool(o, "candidate_alive"), bool(o, "identity_and_frame_stable"), bool(o, "lineage_available"),
                new Lineage(signed(lineage, "house_id"), signed(lineage, "dynasty_id")), nullable(o, "lineage_unavailable_reason"));
    }
    private static Core core(JsonNode raw) {
        try {
            ObjectNode c = StrictJson.object(raw, Set.of("date_raw", "paused", "speed", "local_player_id", "map_ready",
                    "has_played_character", "played_character_id", "played_character_alive"));
            return new Core(signed(c, "date_raw"), bool(c, "paused"), (int) StrictJson.integer(field(c, "speed"), 0, Integer.MAX_VALUE),
                    signed(c, "local_player_id"), bool(c, "map_ready"), bool(c, "has_played_character"),
                    signed(c, "played_character_id"), bool(c, "played_character_alive"));
        } catch (IllegalArgumentException failure) { throw new IllegalArgumentException("malformed_native_core_frame", failure); }
    }
    private static ObjectNode coreNode(Core c) {
        ObjectNode n = StrictJson.object(); return n.put("date_raw", c.dateRaw()).put("paused", c.paused()).put("speed", c.speed())
                .put("local_player_id", c.localPlayerId()).put("map_ready", c.mapReady()).put("has_played_character", c.hasPlayedCharacter())
                .put("played_character_id", c.playedCharacterId()).put("played_character_alive", c.playedCharacterAlive());
    }
    private static boolean matches(Core c, Frame f) {
        return c.paused() && c.mapReady() && c.hasPlayedCharacter() && c.playedCharacterAlive()
                && c.dateRaw() == f.dateRaw() && c.localPlayerId() == f.localPlayerId() && c.playedCharacterId() == f.actorCharacterId();
    }
    static JsonNode field(JsonNode n, String key) {
        StrictJson.require(n != null && n.isObject() && n.has(key), "required field: " + key); return n.get(key);
    }
    static String text(JsonNode n, String key) { return StrictJson.text(field(n, key)); }
    static int signed(JsonNode n, String key) { return (int) StrictJson.integer(field(n, key), Integer.MIN_VALUE, Integer.MAX_VALUE); }
    static BigInteger uint(JsonNode n, String key, boolean positive) {
        return StrictJson.integer(field(n, key), positive ? BigInteger.ONE : BigInteger.ZERO, StrictJson.UINT64_MAX);
    }
    private static boolean bool(JsonNode n, String key) {
        JsonNode v = field(n, key); StrictJson.require(v.isBoolean(), "exact boolean required: " + key); return v.booleanValue();
    }
    private static String nullable(JsonNode n, String key) { JsonNode v = field(n, key); return v.isNull() ? null : reason(StrictJson.text(v)); }
    private static String reason(String value) {
        if (value != null) { StrictJson.text(value); StrictJson.require(value.codePointCount(0, value.length()) <= 1024, "bounded native reason required"); }
        return value;
    }
    private static void nullable(ObjectNode n, String key, String value) { if (value == null) n.putNull(key); else n.put(key, value); }
    private static void positive(BigInteger v) {
        StrictJson.require(v != null && v.signum() > 0 && v.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 native revision required");
    }
}
