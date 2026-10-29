package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Pure narrow estate projection; Root owns original receipt, source qualification and writer lock. */
public final class SuccessionNativeEstate12004 {
    /** Original native ROOT result limit; complete semantic material has its separate shared lease. */
    public static final int MAX_SOURCE_BYTES = 1_048_576;
    public static final String EXECUTABLE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final Set<String> NATIVE_RESULT = Set.of("step", "accepted", "status", "query_sequence",
            "snapshot_revision", "campaign_root_context", "backend_id");
    private SuccessionNativeEstate12004() { }

    /** Comparison evidence only, never a natural-death or player-heir eligibility qualification. */
    public static final class FrozenEstate {
        private final byte[] rootResult;
        private final byte[] semantic;
        private final Expectation expectation;
        private FrozenEstate(byte[] rootResult, byte[] semantic, Expectation expectation) {
            this.rootResult = rootResult.clone(); this.semantic = semantic.clone(); this.expectation = expectation;
        }
        public byte[] originalRootResult() { return rootResult.clone(); }
        public byte[] originalSemantic() { return semantic.clone(); }
        public Expectation expectation() { return expectation; }
        public byte[] wire() { return SuccessionCodec.encodeExpectation(expectation); }
        public String originalRootSha256() { return sha256(rootResult); }
        public String originalSemanticSha256() { return sha256(semantic); }
    }
    public static final class ComparedEstate {
        private final FrozenEstate predecessor;
        private final byte[] rootResult;
        private final byte[] semantic;
        private final Reconciliation comparison;
        private ComparedEstate(FrozenEstate predecessor, byte[] rootResult, byte[] semantic, Reconciliation comparison) {
            this.predecessor = predecessor; this.rootResult = rootResult.clone(); this.semantic = semantic.clone(); this.comparison = comparison;
        }
        public FrozenEstate predecessor() { return predecessor; }
        public Reconciliation comparison() { return comparison; }
        /** Complete M3 wire contract consumed by GoalCodec and LifecycleReducer. */
        public byte[] wire() { return SuccessionCodec.encodeReconciliation(comparison); }
        public byte[] originalRootResult() { return rootResult.clone(); }
        public byte[] originalSemantic() { return semantic.clone(); }
        public String originalRootSha256() { return sha256(rootResult); }
        public String originalSemanticSha256() { return sha256(semantic); }
    }
    /** Current ordinary episode material only; this projection grants neither Continue nor UI clearance. */
    public static final class CurrentEpisodeEstate {
        private final Snapshot snapshot; private final TurnBundle estate;
        private CurrentEpisodeEstate(Snapshot snapshot, TurnBundle estate) { this.snapshot=snapshot; this.estate=estate; }
        public Snapshot snapshot() { return snapshot; }
        public TurnBundle estate() { return estate; }
    }
    public static CurrentEpisodeEstate observeCurrentEpisode(byte[] originalNativeResult, byte[] actualSameFrameSemantic) {
        NativeFrame observed=read(originalNativeResult,actualSameFrameSemantic);Snapshot current=observed.snapshot();
        check(Boolean.FALSE.equals(current.terminal()) && current.terminalReason()==null
                && Objects.equals(current.episodeCharacterId(),current.actor().characterId()),
                "current estate requires the actual living ordinary episode, with no old-subject rewrite");
        return new CurrentEpisodeEstate(current,observed.estate());
    }

    private record NativeFrame(Snapshot snapshot, TurnBundle estate) { }

