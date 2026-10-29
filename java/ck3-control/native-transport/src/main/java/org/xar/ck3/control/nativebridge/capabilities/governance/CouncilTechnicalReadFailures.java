package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.governance.CouncilSelection;
import org.xar.ck3.control.application.planning.governance.CouncilTechnicalReadFailure;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure Council failure adaptation. Shared real after guards and archived originals remain the evidence. */
public final class CouncilTechnicalReadFailures {
    public static final String SCHEMA = "xar.java.council-technical-read-chain/v1";
    private CouncilTechnicalReadFailures() { }

    /** Invoked while the original private read's borrowed writer Session and mailbox scope are held. */
    static Optional<CouncilTechnicalReadFailure> observe(PlanningReadResult.Unavailable<CouncilPrivateCodec.Reply> unavailable,
            PlanningReadRequest failedRequest, PlanningReadRequest initial, CouncilSelection.Position role,
            List<PlanningReadReceipt> prior, NativeCouncilReadPort.ReplayConfiguration configuration,
            ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(unavailable);
        if (unavailable.observedFailure().isEmpty()) return Optional.empty();
        PlanningReadFailure failure = unavailable.observedFailure().orElseThrow();
        try {
            StrictJson.require(failure.request().equals(failedRequest)
                    && unavailable.original().filter(failure.original()::equals).isPresent(),
                    "Council failure differs from its actual failed private READ");
            validate(failure, initial, role, prior, configuration, archive);
            ExactRef failed = PlanningReadFailureCodec.preserve(failure, archive);
            StrictJson.require(PlanningReadFailureCodec.load(failed, archive).equals(failure), "shared failed READ archive changed");
            var body = StrictJson.object().put("schema", SCHEMA).put("initial_operation", initial.operation().value())
                    .put("position_key", role.key());
            body.set("failed_read", failed.toJson());
            var refs = body.putArray("prior_reads");
            for (PlanningReadReceipt read : prior) refs.add(archive.readReferenceOf(read).toJson());
            RawJson raw = new RawJson(StrictJson.canonical(body));
            ExactRef diagnostic = archive.preserveMaterial(raw);
            StrictJson.require(raw.equals(archive.loadMaterial(diagnostic)), "Council failure chain archive changed");
            return Optional.of(replay(diagnostic, configuration, archive));
        } catch (RuntimeException unsupported) {
            // Incomplete or changed evidence remains ordinary Unavailable; never Known or a business action result.
            return Optional.empty();
        }
    }

