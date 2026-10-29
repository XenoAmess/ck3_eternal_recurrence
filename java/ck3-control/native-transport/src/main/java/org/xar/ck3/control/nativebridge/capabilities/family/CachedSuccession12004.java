package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** The native ordered cached roster is observation only; it is not Character.GetPlayerHeir or CanContinue. */
public final class CachedSuccession12004 {
    public static final String STEP = "query-actor-cached-succession-v1";
    public static final String PERMISSION = "allow_private_actor_cached_succession_queries";
    public static final String EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final Set<String> ENVELOPE = Set.of("step", "accepted", "status", "private_build", "read_only", "advertised",
            "game_version", "executable_sha256", "domain_key", "backend_id", "snapshot_revision", "date_raw", "actor_cached_succession");
    private static final Set<String> PAYLOAD = Set.of("schema", "read_only", "game_version", "executable_sha256", "available",
            "unavailable_reason", "capture_epoch", "date_raw", "played_character_id", "played_character_full_id", "roster_complete",
            "native_count", "complete_cached_successor_ids", "native_data_pointer", "land_state_pointer");
    private static final Set<String> PUBLIC = Set.of("schema", "operation", "native_result", "queried_snapshot_id", "queried_revision",
            "queried_native_revision", "date_raw", "game_pid", "connection_generation", "player_character_id",
            "business_postcondition_verified", "full_product_acceptance_credit");
    private CachedSuccession12004() { }
    public record Binding(String snapshotId, BigInteger revision, BigInteger nativeRevision, int dateRaw,
            long gamePid, BigInteger connectionGeneration, long playedCharacterId) {
        public Binding {
            StrictJson.text(snapshotId); positive64(revision); positive64(nativeRevision); positive64(connectionGeneration);
            StrictJson.require(gamePid > 0 && gamePid <= 0xffff_ffffL, "valid Game PID required");
            StrictJson.require(playedCharacterId >= Integer.MIN_VALUE && playedCharacterId <= 0xffff_fffeL
                    && playedCharacterId != -1, "actual signed or unsigned full actor required");
        }
        public long playedFullId() { return playedCharacterId & 0xffff_ffffL; }
    }
    public sealed interface Roster permits Available, Unavailable { }
    public record Available(List<Long> completeCachedSuccessorIds, BigInteger nativeDataPointer, BigInteger landStatePointer) implements Roster {
        public Available {
            completeCachedSuccessorIds = List.copyOf(completeCachedSuccessorIds);
            for (long id : completeCachedSuccessorIds) fullId(id);
            pointer(nativeDataPointer, false); pointer(landStatePointer, true);
            StrictJson.require(nativeDataPointer.signum() != 0 || completeCachedSuccessorIds.isEmpty(), "null data pointer requires empty native cache");
        }
    }
    public record Unavailable(String reason) implements Roster {
        public Unavailable { StrictJson.text(reason); StrictJson.require(reason.length() <= 4096, "bounded actual unavailable reason required"); }
    }
    public record Observation(Binding binding, BigInteger captureEpoch, Roster roster, RawJson originalNativeResult) {
        public Observation { Objects.requireNonNull(binding); positive64(captureEpoch); Objects.requireNonNull(roster); Objects.requireNonNull(originalNativeResult); }
        public boolean businessPostconditionVerified() { return false; }
        public boolean fullProductAcceptanceCredit() { return false; }
    }
    public static Observation decodeNative(RawJson original, Binding binding) {
        Objects.requireNonNull(binding); ObjectNode root = StrictJson.object(StrictJson.parse(original.bytes(), 1_048_576), ENVELOPE);
        build(root); text(root, "step", STEP); yes(root, "accepted"); yes(root, "private_build"); yes(root, "read_only"); no(root, "advertised");
        text(root, "domain_key", "actor_cached_succession_v1"); text(root, "backend_id", "ck3-1.20.0.4-native-actor-cached-succession-v1");
        StrictJson.integer(root.get("snapshot_revision"), binding.nativeRevision(), binding.nativeRevision());
        StrictJson.integer(root.get("date_raw"), binding.dateRaw(), binding.dateRaw());
        ObjectNode value = StrictJson.object(root.get("actor_cached_succession"), PAYLOAD); build(value);
        text(value, "schema", "ck3-1.20.0.4-actor-cached-succession-v1"); yes(value, "read_only");
        StrictJson.integer(value.get("date_raw"), binding.dateRaw(), binding.dateRaw());
        long signedActor = binding.playedFullId() >= 0x8000_0000L ? binding.playedFullId() - 0x1_0000_0000L : binding.playedFullId();
        StrictJson.integer(value.get("played_character_id"), signedActor, signedActor);
        StrictJson.integer(value.get("played_character_full_id"), binding.playedFullId(), binding.playedFullId());
        BigInteger epoch = StrictJson.integer(value.get("capture_epoch"), BigInteger.ONE, StrictJson.UINT64_MAX);
        boolean available = bool(value.get("available"));
        StrictJson.require(bool(value.get("roster_complete")) == available, "roster completeness must equal native availability");
        text(root, "status", available ? "observed" : "unavailable");
        Roster roster;
        if (!available) {
            nil(value, "native_count", "complete_cached_successor_ids", "native_data_pointer", "land_state_pointer");
            roster = new Unavailable(StrictJson.text(value.get("unavailable_reason")));
        } else {
            nil(value, "unavailable_reason");
            int count = (int) StrictJson.integer(value.get("native_count"), 0, Integer.MAX_VALUE);
            JsonNode ids = value.get("complete_cached_successor_ids");
            StrictJson.require(ids.isArray() && ids.size() == count, "complete original-order cache count mismatch");
            List<Long> ordered = new ArrayList<>();
            for (JsonNode id : ids) ordered.add(StrictJson.integer(id, 0, 0xffff_fffeL));
            roster = new Available(ordered, StrictJson.integer(value.get("native_data_pointer"), BigInteger.ZERO, StrictJson.UINT64_MAX),
                    StrictJson.integer(value.get("land_state_pointer"), BigInteger.ONE, StrictJson.UINT64_MAX));
        }
        return new Observation(binding, epoch, roster, original);
    }
    public static RawJson encodePublic(Observation observation) {
        Objects.requireNonNull(observation);
        // Revalidate the retained raw source instead of serializing an independently fabricated roster.
        Observation original = decodeNative(observation.originalNativeResult(), observation.binding());
        StrictJson.require(original.captureEpoch().equals(observation.captureEpoch()) && original.roster().equals(observation.roster()), "typed cached source content differs");
        Binding b = observation.binding();
        ObjectNode node = StrictJson.object().put("schema", "ck3-actor-cached-succession-public-v1").put("operation", "actor_cached_succession")
                .put("queried_snapshot_id", b.snapshotId()).put("queried_revision", b.revision()).put("queried_native_revision", b.nativeRevision())
                .put("date_raw", b.dateRaw()).put("game_pid", b.gamePid()).put("connection_generation", b.connectionGeneration())
                .put("player_character_id", b.playedCharacterId()).put("business_postcondition_verified", false).put("full_product_acceptance_credit", false);
        node.set("native_result", StrictJson.parse(observation.originalNativeResult().bytes(), 1_048_576));
        return new RawJson(StrictJson.canonical(node, 1_048_576));
    }
    public static Observation decodePublic(RawJson original, Binding binding) {
        ObjectNode root = StrictJson.object(StrictJson.parse(original.bytes(), 1_048_576), PUBLIC);
        Observation result = decodeNative(new RawJson(StrictJson.canonical(root.get("native_result"), 1_048_576)), binding);
        JsonNode expected = StrictJson.parse(encodePublic(result).bytes(), 1_048_576);
        StrictJson.require(root.equals(expected), "public cached-succession frame, types, source, or credit changed");
        return result;
    }
    public static Binding decodeBinding(byte[] bytes) {
        ObjectNode n = StrictJson.object(StrictJson.parse(bytes), Set.of("snapshot_id", "revision", "native_revision", "date_raw",
                "game_pid", "connection_generation", "played_character_id"));
        return new Binding(StrictJson.text(n.get("snapshot_id")), StrictJson.integer(n.get("revision"), BigInteger.ONE, StrictJson.UINT64_MAX),
                StrictJson.integer(n.get("native_revision"), BigInteger.ONE, StrictJson.UINT64_MAX), (int) StrictJson.integer(n.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                StrictJson.integer(n.get("game_pid"), 1, 0xffff_ffffL), StrictJson.integer(n.get("connection_generation"), BigInteger.ONE, StrictJson.UINT64_MAX),
                StrictJson.integer(n.get("played_character_id"), Integer.MIN_VALUE, 0xffff_fffeL));
    }
    private static void build(JsonNode node) { text(node, "game_version", "1.20.0.4"); StrictJson.require(StrictJson.text(node.get("executable_sha256")).equalsIgnoreCase(EXE_SHA256), "cached succession exact .4 executable required"); }
    private static void text(JsonNode node, String key, String expected) { StrictJson.require(expected.equals(StrictJson.text(node.get(key))), "cached succession field mismatch: " + key); }
    private static boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "actual JSON boolean required"); return node.booleanValue(); }
    private static void yes(JsonNode node, String field) { StrictJson.trueValue(node.get(field)); }
    private static void no(JsonNode node, String field) { StrictJson.require(!bool(node.get(field)), "actual JSON false required"); }
    private static void nil(JsonNode node, String... fields) { for (String field : fields) StrictJson.require(node.has(field) && node.get(field).isNull(), "explicit JSON null required: " + field); }
    private static void positive64(BigInteger value) { pointer(value, true); }
    private static void pointer(BigInteger value, boolean positive) { StrictJson.require(value != null && value.compareTo(positive ? BigInteger.ONE : BigInteger.ZERO) >= 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "uint64 native identity required"); }
    private static void fullId(long id) { StrictJson.require(id >= 0 && id <= 0xffff_fffeL, "full native cache identity required"); }
}
