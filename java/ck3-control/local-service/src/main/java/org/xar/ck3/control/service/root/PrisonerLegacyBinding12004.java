package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Joins an actual nonempty imported body to its original committed intent/attempt/Native packet. Never synthesizes an action. */
public final class PrisonerLegacyBinding12004 {
    public sealed interface Result permits Clear, Bound, Unavailable { }
    public record Clear(ExactRef originalBody) implements Result { public Clear { Objects.requireNonNull(originalBody); } }
    public record Unavailable(String reason) implements Result { public Unavailable { StrictJson.text(reason); } }
    public record Bound(PrisonerPendingIdentity12004 pending, ExactRef originalBody, ActionReceipt receipt,
            ExactRef originalIntentRecord, ExactRef originalReceipt, ExactRef originalSubmission,
            ExactRef selectedCollectionRead, List<ExactRef> lineage) implements Result {
        public Bound { Objects.requireNonNull(pending); Objects.requireNonNull(originalBody); Objects.requireNonNull(receipt);
            Objects.requireNonNull(originalIntentRecord); Objects.requireNonNull(originalReceipt); Objects.requireNonNull(originalSubmission);
            Objects.requireNonNull(selectedCollectionRead); lineage = List.copyOf(lineage); StrictJson.require(!lineage.isEmpty(), "actual canonical action lineage required"); }
    }
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final ActionSnapshotReader actions;
    private final PrisonerActionBinding12004 preparation;
    public PrisonerLegacyBinding12004(ContinuityWriter writer, NativeOutcomeArchive archive,
            ActionSnapshotReader actions, PrisonerActionBinding12004 preparation) {
        this.writer = Objects.requireNonNull(writer); this.archive = Objects.requireNonNull(archive);
        this.actions = Objects.requireNonNull(actions); this.preparation = Objects.requireNonNull(preparation);
        StrictJson.require(archive.writer() == writer, "legacy rebind must use the sole original writer/archive");
    }
    public Result read(ContinuityStorePort.Session borrowed, PlanningRequest request, PrisonerPlanningPorts.Family family) {
        try {
            writer.requireSession(borrowed);
            return archive.inSession(borrowed, sameArchive -> actions.withFrozen(borrowed, lease -> {
                try {
                    DomainBodies.Read read = borrowed.readDomain(slot(family));
                    if (!(read instanceof DomainBodies.Available original)) return new Unavailable("original prisoner body is unimported/unavailable");
                    JsonNode body = StrictJson.parse(original.canonicalBody(), 1_048_576);
                    requireBody(family, body);
                    PrisonerEpisodeLedger12004.decode(family,new RawJson(original.canonicalBody())).epoch().owner()
                            .require(request.before(),request.source(),request.sessionId());
                    JsonNode pending = body.get("pending");
                    if (pending.isNull()) return new Clear(original.reference().payload());
                    var identity = PrisonerPendingIdentity12004.decode(family, new RawJson(StrictJson.canonical(pending)));
                    List<ActionReceipt> matches = new ArrayList<>();
                    for (ActionReceipt receipt : lease.snapshot().actions()) {
                        var command = receipt.command();
                        if (command.origin() instanceof CommandOrigin.Gameplay && sameCurrent(request, command) && identity.matches(receipt)) matches.add(receipt);
                    }
                    if (matches.size() != 1) return new Unavailable(matches.isEmpty()
                            ? "no original canonical Java action matches this actual pending; UNKNOWN retained"
                            : "multiple original actions match this pending; UNKNOWN retained");
                    ActionReceipt receipt = matches.getFirst(); ActionState.Attempt attempt = ActionTransitions.attempt(receipt.state()).orElseThrow();
                    List<ExactRef> lineage = lineage(borrowed, sameArchive, receipt);
                    NativeActionPort.DispatchOutcome dispatch = ActionTransitions.dispatch(receipt.state()).orElseThrow(
                            () -> new IllegalArgumentException("original native dispatch is missing; no action identity may be reconstructed"));
                    requireZeroState(receipt,dispatch);
                    ExactRef submission = sameArchive.referenceOf(dispatch);
                    StrictJson.require(dispatch.equals(sameArchive.load(submission)), "original submission archive changed");
                    PrisonerActionBinding12004 boundPreparation = preparation.withArchive(sameArchive);
                    NativeRequest prepared = boundPreparation.prepare(receipt.command());
                    StrictJson.require(prepared.equals(attempt.preparedRequest()), "old pending original primitive differs from exact current Java request contract");
                    nativeOriginal(identity, receipt.command(), attempt, dispatch);
                    var selected = boundPreparation.selected(receipt.command());
                    if (family == PrisonerPlanningPorts.Family.RELEASE) releaseTerms(identity, selected);
                    ExactRef receiptRef = sameArchive.receiptReferenceOf(receipt);
                    StrictJson.require(receipt.equals(sameArchive.loadReceipt(receiptRef)), "original canonical receipt bytes differ");
                    lease.assertCurrent();
                    return new Bound(identity, original.reference().payload(), receipt, lineage.getFirst(), receiptRef, submission, selected.reference(), lineage);
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }));
        } catch (IllegalArgumentException | UncheckedIOException | IOException rejected) {
            String reason = rejected.getMessage() == null ? "legacy original source unavailable" : rejected.getMessage();
            return new Unavailable(reason.substring(0, Math.min(reason.length(), 1024)));
        }
    }
    private static boolean sameCurrent(PlanningRequest request, ActionCommand command) {
        return command.before().machineId().equals(request.before().machineId()) && command.before().game().equals(request.before().game())
                && command.before().frame().episodeRunId().equals(request.before().frame().episodeRunId())
                && command.before().frame().identity().player().equals(request.before().frame().identity().player())
                && command.source().equals(request.source()) && command.sessionId().equals(request.sessionId());
    }
    private static List<ExactRef> lineage(ContinuityStorePort.Session borrowed, ActionPorts.OutcomeArchive archive, ActionReceipt latest) throws IOException {
        return lineage(borrowed.head(), archive, latest);
    }
    private static List<ExactRef> lineage(WriterContracts.Head actualHead, ActionPorts.OutcomeArchive archive, ActionReceipt latest) throws IOException {
        var state = actualHead.state(); Optional<ExactRef> cursor = ContinuityActionJournal.recordHead(state);
        Set<ExactRef> seen = new java.util.HashSet<>(); List<ActionRecord> records = new ArrayList<>(); List<ExactRef> refs = new ArrayList<>();
        long maximumSequence = state.sequence();
        while (cursor.isPresent()) {
            ExactRef reference = cursor.orElseThrow(); StrictJson.require(seen.add(reference) && seen.size() <= 100000, "canonical record chain is cyclic or exceeds its bound");
            ActionRecord record = archive.loadRecord(reference); StrictJson.require(archive.recordReferenceOf(record).equals(reference)
                    && record.receipt().sequence() <= maximumSequence, "canonical original record order/identity changed");
            maximumSequence = record.receipt().sequence() - 1;
            if (record.receipt().command().actionId().equals(latest.command().actionId())) { records.add(record); refs.add(reference); }
            cursor = record.previous();
        }
        StrictJson.require(!records.isEmpty() && records.getFirst().receipt().equals(latest), "pending action is not the actual latest canonical lineage");
        Collections.reverse(records); Collections.reverse(refs); Optional<ActionReceipt> previous = Optional.empty();
        for (ActionRecord record : records) {
            ActionReceipt receipt = record.receipt();
            ActionTransitions.validate(previous, receipt.command(), receipt.bodySha256(), receipt.state()); previous = Optional.of(receipt);
        }
        StrictJson.require(records.getFirst().receipt().state() instanceof ActionState.IntentDurable, "actual pre-submission Java intent is absent");
        return List.copyOf(refs);
    }
    /** Source originals only; this does not grant an import or a new action. */
    public static List<ExactRef> originalLineage(WriterContracts.Head head,ActionPorts.OutcomeArchive archive,ActionReceipt actual)throws IOException {
        return lineage(head,archive,actual);
    }
    /** Historical domain verification uses the actual supplied canonical head, never a fabricated current gameplay frame. */
    public static void verifyOriginal(WriterContracts.Head actualHead, ActionPorts.OutcomeArchive archive,
            PrisonerActionBinding12004 preparation, PrisonerPlanningPorts.Family family, RawJson previousBody, ActionReceipt receipt) throws IOException {
        JsonNode previous = StrictJson.parse(previousBody.bytes(), 1_048_576); requireBody(family, previous);
        StrictJson.require(!previous.get("pending").isNull(), "actual previous pending is absent");
        var identity = PrisonerPendingIdentity12004.decode(family, new RawJson(StrictJson.canonical(previous.get("pending"))));
        StrictJson.require(identity.matches(receipt) && receipt.command().source().machineId().equals(actualHead.state().machineId()), "canonical pending identity differs");
        ActionReceipt canonical = ContinuityActionJournal.lookup(actualHead.state(), receipt.command().actionId(), archive)
                .orElseThrow(() -> new IOException("pending action is absent from supplied canonical head"));
        StrictJson.require(canonical.equals(receipt) && archive.receiptReferenceOf(receipt).equals(archive.receiptReferenceOf(canonical)), "pending receipt is not supplied head's exact canonical result");
        lineage(actualHead, archive, receipt);
        var attempt = ActionTransitions.attempt(receipt.state()).orElseThrow();
        var dispatch = ActionTransitions.dispatch(receipt.state()).orElseThrow();
        requireZeroState(receipt,dispatch);
        StrictJson.require(dispatch.equals(archive.load(archive.referenceOf(dispatch))), "original dispatch archive differs");
        var bound = preparation.withArchive(archive);
        StrictJson.require(bound.prepare(receipt.command()).equals(attempt.preparedRequest()), "original selected offer differs from retained attempt");
        nativeOriginal(identity, receipt.command(), attempt, dispatch);
        if (family == PrisonerPlanningPorts.Family.RELEASE) releaseTerms(identity, bound.selected(receipt.command()));
    }
    private static void nativeOriginal(PrisonerPendingIdentity12004 pending, ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch) throws IOException {
        if(dispatch instanceof NativeActionPort.RejectedBeforeDispatch zero){
            StrictJson.require(pending.actionId().filter(command.actionId()::equals).isPresent()&&pending.requestId().isEmpty(),
                    "only the original modern pre-submission pending may consume a canonical zero-write rejection");
            StrictJson.require(zero.requestId().equals(attempt.requestId())&&zero.proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                    &&zero.proof().requestBytesWritten()==0&&attempt.guard().origin().equals(command.origin())
                    &&attempt.guard().source().equals(command.source())&&attempt.guard().sessionId().equals(command.sessionId())
                    &&attempt.guard().operation().equals(command.operation()),"canonical zero-write attempt differs from original pending command");
            return;
        }
        byte[] outbound;
        if (dispatch instanceof NativeActionPort.AckReceived ack) {
            outbound = ack.outbound().orElseThrow(() -> new IllegalArgumentException("original ACK lacks actual outgoing packet")).originalPacket();
            var decoded = NativeWire.decode(ack.originalPacket()); StrictJson.require(decoded instanceof NativeWire.CommandResult, "actual original native response is not a command result");
            var response = (NativeWire.CommandResult) decoded;
            StrictJson.require(response.requestId().equals(attempt.requestId()) && response.nativeOk() == ack.nativeOk()
                    && java.util.Arrays.equals(response.payload().value(), ack.originalFrame().bytes()), "native original ACK envelope differs from canonical retained return");
            StrictJson.require(response.result().token().map(NativeWire.Bytes::value).map(RawJson::new).equals(ack.originalResultToken()), "native raw result token differs from original ACK packet");
            if (pending.requestId().isPresent()) {
                StrictJson.require(ack.nativeOk(), "legacy pending-only ACK is not a successful native pending ACK");
                var token = StrictJson.object(StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()), Set.of("step", "accepted", "status"));
                StrictJson.require(StrictJson.text(token.get("step")).equals(command.operation().value())
                        && StrictJson.text(token.get("status")).equals("submitted_verification_pending"), "legacy pending ACK changed actual operation/status");
                StrictJson.trueValue(token.get("accepted"));
            }
        } else if (dispatch instanceof NativeActionPort.Unknown unknown) outbound = unknown.originalRequestPacket();
        else throw new IllegalArgumentException("zero-dispatch rejection cannot bind a legacy submitted pending");
        NativeWire.ExecuteRequest original = NativeWire.decodeExecuteRequest(outbound);
        StrictJson.require(original.requestId().equals(attempt.requestId()) && original.step().equals(command.operation().value())
                && original.expectedRevision().equals(Optional.of(command.before().frame().identity().nativeRevision()))
                && original.expectedSnapshotRevision().isEmpty()
                && StrictJson.parse(original.normalizedAdditionalFields().value()).equals(StrictJson.parse(attempt.preparedRequest().additionalFields().bytes())),
                "actual outgoing packet differs from original durable prisoner attempt");
        StrictJson.require(attempt.guard().origin().equals(command.origin()) && attempt.guard().source().equals(command.source())
                && attempt.guard().sessionId().equals(command.sessionId()) && attempt.guard().operation().equals(command.operation()), "old pending original guard source/session differs");
    }
    private static void requireZeroState(ActionReceipt receipt,NativeActionPort.DispatchOutcome dispatch){
        if(dispatch instanceof NativeActionPort.RejectedBeforeDispatch)StrictJson.require(receipt.state() instanceof ActionState.RejectedBeforeDispatch zero
                &&zero.dispatch().equals(dispatch),"only the actual canonical zero-dispatch state may settle an unsubmitted pending");
    }
    private static void releaseTerms(PrisonerPendingIdentity12004 pending, PrisonerActionBinding12004.SelectedRead selected) {
        var expected = pending.release().orElseThrow();
        StrictJson.require(selected.intent().options().equals(expected.options()), "persisted release authored options changed");
        JsonNode row = StrictJson.parse(selected.normalized().bytes(), 1_048_576).path("player_prisoner_collection").path("prisoners").get(selected.ordinal());
        JsonNode preview = row.get(expected.mask() == 0 ? "unconditional_release_preview" : "negotiated_release_preview");
        StrictJson.require(StrictJson.parse(expected.costs().bytes()).equals(preview.get("costs"))
                && StrictJson.parse(expected.acceptance().bytes()).equals(preview.get("acceptance")), "persisted release cost/acceptance differs from actual selected source");
    }
    public static void requireBody(PrisonerPlanningPorts.Family family, JsonNode body) {
        PrisonerLedgerReducer12004.validate(family, body);
    }
    public static DomainBodies.Slot slot(PrisonerPlanningPorts.Family family) { return family == PrisonerPlanningPorts.Family.RELEASE ? DomainBodies.Slot.PRISONER_RELEASE : DomainBodies.Slot.PRISONER_RANSOM; }
}
