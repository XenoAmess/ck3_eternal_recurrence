package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Original narrow readonly state_changed response; actual negative packet DATA, never Known or action credit. */
public final class ArmyWindowQueryDeferred {
    public static final String SCHEMA = "xar.war-results-readonly-state-changed/v1";
    private ArmyWindowQueryDeferred() { }
    public static final class Deferred {
        private final RawJson normalized; private final NativeActionPort.AckReceived original;
        private final ArmyCalls.Frame input; private final ArmyTypes.Context context;
        private Deferred(ObjectNode normalized, NativeActionPort.AckReceived original,ArmyCalls.Frame input,ArmyTypes.Context context) {
            this.normalized = new RawJson(bytes(normalized)); this.original = original; this.input=input; this.context=context;
        }
        public RawJson normalized() { return normalized; }
        public NativeActionPort.AckReceived original() { return original; }
        public ArmyCalls.Frame input() { return input; }
        public ArmyTypes.Context context() { return context; }
    }
    public static Optional<Deferred> from(ArmyCalls.Frame input, Complete actualBefore, PlanningReadRequest actualRequest,
            PlanningReadResult.Unavailable<ArmyWindowCodec.Observation> unavailable) throws java.io.IOException {
        Objects.requireNonNull(actualBefore); Objects.requireNonNull(unavailable);
        if (ArmyWindowReads.kind(input.method()) != ArmyWindowCodec.Kind.RESULTS
                || !(unavailable.original().orElse(null) instanceof NativeActionPort.AckReceived ack) || ack.nativeOk()) return Optional.empty();
        String reason;
        try { reason = ArmyWindowQueryFailure.refusalMessage(ArmyWindowCodec.Kind.RESULTS, ack.originalFrame(), ack.requestId()); }
        catch (IllegalArgumentException malformed) { return Optional.empty(); }
        if (!"Native war results refused: state_changed".equals(reason)) return Optional.empty();
        var diagnostics = OpportunityJson.object(actualBefore.semantic().get("diagnostics"), "actual Driver diagnostics");
        var helloValue = diagnostics.get("hello");
        if (!(helloValue instanceof OpportunityJson.Obj hello)
                || !(diagnostics.get("bridge_pid") instanceof OpportunityJson.IntegerValue bridge)
                || !(hello.get("pid") instanceof OpportunityJson.IntegerValue helloPid)
                || bridge.value().signum() <= 0 || !bridge.value().equals(helloPid.value())) return Optional.empty();
        Objects.requireNonNull(actualRequest);
        require(actualRequest.before().equals(actualBefore.identity()) && actualRequest.source().equals(actualBefore.source())
                && actualRequest.sessionId().equals(actualBefore.sessionId()) && actualRequest.arguments().equals(ArmyWindowReads.arguments(input))
                && actualRequest.operation().value().equals(ArmyWindowCodec.Kind.RESULTS.step(ArmyWindowCodec.Operation.QUERY)), "deferred query crossed its exact actual read request/source");
        var context = new ArmyTypes.Context(actualBefore.identity(), actualBefore.source(), actualBefore.sessionId(), actualRequest.deadline());
        input.revision().requireCurrent(context.before().frame().revision());
        var custody = ack.custody().orElseThrow(() -> ArmyWindowQueryFailure.from(ArmyWindowCodec.Kind.RESULTS, unavailable));
        custody.verify(ack);
        require(custody.session().machineId().equals(actualBefore.source().machineId())
                && custody.session().game().equals(actualBefore.identity().game())
                && custody.session().sessionId().equals(actualBefore.sessionId())
                && custody.session().connectionGeneration().equals(actualBefore.connectionGeneration()), "deferred query crossed its actual held source/Game/session/Native connection");
        byte[] outbound = ack.outbound().orElseThrow().originalPacket();
        var request = NativeWire.decodeExecuteRequest(outbound); var response = NativeWire.decode(ack.originalPacket());
        require(request.requestId().equals(ack.requestId()) && request.step().equals(ArmyWindowCodec.Kind.RESULTS.step(ArmyWindowCodec.Operation.QUERY))
                && response instanceof NativeWire.CommandResult result && result.requestId().equals(ack.requestId()), "deferred query changed its actual original request/response");
        ObjectNode rawRequest = closed(parse(Arrays.copyOfRange(outbound,4,outbound.length)), "type","protocol_version","request_id","step","expected_revision");
        equal(rawRequest.get("type"), "execute_step"); require(i32(rawRequest.get("protocol_version")) == 1, "deferred request protocol differs");
        equal(rawRequest.get("request_id"),ack.requestId()); equal(rawRequest.get("step"),request.step()); equal(rawRequest.get("expected_revision"),context.nativeRevision());
        ObjectNode top = parse(ack.originalFrame().bytes());
        var packetTop = parse(((NativeWire.CommandResult) response).payload().value());
        require(top.equals(packetTop), "deferred negative parsed TOP differs from actual retained packet");
        BigInteger driver = ArmyWindowCodec.driverGeneration(actualBefore); ObjectNode value = empty();
        value.put("schema",SCHEMA).put("step",request.step()).put("status","technical_read_deferred").put("accepted",false).put("available",false)
                .put("read_only",true).put("business_submission",false).put("native_ack_verified",false).put("request_retried",false)
                .put("ui_action_credit",false).put("date_advance_observed",false).put("window_presence","unknown").put("close_dispatched",false)
                .put("native_request_id",ack.requestId());
        ObjectNode nativeEvidence = value.putObject("native_error_evidence"); nativeEvidence.set("native_request",rawRequest); nativeEvidence.set("native_command_result",top);
        ObjectNode attempt = value.putObject("failed_attempt");
        attempt.put("validation_schema","war-results-window-query-attempt-v1").put("step",request.step()).put("native_request_id",ack.requestId())
                .put("status","failed").put("error",reason); lease(attempt,context,driver);
        ObjectNode frame = value.putObject("source_frame");
        frame.put("snapshot_id",context.before().frame().snapshotId()).put("revision",context.before().frame().revision())
                .put("native_revision",context.nativeRevision()).put("date_raw",context.dateRaw()).put("actor_character_id",context.playerId())
                .put("connection_generation",driver).put("bridge_pid",bridge.value());
        if (context.before().frame().episodeRunId() == null) frame.putNull("episode_run_id"); else frame.put("episode_run_id",context.before().frame().episodeRunId());
        lease(value,context,driver); return Optional.of(new Deferred(value,ack,input,context));
    }
    private static void lease(ObjectNode value,ArmyTypes.Context context,BigInteger driver) {
        value.put("queried_snapshot_id",context.before().frame().snapshotId()).put("queried_revision",context.before().frame().revision())
                .put("queried_native_revision",context.nativeRevision()).put("queried_date_raw",context.dateRaw())
                .put("queried_actor_character_id",context.playerId()).put("queried_connection_generation",driver);
        if (context.before().frame().episodeRunId() == null) value.putNull("queried_episode_run_id"); else value.put("queried_episode_run_id",context.before().frame().episodeRunId());
    }
}
