package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Immutable full-frame basis. The Root must install its independent archived domain verifier. */
public final class LifeAdvanceEvidence {
    public static final String SCHEMA = "xar.ck3.java-life-advance-evidence/v2";
    public static final String LEGACY_QUERY_SCHEMA = "xar.ck3.java-life-advance-evidence/v1";
    private static final Set<String> BASIS_FIELDS = Set.of("schema", "action_body_sha256", "starting", "ending", "progress_status", "clock_read", "children", "compatible_result");
    private LifeAdvanceEvidence() { }
    public record FrameRecord(ObservationIdentity identity, ObservationProvenance provenance, Instant observedAt,
            ExactRef nativeFrame, ExactRef driverFacts, ExactRef semantic) {
        public FrameRecord {
            Objects.requireNonNull(identity); Objects.requireNonNull(provenance); Objects.requireNonNull(observedAt);
            Objects.requireNonNull(nativeFrame); Objects.requireNonNull(driverFacts); Objects.requireNonNull(semantic);
            require(nativeFrame.bytes() > 0 && driverFacts.bytes() > 0 && semantic.bytes() > 0, "complete original archived frame basis required");
            provenance.validate(identity, nativeFrame);
        }
    }
    /** DATA only: both values are the identical already archived compatible original, never a new report or authority. */
    public record OriginalResult(ExactRef original, RawJson body) {
        public OriginalResult {
            Objects.requireNonNull(original); Objects.requireNonNull(body);
            require(original.bytes() == body.bytes().length && original.sha256().equals(DriverJson.sha256(body.bytes())),
                    "recorded Life result differs from its actual archived exact reference");
        }
    }
    /** Complete replayed original frame records. This grants no current observation, writer or Driver publication authority. */
    public record Recorded(FrameRecord starting, FrameRecord ending, Optional<OriginalResult> originalCompatible) {
        public Recorded { Objects.requireNonNull(starting); Objects.requireNonNull(ending); Objects.requireNonNull(originalCompatible); }
    }
    /** Must rebuild from the exact native packet and Driver facts manifest using the real assembler. */
    @FunctionalInterface public interface BoundFrameVerifier {
        AdvanceObservationPort.Frame rebuild(ActionCommand parent, FrameRecord retained, ActionPorts.OutcomeArchive archive);
    }
    /** Reads the versioned durable Root guard basis. Historical guards without it return empty. */
    @FunctionalInterface public interface EntryFrameReader {
        Optional<AdvanceObservationPort.Frame> read(ActionCommand parent, GuardEvidence guard, ActionPorts.OutcomeArchive archive);
        /** Existing canonical primitive's independently observed after-frame; no Game sampling or dispatch. */
        default Optional<AdvanceObservationPort.Frame> readChild(ActionReceipt child, ActionPorts.OutcomeArchive archive) {
            return Optional.empty();
        }
    }
    public static ExactRef preserve(ActionCommand parent, AdvanceObservationPort.Frame starting,
            AdvanceObservationPort.Frame ending, AdvanceClock.ProgressStatus progress, Optional<ClockStatusRead.Observation> clockRead,
            List<ActionReceipt> children, Optional<ExactRef> compatibleResult, ActionPorts.OutcomeArchive archive) {
        require(starting.identity().equals(parent.before()), "advance evidence did not retain the actual immutable entry frame");
        List<Value> receipts = new ArrayList<>();
        for (ActionReceipt child : children) {
            require(child.settled(), "unresolved child cannot become completed advance evidence");
            receipts.add(ref(archive.preserveReceipt(child)));
        }
        Obj body = new Obj(Map.of("schema", new Text(SCHEMA), "action_body_sha256", new Text(ActionCodec.bodySha256(parent)),
                "starting", frame(preserveFrame(starting, archive)), "ending", frame(preserveFrame(ending, archive)),
                "progress_status", new Text(progress.name()),
                "clock_read", clockRead.<Value>map(value -> ref(archive.preserveRead(value.receipt()))).orElse(Nil.INSTANCE),
                "children", new Arr(receipts), "compatible_result", compatibleResult.<Value>map(LifeAdvanceEvidence::ref).orElse(Nil.INSTANCE)));
        return archive.preserveMaterial(new RawJson(DriverJson.encode(body)));
    }
    static FrameRecord preserveFrame(AdvanceObservationPort.Frame value, ActionPorts.OutcomeArchive archive) {
        Value manifest = value.semantic().get("java_driver_facts_evidence");
        require(manifest instanceof Obj, "complete semantic frame lacks its actual Driver facts evidence manifest");
        ExactRef driverFacts = ExactRef.fromJson(toNode(manifest));
        return new FrameRecord(value.identity(), value.provenance(), value.observedAt(), value.originalEvidence(), driverFacts,
                archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(value.semantic()))));
    }
    /** Rebuild the actual settled endpoint through this same codec and the installed full Driver loader.
     * Canonical membership and complete timeline qualification remain the caller's same-session Root verifier.
     */
    public static AdvanceObservationPort.Frame endingFrame(ActionReceipt actualCanonical, ActionPorts.OutcomeArchive archive,
            BoundFrameVerifier sameRootFrames) {
        Objects.requireNonNull(actualCanonical); Objects.requireNonNull(archive); Objects.requireNonNull(sameRootFrames);
        require(actualCanonical.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED
                && actualCanonical.applied().isPresent() && LifeAdvanceComposite.accepts(actualCanonical.command().operation().value()),
                "completed life gameplay receipt required; UNKNOWN/control-only has no completed endpoint");
        ActionState.EffectObservation effect = actualCanonical.applied().orElseThrow().observation();
        require(effect.observerSchema().equals(AdvancePlan.OBSERVER) && effect.supportingEvidence().size() == 1,
                "completed life endpoint lacks the sole complete archived basis");
        Obj body = DriverJson.object(archive.loadMaterial(effect.supportingEvidence().getFirst()).bytes(), RawJson.MAXIMUM_BYTES);
        require(body.members().keySet().equals(BASIS_FIELDS),
                "completed life basis fields differ");
        boolean legacy = new Text(LEGACY_QUERY_SCHEMA).equals(body.get("schema"));
        require((legacy || new Text(SCHEMA).equals(body.get("schema")))
                && new Text(actualCanonical.bodySha256()).equals(body.get("action_body_sha256")),
                "completed life basis crossed its original action body");
        AdvanceObservationPort.Frame ending = restore(actualCanonical.command(),
                decodeFrame(object(body.get("ending"), "ending"), legacy), archive, sameRootFrames);
        require(ending.identity().equals(effect.after()) && ending.source().equals(effect.source())
                && ending.sessionId().equals(effect.sessionId()) && ending.provenance().equals(effect.provenance())
                && ending.observedAt().equals(effect.observedAt()) && ending.originalEvidence().equals(effect.originalEvidence()),
                "full rebuilt ending frame differs from the canonical applied observation");
        return ending;
    }
    public static void verifyRecorded(ActionReceipt receipt, ActionPorts.OutcomeArchive archive, BoundFrameVerifier frames,
            AdvanceClockArchivedReplay timeline) {
        readRecorded(receipt, archive, frames, timeline);
    }
    /** Existing canonical originals only, including the zero-day composite-control branch.
     * The same complete domain replay precedes this DATA return. Root separately proves canonical membership
     * under its original writer and rebuilds each full Driver/native frame through its sole FrameLoader.
     * UNKNOWN or ACK-only receipts fail before archive access; reconciliation without its old result stays absent.
     * No new material, native query, current frame or publication is produced here.
     */
    public static Recorded readRecorded(ActionReceipt receipt, ActionPorts.OutcomeArchive archive, BoundFrameVerifier frames,
            AdvanceClockArchivedReplay timeline) {
        Objects.requireNonNull(archive); Objects.requireNonNull(frames); Objects.requireNonNull(timeline);
        require(LifeAdvanceComposite.accepts(receipt.command().operation().value()), "life verifier cannot verify another operation");
        ActionState.EffectObservation effect = ActionEffects.observation(receipt).orElseThrow(() -> new IllegalArgumentException("advance has no semantic terminal observation"));
        require(effect.supportingEvidence().size() == 1, "advance needs one exact complete archived basis");
        ExactRef basisRef = effect.supportingEvidence().getFirst();
        Obj body = DriverJson.object(archive.loadMaterial(basisRef).bytes(), RawJson.MAXIMUM_BYTES);
        require(body.members().keySet().equals(BASIS_FIELDS), "life basis fields differ");
        boolean legacyQuery = new Text(LEGACY_QUERY_SCHEMA).equals(body.get("schema"));
        require((new Text(SCHEMA).equals(body.get("schema")) || legacyQuery)
                && new Text(receipt.bodySha256()).equals(body.get("action_body_sha256")), "life evidence crossed the exact durable body");
        ActionCommand parent = receipt.command();
        FrameRecord startingRecord = decodeFrame(object(body.get("starting"), "starting"), legacyQuery);
        FrameRecord endingRecord = decodeFrame(object(body.get("ending"), "ending"), legacyQuery);
        AdvanceObservationPort.Frame starting = restore(parent, startingRecord, archive, frames);
        AdvanceObservationPort.Frame ending = restore(parent, endingRecord, archive, frames);
        require(starting.identity().equals(parent.before()), "archived starting frame differs from the original action");
        AdvanceWait.binding(parent, starting, ending);
        require(AdvancePolicy.truth(ending.semantic(), "paused")
                && ending.identity().frame().identity().player().equals(parent.before().frame().identity().player()), "life settlement requires actual paused same-actor state");
        require(receipt.state() instanceof ActionState.CompositeSettled, "life evidence requires the retained composite execution");
        CompositeExecution execution = ((ActionState.CompositeSettled) receipt.state()).execution();
        List<Value> refs = array(body.get("children"), "children");
        require(refs.size() == execution.children().size(), "archived life children are incomplete");
        List<ActionReceipt> children = new ArrayList<>();
        for (int index = 0; index < refs.size(); index++) {
            ActionReceipt child = archive.loadReceipt(exactRef(refs.get(index)));
            CompositeExecution.Child bound = execution.children().get(index);
            require(child.settled() && child.command().actionId().equals(bound.actionId()) && child.bodySha256().equals(bound.bodySha256()), "archived durable child/body is not the retained child");
            children.add(child);
        }
        AdvancePlan plan = AdvancePlan.decode(parent);
        AdvanceClock.ProgressStatus progress = AdvanceClock.ProgressStatus.valueOf(text(body.get("progress_status"), "progress_status"));
        Optional<PlanningReadReceipt> clockRead = body.get("clock_read") == Nil.INSTANCE ? Optional.empty()
                : Optional.of(archive.loadRead(exactRef(body.get("clock_read"))));
        Optional<ClockStatusRead.Observation> archivedClock = clockRead.map(value -> new ClockStatusRead.Observation(
                ClockStatusRead.decode(value.original()), value, archive.referenceOf(value.original())));
        timeline.verify(parent, plan, starting, ending, progress, archivedClock, children, archive);
        Optional<ExactRef> compatible = body.get("compatible_result") == Nil.INSTANCE ? Optional.empty() : Optional.of(exactRef(body.get("compatible_result")));
        ActionState.EffectObservation rebuilt = LifeAdvanceComposite.observation(parent, plan, ending, progress, compatible.orElse(null), List.of(basisRef));
        require(rebuilt.equals(effect), "life semantic terminal differs from the independently rebuilt archived basis");
        Optional<RawJson> result = AdvanceResult.compatibleResult(receipt, archive);
        require(result.isPresent() == compatible.isPresent(), "advance compatible result presence differs from the exact basis");
        if (result.isPresent()) {
            require(archive.materialReferenceOf(result.orElseThrow()).equals(compatible.orElseThrow()), "advance compatible material identity differs");
            Obj value = DriverJson.object(result.orElseThrow().bytes(), RawJson.MAXIMUM_BYTES);
            require(Objects.equals(value.get("war_progress_before"), AdvanceResult.warSummary(starting.semantic()))
                    && Objects.equals(value.get("war_progress_after"), AdvanceResult.warSummary(ending.semantic())), "archived war summaries differ from complete original frames");
        }
        if (receipt.state() instanceof ActionState.CompositeSettled settled && settled.settlement() instanceof ActionState.CompositeControlApplied control) {
            PlanningReadReceipt terminal = clockRead.orElseThrow(() -> new IllegalArgumentException("control terminal has no independent clock query"));
            CompositeControlObservation rebuiltControl = AdvanceClock.compositeControlTerminal(parent,
                    new ClockStatusRead.Observation(ClockStatusRead.decode(terminal.original()), terminal, archive.referenceOf(terminal.original())), children, rebuilt);
            require(rebuiltControl.equals(control.observation()), "zero-day control settlement differs from retained arm/cancel and fresh semantic proof");
        }
        return new Recorded(startingRecord, endingRecord, result.map(original ->
                new OriginalResult(archive.materialReferenceOf(original), original)));
    }
    /** Complete semantic material DATA only; current/Root qualification still requires the independent frame verifier. */
    static Obj originalSemantic(FrameRecord value, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(value); Objects.requireNonNull(archive);
        return DriverJson.object(archive.loadFullMaterial(value.semantic()).bytes(), RawJson.MAXIMUM_BYTES);
    }
    static AdvanceObservationPort.Frame restore(ActionCommand parent, FrameRecord value, ActionPorts.OutcomeArchive archive, BoundFrameVerifier verifier) {
        Obj actualSemantic = originalSemantic(value, archive);
        AdvanceObservationPort.Frame rebuilt = Objects.requireNonNull(verifier.rebuild(parent, value, archive));
        require(rebuilt.identity().equals(value.identity()) && rebuilt.source().equals(parent.source()) && rebuilt.sessionId().equals(parent.sessionId())
                && rebuilt.provenance().equals(value.provenance()) && rebuilt.observedAt().equals(value.observedAt())
                && rebuilt.originalEvidence().equals(value.nativeFrame()) && rebuilt.semantic().equals(actualSemantic)
                && exactRef(actualSemantic.get("java_driver_facts_evidence")).equals(value.driverFacts()), "complete archived native/Driver facts reconstruction differs");
        return rebuilt;
    }
    private static Obj frame(FrameRecord value) {
        return new Obj(Map.of("identity", OpportunityJsonValue.observation(value.identity()), "observation_provenance", provenance(value.provenance()),
                "observed_at_utc", new Text(value.observedAt().toString()), "native_frame", ref(value.nativeFrame()), "driver_facts", ref(value.driverFacts()), "semantic", ref(value.semantic())));
    }
    private static FrameRecord decodeFrame(Obj value, boolean legacyQuery) {
        require(value.members().keySet().equals(Set.of("identity", legacyQuery ? "read_request_id" : "observation_provenance", "observed_at_utc", "native_frame", "driver_facts", "semantic")), "archived frame fields differ");
        ObservationProvenance provenance = legacyQuery ? new ObservationProvenance.Query(text(value.get("read_request_id"), "read_request_id"))
                : ObservationProvenanceCodec.decode(toNode(value.get("observation_provenance")));
        return new FrameRecord(ProposalLifecycleCodec.decodeObservation(toNode(value.get("identity"))), provenance,
                Instant.parse(StrictJson.utc(text(value.get("observed_at_utc"), "observed_at_utc"))), exactRef(value.get("native_frame")), exactRef(value.get("driver_facts")), exactRef(value.get("semantic")));
    }
    private static Value provenance(ObservationProvenance value) { return org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(ObservationProvenanceCodec.encode(value))); }
    private static Value ref(ExactRef value) { return org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(value.toJson())); }
    private static ExactRef exactRef(Value value) { return ExactRef.fromJson(toNode(object(value, "exact artifact reference"))); }
    private static final class OpportunityJsonValue {
        private OpportunityJsonValue() { }
        static Value observation(ObservationIdentity value) { return org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(ProposalLifecycleCodec.observation(value))); }
    }
}

