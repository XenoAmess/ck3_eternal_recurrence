package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.SwayLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.vanilla.schemesway.SwayScheduleWire;

/** Canonical input replayed by the exact registered SWAY verifier under the original writer lock. */
public final class SwayTransitionCodec {
    public static final String SCHEMA = "xar.java.sway-domain-transition/v2";
    public static final String PUBLIC_START_SCHEMA = "xar.java.sway-domain-transition/v3";
    public static final String FOLLOWING_GAMEPLAY_SCHEMA = "xar.java.sway-domain-transition/v4";
    private SwayTransitionCodec() { }
    public record Proofs(List<ExactRef> reads, Optional<ExactRef> dispatch, Optional<ExactRef> nativeFrame, List<ExactRef> materials) {
        public Proofs(List<ExactRef> reads, Optional<ExactRef> dispatch, Optional<ExactRef> nativeFrame) { this(reads, dispatch, nativeFrame, List.of()); }
        public Proofs { reads = List.copyOf(reads); materials = List.copyOf(materials); require(reads.size() <= 4 && materials.size() <= 8, "bounded Sway source evidence"); java.util.Objects.requireNonNull(dispatch); java.util.Objects.requireNonNull(nativeFrame); }
        public List<ExactRef> all() { java.util.ArrayList<ExactRef> refs = new java.util.ArrayList<>(reads); dispatch.ifPresent(refs::add); nativeFrame.ifPresent(refs::add); refs.addAll(materials); return List.copyOf(refs); }
    }
    public record Input(ExactRef predecessor, Change change, Proofs proofs) { public Input { java.util.Objects.requireNonNull(predecessor); java.util.Objects.requireNonNull(change); java.util.Objects.requireNonNull(proofs); } }
    public static byte[] encode(Input input) {
        ObjectNode row = StrictJson.object(); row.put("schema", input.change() instanceof FollowingGameplay ? FOLLOWING_GAMEPLAY_SCHEMA : input.change() instanceof StartIntent start&&start.admission()==StartAdmission.PUBLIC_NATIVE_FINAL?PUBLIC_START_SCHEMA:SCHEMA); row.set("predecessor", input.predecessor().toJson()); row.set("change", change(input.change()));
        ObjectNode proof = row.putObject("proofs"); var reads = proof.putArray("reads"); input.proofs().reads().forEach(ref -> reads.add(ref.toJson()));
        if (input.proofs().dispatch().isPresent()) proof.set("dispatch", input.proofs().dispatch().orElseThrow().toJson()); else proof.putNull("dispatch");
        if (input.proofs().nativeFrame().isPresent()) proof.set("native_frame", input.proofs().nativeFrame().orElseThrow().toJson()); else proof.putNull("native_frame");
        var materials = proof.putArray("materials"); input.proofs().materials().forEach(ref -> materials.add(ref.toJson()));
        return StrictJson.canonical(row, SwayFormalCodec.MAX);
    }
    public static Input decode(byte[] raw, Ledger before) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, SwayFormalCodec.MAX), Set.of("schema", "predecessor", "change", "proofs")); String schema=SwayNativeWire.string(row,"schema");require(SCHEMA.equals(schema)||PUBLIC_START_SCHEMA.equals(schema)||FOLLOWING_GAMEPLAY_SCHEMA.equals(schema),"registered exact Sway transition schema required");
        boolean publicStart=SwayNativeWire.string(row.get("change"),"kind").equals("public_start_intent");require(publicStart==PUBLIC_START_SCHEMA.equals(schema),"public native Start requires explicit v3; legacy ordinary transitions retain exact v2");
        boolean followingGameplay=SwayNativeWire.string(row.get("change"),"kind").equals("following_gameplay");require(followingGameplay==FOLLOWING_GAMEPLAY_SCHEMA.equals(schema),"gameplay Following requires explicit v4; historical transitions retain their original versions");
        JsonNode proofs = StrictJson.object(row.get("proofs"), Set.of("reads", "dispatch", "native_frame", "materials")); JsonNode reads = proofs.get("reads"); require(reads.isArray() && reads.size() <= 4, "bounded original Sway read references");
        java.util.ArrayList<ExactRef> refs = new java.util.ArrayList<>(); reads.forEach(value -> refs.add(ExactRef.fromJson(value)));
        JsonNode materials = proofs.get("materials"); require(materials.isArray() && materials.size() <= 8, "bounded original material references"); java.util.ArrayList<ExactRef> materialRefs = new java.util.ArrayList<>(); materials.forEach(value -> materialRefs.add(ExactRef.fromJson(value)));
        return new Input(ExactRef.fromJson(row.get("predecessor")), change(row.get("change"), before), new Proofs(refs, SwayFormalCodec.optional(proofs.get("dispatch")).map(ExactRef::fromJson), SwayFormalCodec.optional(proofs.get("native_frame")).map(ExactRef::fromJson), materialRefs));
    }
    static ObjectNode change(Change value) {
        ObjectNode row = StrictJson.object();
        switch (value) {
            case StartIntent change -> { row.put("kind", change.admission()==StartAdmission.PUBLIC_NATIVE_FINAL?"public_start_intent":"start_intent"); row.put("action_id", change.actionId()); row.set("target", SwayFormalCodec.target(change.original())); row.put("context", change.context().name()); }
            case StartAcknowledged change -> { row.put("kind", "start_acknowledged"); row.set("acknowledgement", StrictJson.parse(change.acknowledgement().body().bytes(), SwayFormalCodec.MAX)); }
            case ReceiptRetained change -> { row.put("kind", "receipt_retained"); row.set("receipt", SwayFormalCodec.receipt(change.receipt())); }
            case Recovered change -> { row.put("kind", "recovered"); row.set("target", SwayFormalCodec.target(change.independent())); }
            case LifecycleObserved change -> { row.put("kind", "lifecycle_observed"); row.set("lifecycle", SwayFormalCodec.chunks(SwayLifecycle.encode(change.state()))); }
            case StopIntent change -> { row.put("kind", "stop_intent"); row.put("action_id", change.actionId()); row.set("target", SwayFormalCodec.target(change.target())); }
            case StopAcknowledged change -> { row.put("kind", "stop_acknowledged"); row.set("acknowledgement", StrictJson.parse(change.acknowledgement().body().bytes(), SwayFormalCodec.MAX)); }
            case StopObserved change -> { row.put("kind", "stop_observed"); row.set("lifecycle", SwayFormalCodec.chunks(SwayLifecycle.encode(change.state()))); row.set("queried", ProposalLifecycleCodec.observation(change.queried())); }
            case HistoricalAttached change -> { row.put("kind", "historical_attached"); row.set("target", SwayFormalCodec.target(change.independent())); row.set("restore_attachment", change.restoreAttachment().toJson()); }
            case Following change -> { row.put("kind", "following"); row.set("after", ProposalLifecycleCodec.observation(change.after())); }
            case FollowingGameplay change -> { row.put("kind", "following_gameplay"); row.set("action_before", ProposalLifecycleCodec.observation(change.actionBefore())); row.set("after", ProposalLifecycleCodec.observation(change.after())); row.set("receipt", change.receipt().toJson()); }
            case SchedulerSaved change -> { row.put("kind", "scheduler_saved"); row.set("state", StrictJson.parse(SwayScheduleWire.encodeState(change.state()))); row.set("replay", change.replay().toJson()); }
            case StageRecorded change -> { row.put("kind", "stage_recorded"); row.set("basis", change.basis().toJson()); }
            case ScopeRebound change -> { row.put("kind", "scope_rebound"); row.set("queried", ProposalLifecycleCodec.observation(change.queried())); row.set("restore_material", change.restoreMaterial().toJson()); }
        }
        return row;
    }
    static Change change(JsonNode row, Ledger before) {
        String kind = SwayNativeWire.string(row, "kind");
        return switch (kind) {
            case "start_intent", "public_start_intent" -> { StrictJson.object(row, Set.of("kind", "action_id", "target", "context")); yield new StartIntent(SwayNativeWire.string(row, "action_id"), SwayFormalCodec.target(row.get("target")), MandatoryContext.valueOf(SwayNativeWire.string(row, "context")),kind.equals("public_start_intent")?StartAdmission.PUBLIC_NATIVE_FINAL:StartAdmission.ORDINARY_OPPORTUNITY); }
            case "start_acknowledged" -> {
                StrictJson.object(row, Set.of("kind", "acknowledgement")); Pending pending = before.pending().orElseThrow();
                yield new StartAcknowledged(SwayNativeWire.startAck(SwayFormalCodec.payload(SwayNativeWire.START + pending.original().target(), "submitted_verification_pending", "active_scheme_sway_formal", row.get("acknowledgement"), false, false), "persisted-payload", pending.actionId(), pending.original()));
            }
            case "receipt_retained" -> { StrictJson.object(row, Set.of("kind", "receipt")); yield new ReceiptRetained(SwayFormalCodec.receipt(row.get("receipt"), before.pending().orElseThrow().original().target())); }
            case "recovered" -> { StrictJson.object(row, Set.of("kind", "target")); yield new Recovered(SwayFormalCodec.target(row.get("target"))); }
            case "lifecycle_observed" -> { StrictJson.object(row, Set.of("kind", "lifecycle")); yield new LifecycleObserved(SwayLifecycle.decode(SwayFormalCodec.bytes(row.get("lifecycle")))); }
            case "stop_intent" -> { StrictJson.object(row, Set.of("kind", "action_id", "target")); yield new StopIntent(SwayNativeWire.string(row, "action_id"), SwayFormalCodec.target(row.get("target"))); }
            case "stop_acknowledged" -> {
                StrictJson.object(row, Set.of("kind", "acknowledgement")); Episode current = before.resolved().orElseThrow(); Stop stop = current.stop().orElseThrow(); var id = current.identity();
                yield new StopAcknowledged(SwayNativeWire.stopAck(SwayFormalCodec.payload(SwayNativeWire.STOP, "submitted_verification_pending", "sway_stop", row.get("acknowledgement"), false, true), "persisted-payload", stop.submittedFrom(), stop.actionId(), id.targetCharacterId(), id.schemeInstanceId(), id.schemeInstanceGeneration()));
            }
            case "stop_observed" -> { StrictJson.object(row, Set.of("kind", "lifecycle", "queried")); yield new StopObserved(SwayLifecycle.decode(SwayFormalCodec.bytes(row.get("lifecycle"))), ProposalLifecycleCodec.decodeObservation(row.get("queried"))); }
            case "historical_attached" -> { StrictJson.object(row, Set.of("kind", "target", "restore_attachment")); yield new HistoricalAttached(SwayFormalCodec.target(row.get("target")), ExactRef.fromJson(row.get("restore_attachment"))); }
            case "following" -> { StrictJson.object(row, Set.of("kind", "after")); yield new Following(ProposalLifecycleCodec.decodeObservation(row.get("after"))); }
            case "following_gameplay" -> { StrictJson.object(row, Set.of("kind", "action_before", "after", "receipt")); yield new FollowingGameplay(ProposalLifecycleCodec.decodeObservation(row.get("action_before")), ProposalLifecycleCodec.decodeObservation(row.get("after")), ExactRef.fromJson(row.get("receipt"))); }
            case "scheduler_saved" -> { StrictJson.object(row, Set.of("kind", "state", "replay")); yield new SchedulerSaved(SwayScheduleWire.decodeState(StrictJson.canonical(row.get("state"))), ExactRef.fromJson(row.get("replay"))); }
            case "stage_recorded" -> { StrictJson.object(row, Set.of("kind", "basis")); yield new StageRecorded(ExactRef.fromJson(row.get("basis"))); }
            case "scope_rebound" -> { StrictJson.object(row, Set.of("kind", "queried", "restore_material")); yield new ScopeRebound(ProposalLifecycleCodec.decodeObservation(row.get("queried")), ExactRef.fromJson(row.get("restore_material"))); }
            default -> throw new IllegalArgumentException("unregistered Sway transition kind");
        };
    }
}
