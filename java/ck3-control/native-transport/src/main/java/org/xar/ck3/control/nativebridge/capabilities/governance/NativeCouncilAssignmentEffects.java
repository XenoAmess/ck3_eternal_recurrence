package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.council.*;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** One held Council transaction: durable helper STATUS, later published frame, durable receipt query/STATUS. */
public final class NativeCouncilAssignmentEffects implements NativeEffectRegistry.Observer {
    public static final String REJECTION_SCHEMA = "xar.java.council-assignment-native-rejection/v1";
    public static final String SCHEMA = "xar.java.council-assignment-original-basis/v1";
    private final CouncilContinuationCoordinator continuation;
    private final CouncilContinuationPolicy policy;
    private final NativeEffectSnapshots snapshots;
    private final ActionPorts.OutcomeArchive archive;
    private final NativeEffectEvidence.FrameLoader frames;
    private final Supplier<ContinuityStorePort.Session> originalSession;
    private final Clock clock;
    private final int maximumContinuations;
    public NativeCouncilAssignmentEffects(CouncilContinuationCoordinator continuation, CouncilContinuationPolicy policy,
            NativeEffectSnapshots snapshots, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames,
            Supplier<ContinuityStorePort.Session> originalSession, Clock clock, int maximumContinuations) {
        this.continuation = Objects.requireNonNull(continuation); this.policy = Objects.requireNonNull(policy); this.snapshots = Objects.requireNonNull(snapshots);
        this.archive = Objects.requireNonNull(archive); this.frames = Objects.requireNonNull(frames); this.originalSession = Objects.requireNonNull(originalSession);
        this.clock = Objects.requireNonNull(clock); StrictJson.require(maximumContinuations >= 3 && maximumContinuations <= MAX_ACTIVE_REQUESTS, "bounded complete Council continuation budget required");
        this.maximumContinuations = maximumContinuations;
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        StrictJson.require(command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN), "exact private Council observer required");
        if (!(dispatch instanceof NativeActionPort.AckReceived original)) return NativeEffectRegistry.Projected.pending("original Council result unknown; collect its original request only", List.of(attempt.guard().nativeEvidence()));
        var context = GovernanceActionScope.current(command); var same = context.session(command); var scope = context.mailbox(command);
        var results = new ArrayList<CouncilContinuationReceipt>();
        try {
            CouncilContinuationPolicy.requireOriginalPending(command, attempt, original);
            var prior = continuation.retained(same);
            // A resumed operation has no live mailbox authority. Existing rows are not reissued under new nonces.
            StrictJson.require(prior.isEmpty() || !prior.getFirst().request().scope().parentActionId().equals(command.actionId()), "existing Council continuation chain is collect-only outside its original live call");
            // The canonical core alone may rotate a different already-settled original scope before first issue.
            CouncilContinuationPolicy.Progress progress = CouncilContinuationPolicy.replay(command, attempt, original, List.of(), archive.withSession(same));
            for (int count = 0; progress.next().isPresent(); count++) {
                StrictJson.require(count < maximumContinuations && clock.instant().isBefore(ActionObservationWindow.deadline(command)), "Council continuation deadline/budget exhausted; original requests retained, no requeue");
                Stage next = progress.next().orElseThrow();
                if (next == Stage.RECEIPT_QUERY) snapshots.read(command, attempt); // require actual newer Native+Driver material before receipt issue
                CouncilContinuationReceipt receipt = continuation.continueOnce(same, command, attempt, next, ActionObservationWindow.deadline(command)); results.add(receipt);
                if (receipt.status() != Status.ACK) return NativeEffectRegistry.Projected.pending("Council continuation result UNKNOWN; collect exact original ID only", List.of(receipt.latestRecord()));
                prior = continuation.retained(same);
                progress = CouncilContinuationPolicy.replay(command, attempt, original, prior, archive.withSession(same));
                if (progress.next().filter(stage -> stage == Stage.HELPER_STATUS || stage == Stage.RECEIPT_STATUS).isPresent()) {
                    try { Thread.sleep(10); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); return NativeEffectRegistry.Projected.pending("Council continuation interrupted; no new request after scope exits", List.of(receipt.latestRecord())); }
                }
            }
            if (progress.helper().filter(value -> value.status() == CouncilActionCodec.AckStatus.REJECTED_BEFORE_SUBMIT).isPresent()) {
                var helper = progress.helper().orElseThrow();
                if (helper.disposition() != CouncilActionCodec.HelperDisposition.REJECTED_WITHOUT_INVOCATION)
                    return NativeEffectRegistry.Projected.pending("Council helper remains unresolved: " + helper.disposition() + "; preserve original and do not replay", results.stream().map(CouncilContinuationReceipt::latestRecord).toList());
                var bound = archive.withSession(same);
                continuation.verifyCanonicalChain(same, same.head(), results);
                policy.requirePreflight(command, attempt, results.getFirst().request().supportingEvidence(), bound, original);
                ExactRef basis = preserveRejection(command, attempt, results, helper, bound);
                var rejected = reject(command, attempt, helper, basis);
                // The real producer retains no pending ACK for this rejected helper. There is no receipt RPC to issue.
                scope.complete(results.getLast().outcome().orElseThrow());
                return rejected;
            }
            StrictJson.require(progress.receipt().filter(value -> value.status() == CouncilActionCodec.ReceiptStatus.APPLIED).isPresent(), "Council original native receipt did not verify incumbent assignment");
            var pair = snapshots.read(command, attempt); var boundArchive = archive.withSession(same);
            continuation.verifyCanonicalChain(same, same.head(), results);
            policy.requirePreflight(command, attempt, results.getFirst().request().supportingEvidence(), boundArchive, original);
            RawJson compatible = compatible(progress.receipt().orElseThrow());
            var projected = project(command, attempt, pair, progress.receipt().orElseThrow(), compatible, List.of());
            ExactRef basis = preserve(command, attempt, pair, results, compatible, boundArchive);
            projected = NativeEffectSnapshots.withEvidence(projected, List.of(basis));
            NativeActionPort.DispatchOutcome last = results.getLast().outcome().orElseThrow();
            // All result/event/body/native-frame originals are durable before releasing the one mailbox.
            scope.complete(last);
            return projected;
        } catch (IOException failure) { throw new UncheckedIOException("original Council continuation/effect evidence unavailable; never replay", failure); }
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(ExactRef actualDefinitionSource) {
        return archivedVerifier(actualDefinitionSource, continuation, policy, frames, originalSession);
    }
    /** Pure archive replay is available before a new Game has any adopted Driver; it captures no old Game owner. */
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(ExactRef actualDefinitionSource,
            CouncilContinuationCoordinator continuation, CouncilContinuationPolicy policy,
            NativeEffectEvidence.FrameLoader frames, Supplier<ContinuityStorePort.Session> originalSession) {
        return new NativeRecordedEvidenceVerifier.Binding(new OperationKey(CouncilActionCodec.PRIVATE_ASSIGN), actualDefinitionSource,
                (head, parent, archive) -> {
                    try {
                        var same = originalSession.get(); var settled = (ActionState.Settled) parent.state();
                        if (settled.settlement() instanceof ActionState.Rejected rejected) {
                            verifyRejected(same, head, parent, settled, rejected, continuation, policy, archive);
                            return;
                        }
                        StrictJson.require(settled.settlement() instanceof ActionState.Applied && settled.dispatch() instanceof NativeActionPort.AckReceived, "private Council archived verifier requires its actual primitive effect/original pending ACK");
                        var effect = ((ActionState.Applied) settled.settlement()).observation();
                        StrictJson.require(effect.supportingEvidence().size() == 1, "private Council requires one complete original evidence leaf");
                        RawJson body = exact(effect.supportingEvidence().getFirst(), archive);
                        var row = StrictJson.object(StrictJson.parse(body.bytes()), Set.of("schema", "command_body_sha256", "original_request_id", "before", "after", "continuations", "compatible_material"));
                        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))) && parent.bodySha256().equals(StrictJson.text(row.get("command_body_sha256")))
                                && settled.attempt().requestId().equals(StrictJson.text(row.get("original_request_id"))), "Council evidence leaf crossed canonical parent/original attempt");
                        Complete before = frames.load(frameBasis(row.get("before")), archive), after = frames.load(frameBasis(row.get("after")), archive);
                        StrictJson.require(before.identity().equals(parent.command().before()) && before.source().equals(parent.command().source()) && before.sessionId().equals(parent.command().sessionId())
                                && before.originalEvidence().equals(settled.attempt().guard().nativeEvidence()), "Council archived original before-frame changed");
                        StrictJson.require(after.identity().equals(effect.after()) && after.source().equals(effect.source()) && after.sessionId().equals(effect.sessionId())
                                && after.observedAt().equals(effect.observedAt()) && after.originalEvidence().equals(effect.originalEvidence()), "Council archived actual post-frame changed");
                        var pair = new NativeEffectSnapshots.Pair(before, after); var chain = decodeChain(row.get("continuations"), archive);
                        continuation.verifyCanonicalChain(same, head, chain);
                        policy.requirePreflight(parent.command(), settled.attempt(), chain.getFirst().request().supportingEvidence(), archive, (NativeActionPort.AckReceived) settled.dispatch());
                        var retained = chain.stream().map(receipt -> new Retained(receipt.latestRecord(), CouncilContinuationCodec.decodeEntry(exact(receipt.latestRecord(), archive).bytes()))).toList();
                        var progress = CouncilContinuationPolicy.replay(parent.command(), settled.attempt(), (NativeActionPort.AckReceived) settled.dispatch(), retained, archive);
                        StrictJson.require(progress.next().isEmpty() && progress.receipt().isPresent(), "archived Council chain is incomplete");
                        RawJson compatible = exact(ExactRef.fromJson(row.get("compatible_material")), archive);
                        StrictJson.require(compatible.equals(compatible(progress.receipt().orElseThrow())), "Council history projection differs from original native receipt");
                        var replayed = project(parent.command(), settled.attempt(), pair, progress.receipt().orElseThrow(), compatible, effect.supportingEvidence());
                        NativeEffectEvidence.requireSame(settled.settlement(), replayed, compatible);
                    } catch (IOException failure) { throw new UncheckedIOException("canonical Council continuation replay unavailable", failure); }
                });
    }
    private static NativeEffectRegistry.Projected reject(ActionCommand command, ActionState.Attempt attempt,
            CouncilActionCodec.Ack helper, ExactRef original) {
        StrictJson.require(helper.status() == CouncilActionCodec.AckStatus.REJECTED_BEFORE_SUBMIT && !helper.helperInvoked()
                && !helper.queueAcceptanceObserved() && !helper.verificationPending()
                && helper.disposition() == CouncilActionCodec.HelperDisposition.REJECTED_WITHOUT_INVOCATION,
                "only source-qualified genuine noninvocation may settle Council rejection");
        var rejected = new ActionState.Rejected(attempt.requestId(), "native_council_rejected_before_submit:" + helper.failure(), original);
        ActionEffects.validate(command, attempt, rejected);
        return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(rejected), Optional.empty());
    }
    private static ExactRef preserveRejection(ActionCommand command, ActionState.Attempt attempt, List<CouncilContinuationReceipt> receipts,
            CouncilActionCodec.Ack helper, ActionPorts.OutcomeArchive archive) {
        var row = StrictJson.object().put("schema", REJECTION_SCHEMA).put("command_body_sha256", ActionCodec.bodySha256(command)).put("original_request_id", attempt.requestId());
        var chain = row.putArray("continuations");
        for (var receipt : receipts) {
            var item = chain.addObject(); item.set("entry", receipt.latestRecord().toJson());
            item.set("result_domain_payload", receipt.resultDomainPayload().toJson()); item.set("result_event", receipt.resultEvent().toJson());
        }
        row.set("compatible_material", archive.preserveMaterial(new RawJson(helper.original().bytes())).toJson());
        RawJson body = new RawJson(StrictJson.canonical(row)); ExactRef ref = archive.preserveMaterial(body);
        StrictJson.require(body.equals(archive.loadMaterial(ref)), "Council native rejection archive changed"); return ref;
    }
    private static void verifyRejected(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent,
            ActionState.Settled settled, ActionState.Rejected rejected, CouncilContinuationCoordinator continuation,
            CouncilContinuationPolicy policy, ActionPorts.OutcomeArchive archive) throws IOException {
        var row = StrictJson.object(StrictJson.parse(exact(rejected.originalEvidence(), archive).bytes()), Set.of("schema", "command_body_sha256", "original_request_id", "continuations", "compatible_material"));
        StrictJson.require(REJECTION_SCHEMA.equals(CouncilCodec.text(row, "schema")) && parent.bodySha256().equals(CouncilCodec.text(row, "command_body_sha256"))
                && settled.attempt().requestId().equals(CouncilCodec.text(row, "original_request_id")) && settled.dispatch() instanceof NativeActionPort.AckReceived, "Council rejection crossed its canonical original command/attempt");
        var chain = decodeChain(row.get("continuations"), archive);
        continuation.verifyCanonicalChain(same, head, chain);
        policy.requirePreflight(parent.command(), settled.attempt(), chain.getFirst().request().supportingEvidence(), archive,
                (NativeActionPort.AckReceived) settled.dispatch());
        var retained = chain.stream().map(receipt -> new Retained(receipt.latestRecord(), CouncilContinuationCodec.decodeEntry(exact(receipt.latestRecord(), archive).bytes()))).toList();
        var progress = CouncilContinuationPolicy.replay(parent.command(), settled.attempt(), (NativeActionPort.AckReceived) settled.dispatch(), retained, archive);
        StrictJson.require(progress.next().isEmpty() && progress.receipt().isEmpty() && progress.helper().isPresent(), "Council rejection requires the complete original helper-only terminal chain");
        var helper = progress.helper().orElseThrow();
        RawJson compatible = exact(ExactRef.fromJson(row.get("compatible_material")), archive);
        var replayed = reject(parent.command(), settled.attempt(), helper, rejected.originalEvidence());
        StrictJson.require(replayed.result() instanceof ActionPorts.RejectionObserved actual && actual.rejection().equals(rejected)
                && replayed.compatibleResult().isEmpty() && compatible.equals(new RawJson(helper.original().bytes())), "Council original native rejection replay differs from proposed settlement");
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            CouncilActionCodec.Receipt receipt, RawJson compatible, List<ExactRef> supporting) {
        StrictJson.require(receipt.status() == CouncilActionCodec.ReceiptStatus.APPLIED, "Council ACK/rejection is not independent applied material");
        Complete after = pair.after(); var id = after.identity().frame().identity();
        StrictJson.require(receipt.postSnapshotId().equals("native:" + id.nativeRevision()) && receipt.postNativeRevision().equals(id.nativeRevision())
                && receipt.postPublicRevision().equals(id.nativeRevision()) && receipt.postDateRaw() == id.dateRaw().intValueExact()
                && receipt.ownerId() == id.player().intValueExact() && !after.observedAt().isBefore(attempt.submittedAt()), "Council receipt differs from real fresh after Native+Driver frame");
        List<ExpectedValue> actual = List.of(new ExpectedText(new FieldKey("council.position_key"), receipt.position().key()),
                new ExpectedInteger(new FieldKey("council.incumbent_character_id"), java.math.BigInteger.valueOf(receipt.incumbentId())),
                new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true));
        StrictJson.require(org.xar.ck3.control.g2.planning.ProposalLifecycle.compare(command.expected(), after.identity(), after.source(), NativeGovernanceEffects.SCHEMA, actual)
                == org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "Council actual incumbent did not meet the requested postcondition");
        var observation = new ActionState.EffectObservation(after.identity(), after.source(), after.sessionId(), NativeGovernanceEffects.SCHEMA, actual,
                new ObservationProvenance.Push(after.identity().frame().snapshotId(), id.nativeRevision(), after.originalEvidence()), after.observedAt(), after.originalEvidence(), supporting);
        ActionEffects.validate(command, attempt, new ActionState.Applied(observation));
        return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(observation), Optional.of(compatible));
    }
    private static ExactRef preserve(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair,
            List<CouncilContinuationReceipt> receipts, RawJson compatible, ActionPorts.OutcomeArchive archive) {
        var body = StrictJson.object().put("schema", SCHEMA).put("command_body_sha256", ActionCodec.bodySha256(command)).put("original_request_id", attempt.requestId());
        body.set("before", frame(NativeEffectEvidence.basis(pair.before()))); body.set("after", frame(NativeEffectEvidence.basis(pair.after())));
        var chain = body.putArray("continuations");
        for (CouncilContinuationReceipt receipt : receipts) chain.addObject().set("entry", receipt.latestRecord().toJson());
        for (int index = 0; index < receipts.size(); index++) {
            ObjectNode item = (ObjectNode) chain.get(index); CouncilContinuationReceipt receipt = receipts.get(index);
            item.set("result_domain_payload", receipt.resultDomainPayload().toJson()); item.set("result_event", receipt.resultEvent().toJson());
        }
        body.set("compatible_material", archive.preserveMaterial(compatible).toJson());
        RawJson material = new RawJson(StrictJson.canonical(body)); ExactRef result = archive.preserveMaterial(material);
        StrictJson.require(material.equals(archive.loadMaterial(result)), "Council effect leaf archive changed"); return result;
    }
    private static List<CouncilContinuationReceipt> decodeChain(JsonNode raw, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(raw.isArray() && raw.size() >= 1 && raw.size() <= MAX_ACTIVE_REQUESTS, "complete bounded Council issued/result chain required");
        var result = new ArrayList<CouncilContinuationReceipt>();
        for (JsonNode item : raw) {
            ObjectNode row = StrictJson.object(item, Set.of("entry", "result_domain_payload", "result_event")); ExactRef ref = ExactRef.fromJson(row.get("entry"));
            Entry entry = CouncilContinuationCodec.decodeEntry(exact(ref, archive).bytes());
            result.add(new CouncilContinuationReceipt(entry.request(), entry.status(), entry.outcome().map(archive::load), entry.issued().orElseThrow(), ref,
                    ExactRef.fromJson(row.get("result_domain_payload")), ExactRef.fromJson(row.get("result_event"))));
        }
        return List.copyOf(result);
    }
    private static RawJson compatible(CouncilActionCodec.Receipt receipt) { return new RawJson(receipt.original().bytes()); }
    private static ObjectNode frame(NativeEffectEvidence.FrameBasis frame) { var row = StrictJson.object(); row.set("native_frame", frame.nativeFrame().toJson()); row.set("driver_facts", frame.driverFacts().toJson()); return row; }
    private static NativeEffectEvidence.FrameBasis frameBasis(JsonNode raw) { var row = StrictJson.object(raw, Set.of("native_frame", "driver_facts")); return new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")), ExactRef.fromJson(row.get("driver_facts"))); }
    private static RawJson exact(ExactRef ref, ActionPorts.OutcomeArchive archive) { RawJson raw = archive.loadMaterial(ref); StrictJson.require(ref.bytes() == raw.bytes().length && ref.sha256().equals(ActionCodec.sha256(raw.bytes())), "Council original material bytes/SHA differ"); return raw; }
}
