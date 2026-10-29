package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeGovernanceEffects;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.governance.GovernanceBorrowedSession;
import org.xar.ck3.control.application.planning.governance.GovernanceCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** The existing registered read coordinator supplies both real originals; composition is a pure same-frame operation. */
public final class NativeLifestyleReadPort implements GovernanceCollector.LifestyleReadPort,
        GovernanceActionPreparation.LifestyleRefreshPort, NativeGovernanceEffects.PreparationEvidencePort {
    public static final String PREPARATION_SCHEMA = "xar.java.lifestyle-original-preflight/v1";
    private record Collected(OpportunityJson.Obj value, List<PlanningReadReceipt> reads, List<ExactRef> references) { }
    private final PlanningReadPort port;
    private final GovernancePlanningReads definitions;
    private final ActionPorts.OutcomeArchive archive;
    private final java.util.Optional<GovernanceBorrowedSession> borrowed;
    /** Action preparation already receives its exact original Session; no planning lock is opened here. */
    public NativeLifestyleReadPort(PlanningReadPort port, GovernancePlanningReads definitions, ActionPorts.OutcomeArchive archive) {
        this.port = Objects.requireNonNull(port); this.definitions = Objects.requireNonNull(definitions); this.archive = Objects.requireNonNull(archive); this.borrowed = java.util.Optional.empty();
    }
    public NativeLifestyleReadPort(PlanningReadPort port, GovernancePlanningReads definitions, ActionPorts.OutcomeArchive archive, GovernanceBorrowedSession borrowed) {
        this.port = Objects.requireNonNull(port); this.definitions = Objects.requireNonNull(definitions); this.archive = Objects.requireNonNull(archive); this.borrowed = java.util.Optional.of(Objects.requireNonNull(borrowed));
    }
    @Override public Read<OpportunityJson.Obj> formal(PlanningRequest request) {
        try { return borrowed.orElseThrow(() -> new IllegalStateException("actual planning borrowed Session is not installed")).use(request, same -> { var result = collect(same, request.before(), request.source(), request.sessionId(), request.deadline(), null); return new Known<>(result.value(), result.references()); }); }
        catch (IOException | IllegalStateException failure) { return new Unavailable<>("actual same-Session LIFE formal read unavailable: " + failure.getMessage()); }
    }
    @Override public Read<OpportunityJson.Obj> stockFocus(PlanningRequest request, String target) {
        try { return borrowed.orElseThrow(() -> new IllegalStateException("actual planning borrowed Session is not installed")).use(request, same -> { var result = collect(same, request.before(), request.source(), request.sessionId(), request.deadline(), target); return new Known<>(result.value(), result.references()); }); }
        catch (IOException | IllegalStateException failure) { return new Unavailable<>("actual same-Session LIFE state/focus read unavailable: " + failure.getMessage()); }
    }
    @Override public void verify(ContinuityStorePort.Session same, ActionCommand command) {
        var context = GovernanceActionScope.current(command); StrictJson.require(context.session(command) == same, "LIFE preparation borrowed another writer Session");
        ObjectNode args = CouncilCodec.object(StrictJson.parse(OpportunityJson.encode(command.arguments())));
        boolean focus = command.operation().value().equals(GovernanceActionPreparation.FOCUS);
        var actual = collect(same, command.before(), command.source(), command.sessionId(), command.deadline(), focus ? CouncilCodec.text(args, "target_key") : null);
        requireSelected(command, actual.value()); context.retainPreflight(command, actual.reads());
    }
    @Override public List<ExactRef> preparedEvidence(ContinuityStorePort.Session same, ActionCommand command, String originalRequestId) {
        verify(same, command);
        return archive.inSession(same, bound -> List.of(preserveOriginals(command, originalRequestId, GovernanceActionScope.current(command).preflight(command), bound)));
    }
    /** Copies real original receipt references; it grants no writer, source, readiness or submit authority. */
    public static ExactRef preserveOriginals(ActionCommand command, String originalRequestId, List<PlanningReadReceipt> originals, ActionPorts.OutcomeArchive bound) {
        boolean focus = command.operation().value().equals(GovernanceActionPreparation.FOCUS);
        StrictJson.require(focus || command.operation().value().equals(GovernanceActionPreparation.PERK), "exact LIFE preparation operation required");
        StrictJson.require(originals.size() == (focus ? 2 : 1), "complete original LIFE preparation group required");
        GovernanceReadChronology.requireOrderedReads(originals);
        var row = StrictJson.object().put("schema", PREPARATION_SCHEMA).put("command_body_sha256", ActionCodec.bodySha256(command)).put("original_request_id", StrictJson.text(originalRequestId));
        var refs = row.putArray("reads");
        for (PlanningReadReceipt read : originals) {
            NativeRecordedEvidenceVerifier.requireRead(read, bound); refs.add(bound.readReferenceOf(read).toJson());
        }
        RawJson body = new RawJson(StrictJson.canonical(row)); ExactRef ref = bound.preserveMaterial(body);
        StrictJson.require(body.equals(bound.loadMaterial(ref)), "LIFE original preparation archive changed"); return ref;
    }
    @Override public List<PlanningReadReceipt> originals(ActionCommand command, ActionState.Attempt attempt, ActionPorts.OutcomeArchive sameArchive) {
        var refs = attempt.preparedRequest().preparationEvidence();
        StrictJson.require(refs.size() == 1, "original successful LIFE preparation custody is missing; no replacement read is allowed");
        ExactRef ref = refs.getFirst(); RawJson body = sameArchive.loadMaterial(ref);
        StrictJson.require(ref.bytes() == body.bytes().length && ref.sha256().equals(ActionCodec.sha256(body.bytes())), "LIFE original preparation bytes/SHA changed");
        var row = StrictJson.object(StrictJson.parse(body.bytes()), java.util.Set.of("schema", "command_body_sha256", "original_request_id", "reads"));
        StrictJson.require(PREPARATION_SCHEMA.equals(CouncilCodec.text(row, "schema"))
                && ActionCodec.bodySha256(command).equals(CouncilCodec.text(row, "command_body_sha256"))
                && attempt.requestId().equals(CouncilCodec.text(row, "original_request_id")), "LIFE preparation custody crossed its canonical command or original attempt");
        var items = row.get("reads");
        boolean focus = command.operation().value().equals(GovernanceActionPreparation.FOCUS);
        StrictJson.require(focus || command.operation().value().equals(GovernanceActionPreparation.PERK), "exact LIFE preparation operation required");
        StrictJson.require(items.isArray() && items.size() == (focus ? 2 : 1), "complete original LIFE preparation read list required");
        var result = new ArrayList<PlanningReadReceipt>(); var ids = new java.util.HashSet<String>();
        for (var item : items) {
            ExactRef readRef = ExactRef.fromJson(item); PlanningReadReceipt read = sameArchive.loadRead(readRef);
            StrictJson.require(sameArchive.readReferenceOf(read).equals(readRef) && ids.add(read.requestId()), "LIFE preparation read identity changed or repeated");
            NativeRecordedEvidenceVerifier.requireRead(read, sameArchive); result.add(read);
        }
        return List.copyOf(result);
    }
    @Override public void verify(ActionCommand command, ActionState.Attempt attempt, List<PlanningReadReceipt> originalReads, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(originals(command, attempt, archive).equals(originalReads), "LIFE retained effect preflight differs from its durable original preparation");
        boolean focus = command.operation().value().equals(GovernanceActionPreparation.FOCUS);
        StrictJson.require(focus || command.operation().value().equals(GovernanceActionPreparation.PERK), "exact LIFE preparation evidence required");
        StrictJson.require(originalReads.size() == (focus ? 2 : 1), "complete actual LIFE preflight originals required");
        GovernanceReadChronology.requireOrderedReads(originalReads);
        var args = CouncilCodec.object(StrictJson.parse(OpportunityJson.encode(command.arguments()))); String target = focus ? CouncilCodec.text(args, "target_key") : null;
        var first = originalReads.getFirst(); requireRead(command.before(), command.source(), command.sessionId(), first, focus ? definitions.state() : definitions.formal(), archive);
        OpportunityJson.Obj actual = (focus ? definitions.state() : definitions.formal()).decode(first);
        if (focus) {
            var second = originalReads.getLast(); var contract = definitions.focus(target); requireRead(command.before(), command.source(), command.sessionId(), second, contract, archive);
            StrictJson.require(!second.requestId().equals(first.requestId()), "LIFE state and final focus reused an original request ID");
            actual = (OpportunityJson.Obj) OpportunityJson.parse(StrictJson.canonical(GovernancePlanningReads.combine(node(actual), node(contract.decode(second)))));
        }
        for (var read : originalReads) StrictJson.require(!read.requestId().equals(attempt.requestId())
                && !read.before().binding().observedAt().isAfter(attempt.submittedAt())
                && !read.original().custody().orElseThrow().responseReceived().observedAt().isAfter(attempt.submittedAt()),
                "LIFE preflight was not an actual independent completed read before the original submission");
        requireSelected(command, actual);
        StrictJson.require(attempt.preparedRequest().step().equals(command.operation().value()) && attempt.preparedRequest().requiredCapability().isEmpty()
                && GovernanceActionPreparation.lifestyleFields(command).equals(attempt.preparedRequest().additionalFields()),
                "LIFE cold preflight cannot authorize another prepared primitive or target");
    }
    private Collected collect(ContinuityStorePort.Session same, org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            org.xar.ck3.control.g2.common.G2Source source, String session, java.time.Instant deadline, String target) {
        return archive.inSession(same, bound -> {
            var originals = new ArrayList<PlanningReadReceipt>(); var refs = new ArrayList<ExactRef>();
            var first = target == null ? definitions.formal() : definitions.state();
            var request = new PlanningReadRequest(before, source, session, first.operation(), new OpportunityJson.Obj(java.util.Map.of()), deadline);
            var value = read(same, first, request, bound, originals, refs);
            if (target != null) {
                var focus = definitions.focus(target); var next = new PlanningReadRequest(before, source, session, focus.operation(), new OpportunityJson.Obj(java.util.Map.of()), deadline);
                var focusValue = read(same, focus, next, bound, originals, refs);
                value = (OpportunityJson.Obj) OpportunityJson.parse(StrictJson.canonical(GovernancePlanningReads.combine(node(value), node(focusValue))));
            }
            return new Collected(value, List.copyOf(originals), List.copyOf(refs));
        });
    }
    private OpportunityJson.Obj read(ContinuityStorePort.Session same, ReadContract<OpportunityJson.Obj> contract, PlanningReadRequest request,
            ActionPorts.OutcomeArchive bound, List<PlanningReadReceipt> originals, List<ExactRef> refs) {
        var result = port.read(same, contract, request);
        if (!(result instanceof PlanningReadResult.Known<OpportunityJson.Obj> known)) {
            var unavailable = (PlanningReadResult.Unavailable<OpportunityJson.Obj>) result; unavailable.original().ifPresent(bound::preserve);
            throw new IllegalStateException(unavailable.reason());
        }
        requireRead(request.before(), request.source(), request.sessionId(), known.receipt(), contract, bound);
        originals.add(known.receipt()); refs.add(bound.readReferenceOf(known.receipt())); refs.add(bound.referenceOf(known.receipt().original())); return known.value();
    }
    private static void requireRead(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
            org.xar.ck3.control.g2.common.G2Source source, String session, PlanningReadReceipt read, ReadContract<?> contract, ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(read, archive);
        StrictJson.require(read.request().before().equals(before) && read.request().source().equals(source) && read.request().sessionId().equals(session)
                && read.request().arguments().members().isEmpty() && read.contractId().equals(contract.contractId()) && read.request().operation().equals(contract.operation())
                && read.before().binding().observed().equals(before) && read.after().binding().observed().equals(before)
                && read.before().paused() && read.after().paused() && read.before().mapReady() && read.after().mapReady() && read.before().playerAlive() && read.after().playerAlive()
                && read.before().originalBindingSha256().equals(read.after().originalBindingSha256()) && read.original().outbound().isPresent(), "LIFE actual read crossed its paused complete source/session/frame");
    }
    private static void requireSelected(ActionCommand command, OpportunityJson.Obj actual) {
        var args = CouncilCodec.object(StrictJson.parse(OpportunityJson.encode(command.arguments()))); ObjectNode selected = CouncilCodec.object(args.get("original_query")), current = node(actual);
        StrictJson.require(current.get("status").equals(selected.get("status")) && current.get("source_frame").equals(selected.get("source_frame"))
                && current.get("snapshot").equals(selected.get("snapshot")) && current.get("formal_precondition_status").equals(selected.get("formal_precondition_status")), "LIFE native material changed between selection and its original one-submit transaction");
        if (command.operation().value().equals(GovernanceActionPreparation.FOCUS)) StrictJson.require(current.get("focus_query").equals(selected.get("focus_query")), "selected focus differs from fresh last native final-legality query");
    }
    private static ObjectNode node(OpportunityJson.Obj value) { return CouncilCodec.object(StrictJson.parse(OpportunityJson.encode(value))); }
}