    public static FrozenEstate freeze(byte[] originalNativeResult, byte[] actualSameFrameSemantic) {
        NativeFrame observed = read(originalNativeResult, actualSameFrameSemantic);
        Snapshot snapshot = observed.snapshot();
        check(Boolean.FALSE.equals(snapshot.terminal()) && snapshot.terminalReason() == null
                && Objects.equals(snapshot.episodeCharacterId(), snapshot.actor().characterId()),
                "preclock estate requires actual living old episode");
        Expectation expected = SuccessionPolicy.freeze(observed.estate(), snapshot.episodeRunId(), snapshot.actor().characterId());
        return new FrozenEstate(originalNativeResult, actualSameFrameSemantic, expected);
    }
    public static ComparedEstate reconcile(FrozenEstate retained, byte[] originalFinalNativeResult, byte[] actualFinalSemantic) {
        Objects.requireNonNull(retained);
        FrozenEstate original = freeze(retained.rootResult, retained.semantic);
        check(java.util.Arrays.equals(original.wire(), retained.wire()), "retained estate projection changed");
        NativeFrame after = read(originalFinalNativeResult, actualFinalSemantic);
        Binding before = original.expectation().binding(); Frame current = after.snapshot().frame();
        check(before.episodeRunId().equals(after.snapshot().episodeRunId())
                && Objects.equals(after.snapshot().episodeCharacterId(), before.episodeCharacterId()), "estate crossed old episode");
        check(current.revision().compareTo(before.frame().revision()) >= 0
                && current.nativeRevision().compareTo(before.frame().nativeRevision()) >= 0
                && current.dateRaw() >= before.frame().dateRaw(), "estate source frame regressed");
        Reconciliation compared = SuccessionPolicy.reconcile(original.expectation(), after.snapshot(), after.estate());
        return new ComparedEstate(original, originalFinalNativeResult, actualFinalSemantic, compared);
    }
    private static NativeFrame read(byte[] originalNativeResult, byte[] actualSemantic) {
        JsonNode result = StrictJson.object(FullJsonTree.parse(originalNativeResult, MAX_SOURCE_BYTES), NATIVE_RESULT);
        check("query-campaign-root-context-v1".equals(text(result, "step")), "original campaign-root query step required");
        StrictJson.trueValue(field(result, "accepted"));
        check("available".equals(text(result, "status")) && "native-headless".equals(text(result, "backend_id")), "available original native root required");
        StrictJson.integer(field(result, "query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
        JsonNode semantic = FullJsonTree.parse(actualSemantic, FullJsonTree.MAXIMUM_BYTES);
        check(semantic.isObject(), "actual semantic object required");
        Snapshot snapshot = SuccessionCodec.snapshot(semantic);
        check(snapshot != null && snapshot.frame() != null && snapshot.actor() != null && snapshot.actor().alive()
                && Boolean.TRUE.equals(snapshot.paused()) && Boolean.TRUE.equals(snapshot.mapReady())
                && snapshot.lifecycle() == Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,
                "actual paused living ordinary source required");
        StrictJson.trueValue(field(field(semantic, "played_character"), "alive"));
        nonempty(snapshot.episodeRunId());
        check(snapshot.episodeCharacterId() != null, "actual episode actor required");
        NativeCharacterId.of(snapshot.episodeCharacterId());
        JsonNode reason = field(semantic, "one_life_terminal_reason");
        boolean changed = snapshot.actor().characterId() != snapshot.episodeCharacterId();
        check(changed ? reason.isTextual() && "played_character_changed".equals(reason.textValue()) : reason.isNull(),
                "actual terminal reason and current/episode actors disagree");
        if (semantic.has("one_life_terminal")) {
            JsonNode terminal = semantic.get("one_life_terminal");
            check(terminal.isBoolean() && terminal.booleanValue() == changed, "present terminal boolean must agree with actual actors/reason");
        }
        // Missing native boolean becomes an INTERNAL typed projection, never an added original JSON field.
        snapshot = new Snapshot(snapshot.frame(), snapshot.episodeRunId(), snapshot.episodeCharacterId(),
                snapshot.paused(), snapshot.mapReady(), changed, snapshot.terminalReason(), snapshot.actor(),
                snapshot.activeEvent(), snapshot.pendingInteraction(), snapshot.lifecycle());
        Frame frame = snapshot.frame();
        StrictJson.integer(field(result, "snapshot_revision"), frame.nativeRevision(), frame.nativeRevision());
        JsonNode root = field(result, "campaign_root_context"); check(root.isObject(), "original native root object required");
        check("available".equals(text(root, "status")) && field(root, "unavailable_reason").isNull(), "available root component required");
        StrictJson.integer(field(root, "schema_version"), 1, 1);
        StrictJson.integer(field(root, "snapshot_revision"), frame.nativeRevision(), frame.nativeRevision());
        StrictJson.integer(field(root, "date_raw"), frame.dateRaw(), frame.dateRaw());
        StrictJson.integer(field(root, "player_character_id"), snapshot.actor().characterId(), snapshot.actor().characterId());
        StrictJson.trueValue(field(root, "player_character_alive"));
        JsonNode provenance = field(root, "provenance");
        check("1.20.0.4".equals(text(provenance, "game_version"))
                && EXECUTABLE_SHA256.equalsIgnoreCase(text(provenance, "executable_sha256"))
                && "ck3-1.20.0.4-native-campaign-root-context-v1".equals(text(provenance, "backend_id"))
                && "0x1E0".equals(text(provenance, "held_title_ids_offset"))
                && "0x289DA10".equals(text(provenance, "primary_title_rva")), "actual installed .4 estate source required");
        JsonNode readiness = field(root, "readiness");
        for (String required : List.of("player_identity_ready", "primary_title_ready", "primary_title_succession_ready",
                "held_title_partition_ready", "same_frame_ready")) StrictJson.trueValue(field(readiness, required));
        JsonNode primary = StrictJson.object(field(root, "primary_title"), Set.of("title_id", "tier_raw", "tier_key"));
        int primaryId = (int) StrictJson.integer(field(primary, "title_id"), 1, Integer.MAX_VALUE);
        StrictJson.integer(field(primary, "tier_raw"), 2, 6);
        JsonNode rawHeirs = field(root, "primary_title_succession_character_ids");
        check(rawHeirs.isArray(), "complete ordered primary-title succession vector required");
        Integer primaryHeir = null; int index = 0;
        for (JsonNode heir : rawHeirs) {
            int id = NativeCharacterId.fromJson(heir).value(); if (index++ == 0) primaryHeir = id;
        }
        JsonNode rawRows = field(root, "held_title_partition"); check(rawRows.isArray(), "complete native partition required");
        List<TitleRow> rows = new ArrayList<>(); int previous = 0, primaries = 0; boolean split = false;
        for (JsonNode raw : rawRows) {
            TitleRow row = SuccessionCodec.row(raw, true);
            check(row.title().titleId() > previous, "native partition must retain canonical complete title order"); previous = row.title().titleId();
            check(!Objects.equals(row.firstHeirCharacterId(), snapshot.actor().characterId()), "native title points to current ruler");
            if (row.primary()) {
                primaries++;
                check(row.title().titleId() == primaryId && field(raw, "title").equals(primary)
                        && Objects.equals(row.firstHeirCharacterId(), primaryHeir), "native primary title/heir projection disagrees");
            }
            if (primaryHeir != null && row.firstHeirCharacterId() != null && !primaryHeir.equals(row.firstHeirCharacterId())) split = true;
            rows.add(row);
        }
        check(primaries == 1, "native complete partition requires exactly one primary");
        RiskState risk = primaryHeir == null ? RiskState.NO_PRIMARY_HEIR : split ? RiskState.SPLIT_SUCCESSORS : RiskState.SINGLE_SUCCESSOR;
        return new NativeFrame(snapshot, new TurnBundle(frame, snapshot.actor(), rows, primaryHeir, risk));
    }
    private static JsonNode field(JsonNode value, String key) {
        check(value != null && value.isObject() && value.has(key), "missing native estate field: " + key); return value.get(key);
    }
    private static String text(JsonNode value, String key) { return StrictJson.text(field(value, key)); }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
