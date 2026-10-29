package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** An exact registered read on the original PlanningReadPort; it cannot submit a world action. */
public final class ClockStatusRead {
    public static final String ARM_PREFIX = "research-arm-tactical-daily-sentinel-v1-";
    public static final String CANCEL_PREFIX = "research-cancel-tactical-daily-sentinel-v1-generation-";
    public static final String STEP = "research-query-tactical-daily-sentinel-v1";
    public static final String ARM_CAP = "game.command.research-arm-tactical-daily-sentinel-v1-N";
    public static final String STATUS_CAP = "game.command.research-query-tactical-daily-sentinel-v1";
    public static final String CANCEL_CAP = "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N";
    public static final String CONTRACT_ID = "java.tactical-daily-sentinel.status.v1";
    private final PlanningReadPort reads;
    private final ReadContract<Status> contract;
    private final ActionPorts.OutcomeArchive archive;
    // Factory ownership preserves the exact installed object; Root still grants all actual source/session/custody authority.
    private static final Set<ReadContract<Status>> REGISTERED = java.util.Collections.newSetFromMap(new java.util.WeakHashMap<>());
    public static ReadContract<Status> registeredContract(ExactRef actualNativeDefinition) {
        Objects.requireNonNull(actualNativeDefinition); require(actualNativeDefinition.bytes() > 0, "original native Status definition required");
        ReadContract<Status> actual = new ReadContract<>(CONTRACT_ID, new OperationKey(STEP), Optional.of(STATUS_CAP),
                "tactical-daily-sentinel-status-v1", ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, actualNativeDefinition,
                (request, requestId) -> {
                    require(request.arguments().members().isEmpty(), "original native Status query has no extra arguments");
                    return new NativeRequest(STEP, STATUS_CAP, new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                },
                receipt -> decode(receipt.original()), receipt -> decode(receipt.original()));
        synchronized (REGISTERED) { REGISTERED.add(actual); } return actual;
    }
    public ClockStatusRead(PlanningReadPort reads, ExactRef actualNativeDefinition, ActionPorts.OutcomeArchive archive) {
        this(reads, registeredContract(actualNativeDefinition), archive);
    }
    public ClockStatusRead(PlanningReadPort reads, ReadContract<Status> exactInstalled, ActionPorts.OutcomeArchive archive) {
        this.reads = Objects.requireNonNull(reads); this.archive = Objects.requireNonNull(archive);
        this.contract = Objects.requireNonNull(exactInstalled);
        requireRegisteredContract(exactInstalled);
    }
    /** Source-factory identity and metadata only; this neither installs a Root contract nor grants observation permission. */
    public static void requireRegisteredContract(ReadContract<Status> exactInstalled) {
        Objects.requireNonNull(exactInstalled);
        synchronized (REGISTERED) { require(REGISTERED.contains(exactInstalled), "Status consumer requires the exact source-factory installed contract object"); }
        require(exactInstalled.contractId().equals(CONTRACT_ID) && exactInstalled.operation().equals(new OperationKey(STEP))
                && exactInstalled.requiredCapability().equals(Optional.of(STATUS_CAP))
                && exactInstalled.permissionKey().equals("tactical-daily-sentinel-status-v1")
                && exactInstalled.permissionMode() == ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                && exactInstalled.wireProfile() == ReadContract.WireProfile.EXECUTE_STEP
                && exactInstalled.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && exactInstalled.sourceRef().bytes() > 0 && exactInstalled.hasPureReplay(), "installed Status contract metadata/source/replay differs");
    }
    public ReadContract<Status> contract() { return contract; }
    public ActionPorts.OutcomeArchive archive() { return archive; }
    public ExactRef preserve(NativeActionPort.DispatchOutcome original) { return archive.preserve(original); }
    public record Observation(Status status, PlanningReadReceipt receipt, ExactRef originalEvidence) {
        public Observation {
            Objects.requireNonNull(status); Objects.requireNonNull(receipt); Objects.requireNonNull(originalEvidence);
            require(originalEvidence.bytes() > 0 && receipt.contractId().equals(CONTRACT_ID)
                    && receipt.request().operation().equals(new OperationKey(STEP))
                    && receipt.request().arguments().members().isEmpty()
                    && receipt.request().origin() instanceof CommandOrigin.Gameplay
                    && receipt.before().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    && receipt.after().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    && receipt.before().paused() && receipt.before().mapReady() && receipt.before().playerAlive()
                    && receipt.after().paused() && receipt.after().mapReady() && receipt.after().playerAlive()
                    && status.equals(decode(receipt.original())),
                    "independent original paused clock Status contract/value/evidence required");
        }
    }
    public Observation observe(ActionCommand parent, AdvanceObservationPort.Frame current, Instant deadline) {
        require(current.source().equals(parent.source()) && current.sessionId().equals(parent.sessionId())
                && current.identity().game().equals(parent.before().game()), "clock read crossed held Game/source/session");
        var request = new PlanningReadRequest(current.identity(), parent.source(), parent.sessionId(), new OperationKey(STEP),
                new OpportunityJson.Obj(Map.of()), deadline);
        PlanningReadResult<Status> result = reads.read(contract, request);
        if (result instanceof PlanningReadResult.Known<Status> known) {
            require(known.receipt().request().equals(request) && known.receipt().contractId().equals(contract.contractId()),
                    "Status read returned another original request or installed contract");
            return new Observation(known.value(), known.receipt(), archive.preserve(known.receipt().original()));
        }
        throw new IllegalStateException("native clock status unavailable: " + ((PlanningReadResult.Unavailable<Status>) result).reason());
    }
    public static Status decode(NativeActionPort.AckReceived ack) {
        require(ack.nativeOk() && ack.originalResultToken().isPresent(), "native clock query did not return a successful original token");
        JsonNode token = StrictJson.parse(ack.originalResultToken().orElseThrow().bytes());
        require(token.isObject() && token.path("step").isTextual() && STEP.equals(token.path("step").textValue())
                && token.path("accepted").isBoolean() && token.path("accepted").booleanValue()
                && token.path("status").isTextual() && token.path("status").textValue().equals("available"), "native clock status result contract differs");
        return SentinelObservation.decode(token.get("tactical_daily_sentinel"));
    }
    public static boolean available(Set<String> capabilities) { return capabilities.containsAll(Set.of(ARM_CAP, STATUS_CAP, CANCEL_CAP)); }
}