    /** Replays preserved originals without a native query, mailbox, writer acquisition or submission. */
    public static CouncilTechnicalReadFailure replay(ExactRef diagnostic,
            NativeCouncilReadPort.ReplayConfiguration configuration, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(configuration); Objects.requireNonNull(archive);
        var body = index(diagnostic, archive);
        var role = java.util.Arrays.stream(CouncilSelection.Position.values())
                .filter(value -> value.key().equals(CouncilCodec.text(body, "position_key"))).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("unsupported original Council position"));
        ExactRef failed = ExactRef.fromJson(body.get("failed_read"));
        PlanningReadFailure failure = PlanningReadFailureCodec.load(failed, archive);
        JsonNode prior = body.get("prior_reads");
        StrictJson.require(prior != null && prior.isArray() && prior.size() <= configuration.maximumStatusPolls() + 1,
                "complete bounded original Council failure chain required");
        var reads = new ArrayList<PlanningReadReceipt>();
        for (JsonNode item : prior) {
            ExactRef ref = ExactRef.fromJson(item); PlanningReadReceipt read = archive.loadRead(ref);
            StrictJson.require(archive.readReferenceOf(read).equals(ref), "Council prior READ reference changed");
            reads.add(read);
        }
        PlanningReadRequest initial = reads.isEmpty() ? failure.request() : reads.getFirst().request();
        StrictJson.require(initial.operation().value().equals(CouncilCodec.text(body, "initial_operation")),
                "Council initial operation changed in retained diagnostic");
        validate(failure, initial, role, reads, configuration, archive);
        // The diagnostic indexes every prior original, avoiding truncation at the policy's top-level evidence cap.
        var originals = new LinkedHashSet<ExactRef>();
        originals.add(diagnostic); originals.add(failed); originals.add(failure.originalRef()); originals.add(failure.preparedRef());
        return new CouncilTechnicalReadFailure(initial, failure, List.copyOf(reads), List.copyOf(originals), diagnostic);
    }

    /** The transport receives the shared original failure evidence, never this domain's outer index. */
    public static ExactRef failedReadReference(ExactRef diagnostic, ActionPorts.OutcomeArchive archive) {
        return ExactRef.fromJson(index(diagnostic, archive).get("failed_read"));
    }
    /** One pure technical domain for live transport exit and cold Council replay; never grants mailbox authority. */
    public static void requireTechnicalReadFailure(PlanningReadFailure failure) {
        Objects.requireNonNull(failure);
        String step = failure.request().operation().value();
        StrictJson.require((step.equals(CouncilPrivateCodec.QUERY) || step.equals(CouncilPrivateCodec.GATES)
                || step.equals(CouncilPrivateCodec.STATUS)) && failure.prepared().step().equals(step)
                && failure.original().requestId().equals(failure.requestId())
                && PlanningReadFailure.returnedRead(failure.original()),
                "Council technical failure requires its actual returned read-only QUERY/GATES/STATUS");
        if (failure.original() instanceof NativeActionPort.AckReceived ack) {
            JsonNode frame = StrictJson.parse(ack.originalFrame().bytes());
            requireUnavailableCommandResult(frame, failure.requestId());
            if (ack.nativeOk()) {
                JsonNode token = StrictJson.parse(ack.originalResultToken()
                        .orElseThrow(() -> new IllegalArgumentException("successful Council ACK has no original malformed token")).bytes());
                StrictJson.require(!token.isObject() && frame instanceof ObjectNode body
                        && body.get("result") != null && body.get("result").equals(token),
                        "successful Council ACK is technical only for its original non-object result");
            }
        } else if (failure.original() instanceof NativeActionPort.Unknown unknown) {
            if (unknown.rawReturn().isPresent())
                requireUnavailableCommandResult(StrictJson.parse(unknown.rawReturn().orElseThrow().bytes()), failure.requestId());
        } else throw new IllegalArgumentException("Council technical failure was not actually sent");
    }
    private static ObjectNode index(ExactRef diagnostic, ActionPorts.OutcomeArchive archive) {
        RawJson raw = archive.loadMaterial(diagnostic);
        StrictJson.require(diagnostic.bytes() == raw.bytes().length && diagnostic.sha256().equals(ActionCodec.sha256(raw.bytes())),
                "Council failure diagnostic bytes/SHA changed");
        var body = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("schema", "initial_operation", "position_key", "failed_read", "prior_reads"));
        StrictJson.require(SCHEMA.equals(CouncilCodec.text(body, "schema")), "Council failure diagnostic schema differs");
        return body;
    }

    private static void validate(PlanningReadFailure failure, PlanningReadRequest initial, CouncilSelection.Position role,
            List<PlanningReadReceipt> prior, NativeCouncilReadPort.ReplayConfiguration configuration,
            ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(failure); Objects.requireNonNull(initial); Objects.requireNonNull(role);
        Objects.requireNonNull(configuration); prior = List.copyOf(prior);
        StrictJson.require(prior.size() <= configuration.maximumStatusPolls() + 1, "bounded complete Council failure chain required");
        String initialStep = initial.operation().value();
        StrictJson.require(initialStep.equals(CouncilPrivateCodec.QUERY) || initialStep.equals(CouncilPrivateCodec.GATES),
                "only optional Council QUERY/GATES can be technically deferred");
        StrictJson.require(initial.arguments().equals(new Obj(Map.of()).with("position_key", new Text(role.key()))),
                "Council technical read queried a different position or injected fields");
        var definitions = configuration.definitions();
        ReadContract<CouncilPrivateCodec.Reply> first = initialStep.equals(CouncilPrivateCodec.GATES) ? definitions.gates() : definitions.query();
        var ids = new java.util.HashSet<String>();
        for (int index = 0; index < prior.size(); index++) {
            PlanningReadReceipt read = prior.get(index);
            ReadContract<CouncilPrivateCodec.Reply> contract = index == 0 ? first : definitions.status();
            requireRequest(read.request(), initial, index == 0 ? initial.operation() : definitions.status().operation(), index == 0 ? initial.arguments() : new Obj(Map.of()));
            StrictJson.require(read.contractId().equals(contract.contractId()) && ids.add(read.requestId()),
                    "Council prior contract changed or repeated an original request ID");
            NativeRecordedEvidenceVerifier.requireRead(read, archive);
            GovernanceNativeReads.verifyGuards(read);
            StrictJson.require(!(contract.decode(read) instanceof CouncilPrivateCodec.Terminal),
                    "Council technical chain continued after a terminal result");
        }
        if (!prior.isEmpty()) GovernanceReadChronology.requireOrderedReads(prior);
        ReadContract<CouncilPrivateCodec.Reply> last = prior.isEmpty() ? first : definitions.status();
        requireRequest(failure.request(), initial, last.operation(), prior.isEmpty() ? initial.arguments() : new Obj(Map.of()));
        StrictJson.require(failure.contractId().equals(last.contractId()) && ids.add(failure.requestId())
                && failure.prepared().equals(last.prepare(failure.request(), failure.requestId())),
                "Council failed read changed its actual contract/request/prepared primitive");
        StrictJson.require(failure.original().equals(archive.load(failure.originalRef()))
                && failure.prepared().equals(archive.loadRequest(failure.preparedRef()))
                && failure.originalRef().equals(archive.referenceOf(failure.original()))
                && failure.preparedRef().equals(archive.requestReferenceOf(failure.prepared())),
                "Council failed READ original/prepared archive changed");
        requireFrame(failure.before(), initial); requireFrame(failure.after(), initial);
        StrictJson.require(failure.before().binding().origin().equals(failure.after().binding().origin())
                && failure.before().binding().connectionGeneration().equals(failure.after().binding().connectionGeneration())
                && failure.before().originalBindingSha256().equals(failure.after().originalBindingSha256()),
                "Council failed READ drifted from its actual original living paused frame");
        requireTechnicalReadFailure(failure);
        NativeActionPort.DispatchOutcome original = failure.original(); byte[] packet;
        if (original instanceof NativeActionPort.AckReceived ack) {
            var outbound = ack.outbound().orElseThrow(() -> new IllegalArgumentException("Council failed READ outbound packet missing"));
            StrictJson.require(outbound.requestId().equals(failure.requestId()), "Council failure outbound ID changed");
            packet = outbound.originalPacket();
            var custody = GovernanceReadChronology.requireAck(ack, failure.before().binding());
            if (!prior.isEmpty()) GovernanceReadChronology.requireAfter(
                    GovernanceReadChronology.requireAck(prior.getLast().original(), prior.getLast().before().binding()), custody);
        } else if (original instanceof NativeActionPort.Unknown unknown) {
            var cause = unknown.failureCause().orElseThrow(() -> new IllegalArgumentException("Council failed READ lacks actual send-returned evidence"));
            StrictJson.require(cause.stage() == NativeActionPort.FailureStage.RESPONSE_WAIT
                    && cause.kind() != NativeActionPort.FailureKind.INTERRUPTED,
                    "Council technical deferral requires a returned send and excludes interruption");
            packet = unknown.originalRequestPacket();
        } else throw new IllegalArgumentException("Council request was not actually sent; no technical deferral");
        StrictJson.require(original.requestId().equals(failure.requestId()) && packet.length > 0,
                "Council failed READ lost its actual sent packet identity");
        PrivateCouncilReads.requireOriginalWire(failure.request(), failure.requestId(), packet, last.operation().value());
    }

    private static void requireRequest(PlanningReadRequest actual, PlanningReadRequest initial, OperationKey operation, OpportunityJson.Obj arguments) {
        StrictJson.require(actual.before().equals(initial.before()) && actual.source().equals(initial.source())
                && actual.sessionId().equals(initial.sessionId()) && actual.deadline().equals(initial.deadline())
                && actual.operation().equals(operation) && actual.arguments().equals(arguments),
                "Council read-only chain crossed original frame/source/session/operation/fields");
    }
    private static void requireFrame(PlanningReadGuard actual, PlanningReadRequest initial) {
        StrictJson.require(actual.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && actual.binding().observed().equals(initial.before()) && actual.binding().source().equals(initial.source())
                && actual.binding().sessionId().equals(initial.sessionId()) && actual.paused() && actual.mapReady() && actual.playerAlive(),
                "Council technical failure has no actual same-frame living paused after guard");
    }
    private static void requireUnavailableCommandResult(JsonNode frame, String requestId) {
        if (!(frame instanceof ObjectNode value)) return;
        JsonNode error = value.get("error");
        StrictJson.require(error == null || !error.isTextual()
                || !error.textValue().equals("nonwar private snapshot revision is stale or malformed"),
                "Council stale rejection needs source refresh, not technical deferral");
        JsonNode protocol = value.get("protocol_version"), ok = value.get("ok");
        boolean successful = value.path("type").isTextual() && value.path("type").textValue().equals("command_result")
                && protocol != null && protocol.isIntegralNumber() && protocol.bigIntegerValue().equals(java.math.BigInteger.ONE)
                && value.path("request_id").isTextual() && value.path("request_id").textValue().equals(requestId)
                && ok != null && ok.isBoolean() && ok.booleanValue() && value.get("result") instanceof ObjectNode;
        StrictJson.require(!successful, "completed command_result or later normalization error is not Council technical unavailability");
    }
}
