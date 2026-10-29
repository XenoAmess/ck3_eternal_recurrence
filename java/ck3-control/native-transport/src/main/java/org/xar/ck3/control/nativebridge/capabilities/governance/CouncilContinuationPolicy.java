package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** Source-specific Council continuation legality. Every STATUS remains a separately durable native request. */
public final class CouncilContinuationPolicy implements CouncilContinuationPorts.Policy {
    public static final String PREFLIGHT_SCHEMA = "xar.java.council-original-preflight/v1";
    private final PrivateCouncilReads definitions;
    private final NativeEffectEvidence.FrameLoader frames;
    private final String version;
    private final String sha256;
    public CouncilContinuationPolicy(PrivateCouncilReads definitions, NativeEffectEvidence.FrameLoader frames, String version, String sha256) {
        this.definitions = Objects.requireNonNull(definitions); this.frames = Objects.requireNonNull(frames);
        CouncilCodec.requireBuild(version, sha256); this.version = version; this.sha256 = sha256;
    }
    @Override public List<ExactRef> prepareEvidence(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent,
            Stage stage, List<Retained> prior, ActionPorts.OutcomeArchive archive) {
        var context = GovernanceActionScope.current(parent.command());
        StrictJson.require(context.session(parent.command()) == same, "continuation borrowed another original writer"); context.mailbox(parent.command());
        if (!prior.isEmpty()) return prior.getFirst().request().supportingEvidence();
        var reads = context.preflight(parent.command());
        StrictJson.require(!reads.isEmpty() && reads.size() <= 3002, "actual held-scope final-gates preflight is required");
        var body = StrictJson.object().put("schema", PREFLIGHT_SCHEMA).put("command_body_sha256", parent.bodySha256())
                .put("original_request_id", ActionTransitions.attempt(parent.state()).orElseThrow().requestId());
        var refs = body.putArray("reads");
        for (var read : reads) { NativeRecordedEvidenceVerifier.requireRead(read, archive); refs.add(archive.readReferenceOf(read).toJson()); }
        RawJson material = new RawJson(StrictJson.canonical(body)); ExactRef ref = archive.preserveMaterial(material);
        StrictJson.require(material.equals(archive.loadMaterial(ref)), "actual Council preflight archive changed");
        requirePreflight(parent.command(), ActionTransitions.attempt(parent.state()).orElseThrow(), List.of(ref), archive, parent.ack().orElseThrow());
        return List.of(ref);
    }
    @Override public void verifyIssue(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent,
            List<Retained> prior, Request next, ActionPorts.OutcomeArchive archive) throws IOException {
        var context = GovernanceActionScope.current(parent.command());
        StrictJson.require(context.session(parent.command()) == same, "continuation lost original Session"); context.mailbox(parent.command());
        var attempt = ActionTransitions.attempt(parent.state()).orElseThrow();
        requirePreflight(parent.command(), attempt, next.supportingEvidence(), archive, parent.ack().orElseThrow());
        Progress progress = replay(parent.command(), attempt, parent.ack().orElseThrow(), prior, archive);
        StrictJson.require(progress.next().filter(next.stage()::equals).isPresent(), "Council continuation stage is not the next original native operation");
        StrictJson.require(prior.stream().allMatch(row -> row.request().supportingEvidence().equals(next.supportingEvidence())), "continuation changed its original preflight basis");
        var actual = RootGuardEvidence.loadFrame(next.guard(), archive, frames);
        StrictJson.require(actual.source().equals(parent.command().source()) && actual.sessionId().equals(parent.command().sessionId())
                && actual.identity().game().equals(parent.command().before().game())
                && actual.identity().frame().episodeRunId().equals(parent.command().before().frame().episodeRunId())
                && actual.identity().frame().identity().player().equals(parent.command().before().frame().identity().player()), "continuation source frame changed Game/player/episode");
        if (next.stage() == Stage.RECEIPT_QUERY) StrictJson.require(actual.identity().frame().identity().nativeRevision()
                .compareTo(parent.command().before().frame().identity().nativeRevision()) > 0, "Council receipt must follow a genuinely newer published native frame");
        NativeRequest prepared = archive.loadRequest(next.preparedRequest());
        StrictJson.require(prepared.step().equals(next.stage().step()) && prepared.requiredCapability().isEmpty()
                && prepared.additionalFields().objectFieldNames().isEmpty(), "Council continuation cannot add wire arguments or another step");
    }
    @Override public void verifyOutcome(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt parent,
            List<Retained> prior, Entry next, NativeActionPort.DispatchOutcome original, ActionPorts.OutcomeArchive archive) throws IOException {
        StrictJson.require(original.requestId().equals(next.request().requestId()) && original.equals(archive.load(next.outcome().orElseThrow())), "continuation outcome lost original custody");
        // Invalid/false native results must still become durable terminal facts. They never admit a following request.
        if (original instanceof NativeActionPort.AckReceived ack && ack.outbound().isPresent()) requireWire(next.request(), ack);
    }
    public void requirePreflight(ActionCommand command, ActionState.Attempt attempt, List<ExactRef> refs, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(refs.size() == 1, "one complete original Council preflight leaf required");
        RawJson raw = exact(refs.getFirst(), archive);
        var row = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("schema", "command_body_sha256", "original_request_id", "reads"));
        StrictJson.require(PREFLIGHT_SCHEMA.equals(StrictJson.text(row.get("schema"))) && ActionCodec.bodySha256(command).equals(StrictJson.text(row.get("command_body_sha256")))
                && attempt.requestId().equals(StrictJson.text(row.get("original_request_id"))), "Council preflight crossed original action/attempt");
        var items = row.get("reads"); StrictJson.require(items.isArray() && !items.isEmpty() && items.size() <= 3002, "bounded complete Council preflight requests required");
        var expected = GovernanceActionPreparation.councilRequest(command, attempt.requestId());
        var ids = new HashSet<String>(); var originals = new ArrayList<PlanningReadReceipt>();
        CouncilPrivateCodec.Terminal terminal = null; PlanningReadReceipt last = null;
        for (int i = 0; i < items.size(); i++) {
            ExactRef ref = ExactRef.fromJson(items.get(i)); PlanningReadReceipt read = archive.loadRead(ref);
            StrictJson.require(archive.readReferenceOf(read).equals(ref), "preflight read reference changed"); NativeRecordedEvidenceVerifier.requireRead(read, archive);
            originals.add(read);
            StrictJson.require(ids.add(read.requestId()) && !read.requestId().equals(attempt.requestId()) && read.request().before().equals(command.before())
                    && read.request().source().equals(command.source()) && read.request().sessionId().equals(command.sessionId())
                    && read.before().binding().observed().equals(command.before()) && read.after().binding().observed().equals(command.before())
                    && read.before().originalBindingSha256().equals(read.after().originalBindingSha256())
                    && !read.original().outbound().isEmpty(), "Council preflight is not its original same-frame native read");
            ReadContract<CouncilPrivateCodec.Reply> contract = i == 0 ? definitions.gates() : definitions.status();
            StrictJson.require(read.contractId().equals(contract.contractId()) && read.request().operation().equals(contract.operation()), "Council preflight contract/stage changed");
            if (i == 0) StrictJson.require(read.request().arguments().equals(new OpportunityJson.Obj(Map.of()).with("position_key", new OpportunityJson.Text(expected.position().key()))), "Council preflight queried another cached position");
            else StrictJson.require(read.request().arguments().members().isEmpty(), "Council preflight STATUS cannot take arguments");
            var reply = contract.decode(read);
            StrictJson.require(terminal == null, "Council preflight queried after already consuming its terminal result");
            if (reply instanceof CouncilPrivateCodec.Terminal found) terminal = found;
            last = read;
        }
        StrictJson.require(terminal != null && last != null, "Council preflight has no actually consumed terminal gates");
        GovernanceReadChronology.requireOrderedReads(originals);
        var query = new PlanningReadRequest(command.before(), command.source(), command.sessionId(), definitions.gates().operation(),
                new OpportunityJson.Obj(Map.of()).with("position_key", new OpportunityJson.Text(expected.position().key())), command.deadline());
        var normalized = CouncilCodec.object(StrictJson.parse(CouncilPrivateCodec.normalize(terminal, CouncilPrivateCodec.GATES,
                PrivateCouncilReads.nativeFrame(query), GovernanceNativeReads.frame(query), expected.position(), version, sha256).bytes()));
        var original = CouncilCodec.object(StrictJson.parse(OpportunityJson.encode(command.arguments())).get("original_query"));
        StrictJson.require(normalized.hasNonNull("council_composition_candidates") && normalized.hasNonNull("council_final_gates")
                && normalized.get("council_composition_candidates").equals(original.get("council_composition_candidates"))
                && normalized.get("council_final_gates").equals(original.get("council_final_gates")), "Council preflight does not reproduce original selected final legality");
    }
    public void requirePreflight(ActionCommand command, ActionState.Attempt attempt, List<ExactRef> refs,
            ActionPorts.OutcomeArchive archive, NativeActionPort.AckReceived originalSubmission) {
        requirePreflight(command, attempt, refs, archive);
        var row = StrictJson.parse(exact(refs.getFirst(), archive).bytes());
        for (var item : row.get("reads")) NativeRequestChronology.requireBeforeSubmission(archive.loadRead(ExactRef.fromJson(item)), attempt, originalSubmission);
    }
    public record Progress(Optional<Stage> next, Optional<CouncilActionCodec.Ack> helper, Optional<CouncilActionCodec.Receipt> receipt) {
        public Progress { Objects.requireNonNull(next); Objects.requireNonNull(helper); Objects.requireNonNull(receipt); }
    }
    public static Progress replay(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived original,
            List<Retained> rows, ActionPorts.OutcomeArchive archive) throws IOException {
        requireOriginalPending(command, attempt, original);
        var previousCustody = GovernanceReadChronology.requireAck(original, attempt.guard());
        StrictJson.require(!previousCustody.writeEntered().observedAt().isBefore(attempt.submittedAt()), "Council original native write predates the canonical attempt");
        Optional<Stage> next = Optional.of(Stage.HELPER_STATUS); CouncilActionCodec.Ack helper = null; CouncilActionCodec.Receipt receipt = null;
        var ids = new HashSet<String>(); ids.add(attempt.requestId()); long sequence = 0; java.math.BigInteger nativeSequence = java.math.BigInteger.ZERO;
        for (Retained retained : rows) {
            StrictJson.require(retained.entry().equals(CouncilContinuationCodec.decodeEntry(exact(retained.reference(), archive).bytes())), "continuation entry differs from its original archive");
            Request request = retained.request();
            StrictJson.require(retained.status() == Status.ACK && next.filter(request.stage()::equals).isPresent()
                    && request.scope().parentActionId().equals(command.actionId()) && request.scope().parentBodySha256().equals(ActionCodec.bodySha256(command))
                    && request.scope().originalAttemptRequestId().equals(attempt.requestId()) && ids.add(request.requestId()) && request.issuedSequence() > sequence,
                    "Council continuation replay crossed original scope/order or unresolved request"); sequence = request.issuedSequence();
            var outcome = archive.load(retained.entry().outcome().orElseThrow());
            StrictJson.require(outcome instanceof NativeActionPort.AckReceived, "continuation does not have an original ACK");
            var ack = (NativeActionPort.AckReceived) outcome; requireWire(request, ack); var material = result(ack);
            var actualCustody = GovernanceReadChronology.requireAck(ack, request.guard());
            GovernanceReadChronology.requireAfter(previousCustody, actualCustody);
            StrictJson.require(!actualCustody.writeEntered().observedAt().isBefore(request.issuedAt())
                    && !actualCustody.responseReceived().observedAt().isAfter(request.deadline()), "Council continuation escaped its original issued time/deadline");
            previousCustody = actualCustody;
            if (isPending(material, request.stage().step())) {
                if (request.stage() == Stage.RECEIPT_QUERY) next = Optional.of(Stage.RECEIPT_STATUS);
                continue;
            }
            var actualSequence = CouncilCodec.u64(material.get("query_sequence"), true);
            StrictJson.require(actualSequence.compareTo(nativeSequence) > 0, "Council original native terminal sequence did not advance"); nativeSequence = actualSequence;
            if (request.stage() == Stage.HELPER_STATUS) {
                helper = decodeHelperTerminal(new RawJson(StrictJson.canonical(material)), GovernanceActionPreparation.councilRequest(command, attempt.requestId()));
                next = helper.status() == CouncilActionCodec.AckStatus.HELPER_INVOKED_VERIFICATION_PENDING ? Optional.of(Stage.RECEIPT_QUERY) : Optional.empty();
            } else {
                StrictJson.require(helper != null, "receipt query precedes original helper terminal");
                envelope(material, CouncilActionCodec.RECEIPT, "council_assign_councillor_receipt");
                receipt = CouncilActionCodec.decodeReceipt(StrictJson.canonical(material.get("council_assign_councillor_receipt")), helper);
                StrictJson.require(CouncilCodec.text(material, "status").equals(CouncilCodec.text(CouncilCodec.object(StrictJson.parse(receipt.original().bytes())), "status"))
                        && CouncilCodec.u64(material.get("snapshot_revision"), true).equals(request.guard().observed().frame().identity().nativeRevision()), "receipt terminal crossed its actual query native frame");
                next = Optional.empty();
            }
        }
        return new Progress(next, Optional.ofNullable(helper), Optional.ofNullable(receipt));
    }
    /** Original semantic terminal -> shared exact helper DTO. A native rejected helper has an all-zero pre-frame. */
    public static CouncilActionCodec.Ack decodeHelperTerminal(RawJson original, CouncilActionCodec.Request expected) {
        var material = CouncilCodec.object(StrictJson.parse(original.bytes()));
        envelope(material, CouncilActionCodec.ASSIGN, "council_assign_councillor_ack");
        var helper = CouncilActionCodec.decodeAck(StrictJson.canonical(material.get("council_assign_councillor_ack")), expected);
        var originalHelper = CouncilCodec.object(StrictJson.parse(helper.original().bytes()));
        StrictJson.require(CouncilCodec.text(material, "status").equals(CouncilCodec.text(originalHelper, "status"))
                && CouncilCodec.u64(material.get("snapshot_revision"), false).equals(helper.status() == CouncilActionCodec.AckStatus.HELPER_INVOKED_VERIFICATION_PENDING
                        ? expected.frame().nativeRevision() : java.math.BigInteger.ZERO), "helper terminal envelope/native frame differs");
        return helper;
    }
    public static void requireOriginalPending(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived original) throws IOException {
        StrictJson.require(command.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN) && original.requestId().equals(attempt.requestId())
                && original.outbound().isPresent() && attempt.preparedRequest().step().equals(command.operation().value()), "original private Council attempt/ACK required");
        var wire = NativeWire.decodeExecuteRequest(original.outbound().orElseThrow().originalPacket());
        var expected = GovernanceActionPreparation.councilRequest(command, attempt.requestId());
        StrictJson.require(wire.requestId().equals(attempt.requestId()) && wire.step().equals(command.operation().value())
                && wire.expectedRevision().filter(command.before().frame().identity().nativeRevision()::equals).isPresent() && wire.expectedSnapshotRevision().isEmpty()
                && StrictJson.parse(wire.normalizedAdditionalFields().value()).equals(StrictJson.parse(attempt.preparedRequest().additionalFields().bytes()))
                && StrictJson.parse(wire.normalizedAdditionalFields().value()).equals(CouncilActionCodec.wireFields(expected, true)), "original Council outbound differs from durable selected candidate primitive");
        StrictJson.require(isPending(result(original), CouncilActionCodec.PRIVATE_ASSIGN), "original private Council result is not its genuine pending transport ACK");
    }
    public static void requireWire(Request request, NativeActionPort.AckReceived original) throws IOException {
        StrictJson.require(original.requestId().equals(request.requestId()) && original.outbound().isPresent(), "continuation actual outbound/correlation required");
        var wire = NativeWire.decodeExecuteRequest(original.outbound().orElseThrow().originalPacket());
        StrictJson.require(wire.requestId().equals(request.requestId()) && wire.step().equals(request.stage().step()) && wire.expectedSnapshotRevision().isEmpty()
                && StrictJson.parse(wire.normalizedAdditionalFields().value()).isEmpty(), "continuation outbound wire differs from its fixed original producer");
        StrictJson.require(request.stage() == Stage.RECEIPT_QUERY
                ? wire.expectedRevision().filter(request.guard().observed().frame().identity().nativeRevision()::equals).isPresent()
                : wire.expectedRevision().isEmpty(), "continuation revision profile changed");
    }
    public static ObjectNode result(NativeActionPort.AckReceived original) throws IOException {
        StrictJson.require(original.nativeOk() && original.originalResultToken().isPresent(), "native continuation was rejected/unavailable; no new request");
        var decoded = NativeWire.decode(original.originalPacket());
        StrictJson.require(decoded instanceof NativeWire.CommandResult, "original ACK packet is not command_result"); var frame = (NativeWire.CommandResult) decoded;
        StrictJson.require(frame.nativeOk() && frame.requestId().equals(original.requestId()) && java.util.Arrays.equals(frame.payload().value(), original.originalFrame().bytes())
                && frame.result().token().isPresent() && java.util.Arrays.equals(frame.result().token().orElseThrow().value(), original.originalResultToken().orElseThrow().bytes()), "continuation full packet/result token differs");
        return CouncilCodec.object(StrictJson.parse(original.originalResultToken().orElseThrow().bytes()));
    }
    public static boolean isPending(ObjectNode value, String step) {
        if (!value.has("private_council_transport")) return false;
        StrictJson.object(value, Set.of("private_council_transport", "advertised", "step", "status")); StrictJson.trueValue(value.get("private_council_transport"));
        StrictJson.require(!CouncilCodec.bool(value.get("advertised")) && CouncilCodec.text(value, "step").equals(step)
                && CouncilCodec.text(value, "status").equals("pending"), "Council mailbox pending envelope drift/idle"); return true;
    }
    private static void envelope(ObjectNode value, String step, String payload) {
        StrictJson.object(value, Set.of("schema", "step", "accepted", "status", "query_sequence", "snapshot_revision", payload, "backend_id"));
        StrictJson.require(CouncilCodec.text(value, "schema").equals("xar.ck3.council-application-main/v1") && CouncilCodec.text(value, "step").equals(step)
                && CouncilCodec.text(value, "backend_id").equals("native-headless"), "Council terminal semantic source/step drift");
        StrictJson.trueValue(value.get("accepted")); CouncilCodec.u64(value.get("query_sequence"), true); CouncilCodec.u64(value.get("snapshot_revision"), false);
    }
    private static RawJson exact(ExactRef ref, ActionPorts.OutcomeArchive archive) {
        RawJson raw = archive.loadMaterial(ref); StrictJson.require(ref.bytes() == raw.bytes().length && ref.sha256().equals(ActionCodec.sha256(raw.bytes())), "Council original leaf bytes/SHA differ"); return raw;
    }
}
