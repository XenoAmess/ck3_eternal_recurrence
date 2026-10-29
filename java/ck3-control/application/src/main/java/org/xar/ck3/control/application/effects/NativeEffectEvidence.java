package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Durable ordinary-effect inputs, with no stored expected-values or acceptance flag to substitute for a replay. */
public final class NativeEffectEvidence {
    public static final String SCHEMA = "xar.java.native-effect-original-basis/v2";
    public static final String RECONCILIATION_SCHEMA = "xar.java.native-effect-original-basis/v3";
    private static final Set<String> V2_FIELDS = Set.of("schema", "command_body_sha256", "request_id", "before", "after", "compatible_material", "independent_reads", "supporting_materials");
    private NativeEffectEvidence() { }
    public record FrameBasis(ExactRef nativeFrame, ExactRef driverFacts) {
        public FrameBasis { Objects.requireNonNull(nativeFrame); Objects.requireNonNull(driverFacts); StrictJson.require(!nativeFrame.equals(driverFacts), "native packet and Driver facts manifest are different originals"); }
    }
    @FunctionalInterface public interface FrameLoader {
        /** Root binds the actual Driver evidence decoder and assembler; no constructor-only or semantic-export fallback is legal. */
        Complete load(FrameBasis original, ActionPorts.OutcomeArchive archive);
    }
    public record Original(NativeEffectSnapshots.Pair frames, List<PlanningReadReceipt> independentReads, RawJson compatibleResult,
            List<ExactRef> supportingMaterials, java.util.Optional<GuardEvidence> reconciliationGuard) {
        public Original { Objects.requireNonNull(frames); independentReads = List.copyOf(independentReads); Objects.requireNonNull(compatibleResult); supportingMaterials = List.copyOf(supportingMaterials); Objects.requireNonNull(reconciliationGuard); }
        public Original(NativeEffectSnapshots.Pair frames, List<PlanningReadReceipt> independentReads, RawJson compatibleResult, List<ExactRef> supportingMaterials) {
            this(frames, independentReads, compatibleResult, supportingMaterials, java.util.Optional.empty());
        }
        public Original(NativeEffectSnapshots.Pair frames, List<PlanningReadReceipt> independentReads, RawJson compatibleResult) {
            this(frames, independentReads, compatibleResult, List.of());
        }
    }
    public static ExactRef preserve(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair frames,
            List<PlanningReadReceipt> reads, RawJson compatible, ActionPorts.OutcomeArchive archive) {
        return preserve(command, attempt, frames, reads, compatible, List.of(), archive);
    }
    public static ExactRef preserve(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair frames,
            List<PlanningReadReceipt> reads, RawJson compatible, List<ExactRef> supportingMaterials, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(command); Objects.requireNonNull(attempt); Objects.requireNonNull(frames); Objects.requireNonNull(compatible);
        java.util.Optional<GuardEvidence> reconciliation = java.util.Optional.empty();
        if (ActionReconciliationScope.activeFor(command)) {
            try { reconciliation = java.util.Optional.of(ActionReconciliationScope.requireObservationGuard(command, attempt)); }
            catch (java.io.IOException unavailable) { throw new java.io.UncheckedIOException("actual pending push qualification is unavailable", unavailable); }
            requireReconciliation(command, attempt, frames.after(), reconciliation.orElseThrow());
        }
        StrictJson.require(reads != null && reads.size() <= 16, "finite actual independent-read evidence required");
        FrameBasis before = basis(frames.before()), after = basis(frames.after());
        for (FrameBasis frame : List.of(before, after)) {
            RootGuardChecks.exact(frame.nativeFrame(), archive.loadNativeFrame(frame.nativeFrame()));
            RootGuardChecks.exact(frame.driverFacts(), archive.loadFullMaterial(frame.driverFacts()).bytes());
        }
        ExactRef material = archive.preserveMaterial(compatible);
        StrictJson.require(compatible.equals(archive.loadMaterial(material)), "actual compatible result archive changed");
        ObjectNode row = StrictJson.object(); row.put("schema", reconciliation.isPresent() ? RECONCILIATION_SCHEMA : SCHEMA); row.put("command_body_sha256", ActionCodec.bodySha256(command)); row.put("request_id", attempt.requestId());
        reconciliation.ifPresent(guard -> row.set("reconciliation_guard", CommandOriginCodec.guard(guard)));
        row.set("before", json(before)); row.set("after", json(after)); row.set("compatible_material", material.toJson());
        var array = row.putArray("independent_reads"); var requestIds = new java.util.HashSet<String>();
        for (PlanningReadReceipt read : List.copyOf(reads)) {
            StrictJson.require(requestIds.add(read.requestId()) && !read.requestId().equals(attempt.requestId()), "duplicate or action ACK used as independent read");
            NativeRecordedEvidenceVerifier.requireRead(read, archive); array.add(archive.readReferenceOf(read).toJson());
        }
        StrictJson.require(supportingMaterials != null && supportingMaterials.size() <= 16, "bounded original domain material closure required");
        var materials = row.putArray("supporting_materials"); var uniqueMaterials = new java.util.HashSet<ExactRef>();
        for (ExactRef ref : List.copyOf(supportingMaterials)) {
            StrictJson.require(uniqueMaterials.add(ref), "duplicate original supporting material");
            RootGuardChecks.exact(ref, archive.loadMaterial(ref).bytes()); materials.add(ref.toJson());
        }
        RawJson body = EffectJson.raw(row); ExactRef reference = archive.preserveMaterial(body);
        StrictJson.require(body.equals(archive.loadMaterial(reference)), "actual effect basis archive changed"); return reference;
    }
    /** Selects only this exact shared basis. Domain-specific proof planes retain their own strict replay. */
    public static java.util.Optional<Original> loadIfPresent(ActionReceipt receipt, ActionPorts.OutcomeArchive archive, FrameLoader frames) {
        if (!(receipt.state() instanceof ActionState.Settled settled)
                || !(settled.settlement() instanceof ActionState.Applied applied)
                || applied.observation().supportingEvidence().isEmpty()) return java.util.Optional.empty();
        ExactRef reference = applied.observation().supportingEvidence().getFirst();
        RawJson body = archive.loadMaterial(reference); RootGuardChecks.exact(reference, body.bytes());
        var schema = EffectJson.parse(body).get("schema");
        if (schema == null || !schema.isTextual() || !(SCHEMA.equals(schema.textValue()) || RECONCILIATION_SCHEMA.equals(schema.textValue()))) return java.util.Optional.empty();
        return java.util.Optional.of(load(receipt, archive, frames));
    }
    public static Original load(ActionReceipt receipt, ActionPorts.OutcomeArchive archive, FrameLoader frames) {
        ArchivedBasis archived=archivedBasis(receipt,archive);
        var settled=archived.settled();var effect=archived.effect();ObjectNode row=archived.row();
        Complete before = frames.load(decode(row.get("before")), archive), after = frames.load(decode(row.get("after")), archive);
        StrictJson.require(before.identity().equals(receipt.command().before()) && before.source().equals(receipt.command().source())
                && before.sessionId().equals(receipt.command().sessionId()) && before.originalEvidence().equals(settled.attempt().guard().nativeEvidence()), "rebuilt original before frame differs");
        StrictJson.require(after.identity().equals(effect.after()) && after.source().equals(effect.source()) && after.sessionId().equals(effect.sessionId())
                && after.observedAt().equals(effect.observedAt()) && after.originalEvidence().equals(effect.originalEvidence()), "rebuilt original after frame differs");
        var pair = new NativeEffectSnapshots.Pair(before, after);
        java.util.Optional<GuardEvidence> reconciliation = reconciliationGuard(effect, archive);
        reconciliation.ifPresent(guard -> requireReconciliation(receipt.command(), settled.attempt(), after, guard));
        return new Original(pair, archived.reads(), archived.compatible(), archived.retained(), reconciliation);
    }
    /** Exact archived DATA only. This retains the same basis, read and material closure checks as load;
     * it does not reconstruct physical frames or grant domain, history membership or Readiness authority. */
    public static List<PlanningReadReceipt> archivedReads(ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
        return archivedBasis(receipt,archive).reads();
    }
    private record ArchivedBasis(ActionState.Settled settled,ActionState.EffectObservation effect,ObjectNode row,
            List<PlanningReadReceipt> reads,RawJson compatible,List<ExactRef> retained) { }
    private static ArchivedBasis archivedBasis(ActionReceipt receipt,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(receipt.state() instanceof ActionState.Settled, "ordinary effect basis requires its original primitive settlement");
        var settled = (ActionState.Settled) receipt.state();
        StrictJson.require(settled.settlement() instanceof ActionState.Applied, "ordinary effect basis cannot prove a control, frontend or rejection branch");
        var effect = ((ActionState.Applied) settled.settlement()).observation();
        StrictJson.require(!effect.supportingEvidence().isEmpty() && effect.supportingEvidence().size() <= 17, "ordinary effect requires its explicit basis and bounded original material closure");
        ExactRef reference = effect.supportingEvidence().getFirst(); RawJson body = archive.loadMaterial(reference); RootGuardChecks.exact(reference, body.bytes());
        ObjectNode row = decodeBasis(body);
        StrictJson.require(receipt.bodySha256().equals(StrictJson.text(row.get("command_body_sha256")))
                && settled.attempt().requestId().equals(StrictJson.text(row.get("request_id"))), "original effect basis crossed the canonical command/request");
        FrameBasis beforeBasis=decode(row.get("before")),afterBasis=decode(row.get("after"));
        StrictJson.require(beforeBasis.nativeFrame().equals(settled.attempt().guard().nativeEvidence())
                &&afterBasis.nativeFrame().equals(effect.originalEvidence()),"archived effect basis crossed the actual original native frames");
        for(FrameBasis basis:List.of(beforeBasis,afterBasis)) {
            RootGuardChecks.exact(basis.nativeFrame(),archive.loadNativeFrame(basis.nativeFrame()));
            RootGuardChecks.exact(basis.driverFacts(),archive.loadFullMaterial(basis.driverFacts()).bytes());
        }
        StrictJson.require(row.get("independent_reads") != null && row.get("independent_reads").isArray() && row.get("independent_reads").size() <= 16, "actual independent-read references required");
        List<PlanningReadReceipt> reads = new ArrayList<>(); var requestIds = new java.util.HashSet<String>();
        for (var value : row.get("independent_reads")) {
            ExactRef readRef = ExactRef.fromJson(value); PlanningReadReceipt read = archive.loadRead(readRef);
            StrictJson.require(archive.readReferenceOf(read).equals(readRef) && requestIds.add(read.requestId())
                    && !read.requestId().equals(settled.attempt().requestId()), "independent read identity changed");
            NativeRecordedEvidenceVerifier.requireRead(read, archive); reads.add(read);
        }
        ExactRef material = ExactRef.fromJson(row.get("compatible_material")); RawJson compatible = archive.loadMaterial(material); RootGuardChecks.exact(material, compatible.bytes());
        var materials = row.get("supporting_materials");
        StrictJson.require(materials != null && materials.isArray() && materials.size() <= 16, "explicit bounded original supporting materials required");
        List<ExactRef> retained = new ArrayList<>(); var uniqueMaterials = new java.util.HashSet<ExactRef>();
        for (var value : materials) {
            ExactRef ref = ExactRef.fromJson(value); StrictJson.require(!ref.equals(reference) && uniqueMaterials.add(ref), "duplicate or recursive supporting material");
            RootGuardChecks.exact(ref, archive.loadMaterial(ref).bytes()); retained.add(ref);
        }
        List<ExactRef> exactClosure = new ArrayList<>(); exactClosure.add(reference); exactClosure.addAll(retained);
        StrictJson.require(effect.supportingEvidence().equals(exactClosure), "receipt material custody differs from the original explicit evidence closure");
        return new ArchivedBasis(settled,effect,row,List.copyOf(reads),compatible,List.copyOf(retained));
    }
    /** Typed DATA extraction for physical custody. Qualification must call the actual Root verifier. */
    public static java.util.Optional<GuardEvidence> reconciliationGuard(ActionState.EffectObservation effect, ActionPorts.OutcomeArchive archive) {
        if (effect.supportingEvidence().isEmpty()) return java.util.Optional.empty();
        ExactRef reference = effect.supportingEvidence().getFirst(); RawJson body = archive.loadMaterial(reference);
        RootGuardChecks.exact(reference, body.bytes()); var value = EffectJson.parse(body); var schema = value.get("schema");
        if (schema == null || !schema.isTextual() || !RECONCILIATION_SCHEMA.equals(schema.textValue())) return java.util.Optional.empty();
        ObjectNode row = decodeBasis(body); GuardEvidence guard = CommandOriginCodec.guard(row.get("reconciliation_guard"));
        StrictJson.require(guard.origin() instanceof CommandOrigin.Reconciliation && guard.nativeEvidence().equals(effect.originalEvidence())
                && guard.origin().requireReconciliation().factual().equals(effect.after()) && guard.source().equals(effect.source())
                && guard.sessionId().equals(effect.sessionId()), "reconciliation basis changed its actual effect frame/source/session");
        return java.util.Optional.of(guard);
    }
    /** Explicit mixed-plane references for the sole writer event pin vector; parsing grants no authority. */
    public static List<ExactRef> reconciliationReferences(ActionState.EffectObservation effect, ActionPorts.OutcomeArchive archive) {
        var guard = reconciliationGuard(effect, archive);
        if (guard.isEmpty()) return List.of();
        GuardEvidence original = guard.orElseThrow(); var identity = original.origin().requireReconciliation();
        var references = new java.util.LinkedHashSet<ExactRef>();
        references.add(original.nativeEvidence()); references.add(original.capabilityEvidence()); references.addAll(original.supportingEvidence());
        references.addAll(identity.evidence().originals()); references.add(identity.pending().originalReceipt()); references.add(identity.pending().originalBeforeDriver());
        return List.copyOf(references);
    }
    private static ObjectNode decodeBasis(RawJson body) {
        var value = EffectJson.parse(body); String schema = StrictJson.text(value.get("schema"));
        if (SCHEMA.equals(schema)) return StrictJson.object(value, V2_FIELDS);
        StrictJson.require(RECONCILIATION_SCHEMA.equals(schema), "unregistered native effect basis schema");
        var fields = new java.util.HashSet<>(V2_FIELDS); fields.add("reconciliation_guard");
        return StrictJson.object(value, Set.copyOf(fields));
    }
    private static void requireReconciliation(ActionCommand command, ActionState.Attempt attempt, Complete after, GuardEvidence guard) {
        StrictJson.require(guard.origin() instanceof CommandOrigin.Reconciliation, "actual pending push guard is required");
        var identity = guard.origin().requireReconciliation(); var pending = identity.pending();
        StrictJson.require(pending.actionId().equals(command.actionId()) && pending.bodySha256().equals(ActionCodec.bodySha256(command))
                && pending.requestId().equals(attempt.requestId()) && pending.originalBefore().equals(command.before())
                && guard.operation().equals(command.operation()) && guard.authorityId().equals(attempt.guard().authorityId())
                && identity.factual().equals(after.identity()) && identity.source().equals(after.source()) && identity.sessionId().equals(after.sessionId())
                && identity.connectionGeneration().equals(after.connectionGeneration()) && identity.nativeEvidence().equals(after.originalEvidence())
                && identity.evidence().observationManifest().equals(basis(after).driverFacts()), "pending push guard crossed the original action or actual after frame");
    }
    public static FrameBasis basis(Complete frame) {
        Objects.requireNonNull(frame);
        var original = frame.semantic().get("java_driver_facts_evidence");
        StrictJson.require(original != null && original != org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,
                "complete original Driver facts manifest was not archived");
        return new FrameBasis(frame.originalEvidence(), DriverObservationEvidenceReader.reference(original));
    }
    private static ObjectNode json(FrameBasis basis) { var row = StrictJson.object(); row.set("native_frame", basis.nativeFrame().toJson()); row.set("driver_facts", basis.driverFacts().toJson()); return row; }
    private static FrameBasis decode(com.fasterxml.jackson.databind.JsonNode value) { var row = StrictJson.object(value, Set.of("native_frame", "driver_facts")); return new FrameBasis(ExactRef.fromJson(row.get("native_frame")), ExactRef.fromJson(row.get("driver_facts"))); }
    public static void requireSame(ActionState.Settlement proposed, NativeEffectRegistry.Projected replayed, RawJson originalCompatible) {
        StrictJson.require(proposed instanceof ActionState.Applied && replayed.result() instanceof ActionPorts.EffectObserved, "archived domain replay did not independently observe an applied effect");
        StrictJson.require(((ActionState.Applied) proposed).observation().equals(((ActionPorts.EffectObserved) replayed.result()).observation()), "archived native/material replay differs from the proposed effect");
        StrictJson.require(replayed.compatibleResult().equals(java.util.Optional.of(originalCompatible)), "archived domain replay differs from the original material history projection");
    }
}
