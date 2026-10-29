package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.SwayHistoricalImport;

/** Complete legacy bytes and typed historical facts. No historical stamp is relabelled as a current Game. */
public final class SwayLegacyImport {
    private SwayLegacyImport() { }
    public enum Kind { PENDING, RESOLVED }
    public record Pending(String actionId, long actor, long target, SwayFormalState.PendingStage stage,
            BigInteger preEpoch, BigInteger preContainer, int preDate, BigInteger preRevision,
            int preOpinion, Optional<String> episode, ProjectionJson original) {
        public Pending { SwayNativeWire.action(actionId, false); SwayNativeWire.character(actor); SwayNativeWire.character(target); require(actor != target && preOpinion >= -100 && preOpinion <= 100, "historical pending actor/target/opinion differs"); Objects.requireNonNull(stage); SwayNativeWire.u64(preEpoch, 1); SwayNativeWire.u64(preContainer, 1); SwayNativeWire.u64(preRevision, 1); Objects.requireNonNull(episode); episode.ifPresent(StrictJson::text); Objects.requireNonNull(original); }
    }
    public record OriginalIntent(Kind kind, ProjectionJson original) {
        public OriginalIntent { Objects.requireNonNull(kind); Objects.requireNonNull(original); if (kind == Kind.PENDING) pending(original); else SwayHistoricalImport.parse(original); }
        public void requireIdentity(Identity id) {
            if (kind == Kind.RESOLVED) require(SwayHistoricalImport.parse(original).identity().equals(id), "historical original identity differs");
            else { Pending value = pending(original); require(value.actionId().equals(id.actionId()) && value.actor() == id.actorCharacterId() && value.target() == id.targetCharacterId(), "historical pending action/actor/target differs"); }
        }
        public Identity requireCurrent(SwayNativeWire.TargetRead current) {
            JsonNode row = StrictJson.parse(original.bytes(), SwayFormalCodec.MAX);
            long actor = SwayNativeWire.integer(row, "actor_character_id", 1, 0xffff_fffeL), target = SwayNativeWire.integer(row, "target_character_id", 1, 0xffff_fffeL);
            require(actor == current.binding().actor() && target == current.target() && current.matching(), "historical attachment needs current matching actor/target");
            Optional<Identity> expected = kind == Kind.RESOLVED ? Optional.of(SwayHistoricalImport.parse(original).identity()) : retainedPendingIdentity(pending(original));
            List<SwayNativeWire.Instance> candidates = current.instances().stream().filter(value -> value.target() == target)
                    .filter(value -> expected.isEmpty() || value.fullId() == expected.orElseThrow().schemeInstanceId() && value.generation() == expected.orElseThrow().schemeInstanceGeneration()).toList();
            require(candidates.size() == 1, "fresh restored native read needs one exact historical instance");
            if (kind == Kind.PENDING) requirePendingEpisode(pending(original), current.binding().before().frame().episodeRunId());
            var instance = candidates.getFirst(); return new Identity(SwayNativeWire.string(row, "action_id"), actor, target, instance.fullId(), instance.generation());
        }
        public boolean historicalConsumed(SwayHistoricalImport.Plane plane) {
            if (kind != Kind.RESOLVED) return false;
            var field = SwayHistoricalImport.parse(original).plane(plane);
            return field instanceof SwayHistoricalImport.Retained retained && retained.consumption().markedConsumed();
        }
        public boolean historicalStartConsumed() { return kind == Kind.RESOLVED && SwayHistoricalImport.parse(original).startConsumption().markedConsumed(); }
        public BigInteger preEpoch() { return SwayNativeWire.wide(StrictJson.parse(original.bytes(), SwayFormalCodec.MAX), "pre_capture_epoch", 1); }
        @Override public boolean equals(Object value) { return value instanceof OriginalIntent other && kind == other.kind && Arrays.equals(original.bytes(), other.original.bytes()); }
        @Override public int hashCode() { return 31 * kind.hashCode() + Arrays.hashCode(original.bytes()); }
    }
    public record Imported(ExactRef archivedOriginal, ProjectionJson original, Optional<Pending> pending,
            Optional<SwayHistoricalImport.History> resolved) {
        public Imported {
            Objects.requireNonNull(archivedOriginal); Objects.requireNonNull(original); Objects.requireNonNull(pending); Objects.requireNonNull(resolved);
            require(archivedOriginal.bytes() == original.bytes().length && archivedOriginal.sha256().equals(org.xar.ck3.control.application.action.ActionCodec.sha256(original.bytes())), "imported whole original reference differs");
            JsonNode root = StrictJson.object(StrictJson.parse(original.bytes(), SwayFormalCodec.MAX), Set.of("schema", "pending", "resolved"));
            require(root.get("pending").isNull() == pending.isEmpty() && root.get("resolved").isNull() == resolved.isEmpty(), "imported original nullable branches differ");
            pending.ifPresent(value -> require(StrictJson.parse(value.original().bytes(), SwayFormalCodec.MAX).equals(root.get("pending")) && value.actionId().equals(SwayNativeWire.string(root.get("pending"), "action_id")) && value.actor() == SwayNativeWire.integer(root.get("pending"), "actor_character_id", 1, 0xffff_ffffL) && value.target() == SwayNativeWire.integer(root.get("pending"), "target_character_id", 1, 0xffff_ffffL), "imported pending differs from whole original"));
            resolved.ifPresent(value -> require(StrictJson.parse(value.originalResolved().bytes(), SwayFormalCodec.MAX).equals(root.get("resolved")), "imported resolved differs from whole original"));
        }
        public OriginalIntent currentIntent() {
            if (pending.isPresent()) return new OriginalIntent(Kind.PENDING, pending.orElseThrow().original());
            return new OriginalIntent(Kind.RESOLVED, resolved.orElseThrow(() -> new IllegalArgumentException("empty original has no historical current episode")).originalResolved());
        }
    }
    public static Imported parse(ExactRef archivedOriginal, byte[] bytes) {
        ObjectNode row = StrictJson.object(StrictJson.parse(bytes, SwayFormalCodec.MAX), Set.of("schema", "pending", "resolved"));
        SwayNativeWire.equals(row, "schema", "xar.ck3.active-scheme-sway-formal-private.v1");
        require(archivedOriginal.bytes() == bytes.length && archivedOriginal.sha256().equals(org.xar.ck3.control.application.action.ActionCodec.sha256(bytes)), "full legacy immutable input SHA differs");
        Optional<Pending> pending = SwayFormalCodec.optional(row.get("pending")).map(value -> pending(json(value)));
        Optional<SwayHistoricalImport.History> resolved = SwayFormalCodec.optional(row.get("resolved")).map(value -> SwayHistoricalImport.parse(json(value)));
        return new Imported(archivedOriginal, ProjectionJson.object(bytes, SwayFormalCodec.MAX), pending, resolved);
    }
    public static Pending pending(ProjectionJson original) {
        JsonNode row = StrictJson.parse(original.bytes(), SwayFormalCodec.MAX); require(row.isObject(), "legacy pending object required");
        Set<String> required = Set.of("stage", "action_id", "actor_character_id", "target_character_id", "pre_capture_epoch", "pre_container_generation", "pre_date_raw", "pre_native_revision", "pre_target_opinion_of_actor");
        Set<String> allowed = new java.util.HashSet<>(required); allowed.addAll(Set.of("episode_run_id", "followup", "ack", "native_applied_receipt", "native_receipt_source"));
        Set<String> actual = new java.util.HashSet<>(); row.fieldNames().forEachRemaining(actual::add); require(actual.containsAll(required) && allowed.containsAll(actual), "legacy pending fields differ");
        String action = SwayNativeWire.string(row, "action_id"); SwayNativeWire.action(action, false);
        long actor = SwayNativeWire.integer(row, "actor_character_id", 1, 0xffff_fffeL), target = SwayNativeWire.integer(row, "target_character_id", 1, 0xffff_fffeL); require(actor != target, "legacy pending actor cannot equal target");
        var stage = switch (SwayNativeWire.string(row, "stage")) { case "submission_unresolved" -> SwayFormalState.PendingStage.SUBMISSION_UNRESOLVED; case "receipt_pending" -> SwayFormalState.PendingStage.RECEIPT_PENDING; case "postcondition_pending" -> SwayFormalState.PendingStage.POSTCONDITION_PENDING; default -> throw new IllegalArgumentException("unknown legacy pending stage"); };
        if (row.has("ack")) require(row.get("ack").isObject(), "legacy ACK object required");
        if (row.has("followup")) require(row.get("followup").isObject(), "legacy followup object required");
        if (row.has("native_receipt_source")) require(row.get("native_receipt_source").isObject(), "legacy receipt-source object required");
        require(stage != SwayFormalState.PendingStage.RECEIPT_PENDING || row.has("ack"), "legacy receipt pending preserves ACK");
        require(stage != SwayFormalState.PendingStage.POSTCONDITION_PENDING || row.has("native_applied_receipt"), "legacy postcondition pending preserves original receipt");
        Pending result = new Pending(action, actor, target, stage, SwayNativeWire.wide(row, "pre_capture_epoch", 1), SwayNativeWire.wide(row, "pre_container_generation", 1), SwayNativeWire.signed(row, "pre_date_raw"), SwayNativeWire.wide(row, "pre_native_revision", 1), Math.toIntExact(SwayNativeWire.integer(row, "pre_target_opinion_of_actor", -100, 100)), row.has("episode_run_id") ? Optional.of(SwayNativeWire.string(row, "episode_run_id")) : Optional.empty(), original);
        retainedPendingIdentity(result); return result;
    }
    private static Optional<Identity> retainedPendingIdentity(Pending pending) {
        JsonNode row = StrictJson.parse(pending.original().bytes(), SwayFormalCodec.MAX); if (!row.has("native_applied_receipt")) return Optional.empty();
        JsonNode receipt = row.get("native_applied_receipt"); require(receipt.isObject(), "retained legacy receipt object required");
        SwayNativeWire.equals(receipt, "schema", "active-scheme-sway-formal-private-v1"); SwayNativeWire.equals(receipt, "stage", "applied");
        require(SwayNativeWire.bool(receipt, "postcondition_verified") && SwayNativeWire.string(receipt, "action_id").equals(pending.actionId()), "historical receipt original action differs");
        if (receipt.has("actor_character_id")) require(SwayNativeWire.integer(receipt, "actor_character_id", 1, 0xffff_fffeL) == pending.actor(), "historical receipt actor differs");
        if (receipt.has("target_character_id")) require(SwayNativeWire.integer(receipt, "target_character_id", 1, 0xffff_fffeL) == pending.target(), "historical receipt target differs");
        String build = SwayNativeWire.string(receipt, "exact_ck3_build"), exe = SwayNativeWire.string(receipt, "exe_sha256");
        require(build.equals("1.20.0.4") && exe.equals("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                || build.equals("1.20.0.3") && exe.equals("94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"), "unknown historical pending receipt build/executable pair");
        require(SwayNativeWire.wide(receipt, "post_capture_epoch", 1).compareTo(pending.preEpoch()) > 0 && SwayNativeWire.signed(receipt, "post_date_raw") == pending.preDate(), "retained historical operation epoch/date differs");
        long full = SwayNativeWire.integer(receipt, "scheme_instance_id", 1, 0xffff_fffeL); int generation = Math.toIntExact(SwayNativeWire.integer(receipt, "scheme_instance_generation", 0, 255)); require(generation == full >>> 24, "historical full instance generation differs");
        return Optional.of(new Identity(pending.actionId(), pending.actor(), pending.target(), full, generation));
    }
    private static void requirePendingEpisode(Pending pending, String currentEpisode) {
        var episodes = new java.util.HashSet<String>(); pending.episode().ifPresent(episodes::add); JsonNode source = StrictJson.parse(pending.original().bytes(), SwayFormalCodec.MAX).get("native_receipt_source");
        if (source != null) {
            SwayNativeWire.equals(source, "schema", "xar.ck3.sway-receipt-source-frame.v1");
            for (String name : List.of("before", "after")) {
                JsonNode frame = source.get(name); require(frame != null && frame.isObject(), "historical receipt frame missing");
                if (frame.has("episode_run_id")) episodes.add(SwayNativeWire.string(frame, "episode_run_id"));
                if (frame.has("actor_character_id")) require(SwayNativeWire.integer(frame, "actor_character_id", 1, 0xffff_fffeL) == pending.actor(), "historical receipt sidecar actor differs");
            }
        }
        require(episodes.size() <= 1 && episodes.stream().allMatch(currentEpisode::equals), "historical pending episode/source conflicts with current restored frame");
    }
    static ProjectionJson json(JsonNode value) { return ProjectionJson.object(value.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8), SwayFormalCodec.MAX); }
}
