package org.xar.ck3.control.application.action;

import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual failed READ data. It grants no Known value, business effect, replay or submit permission.
 * Live custody is authenticated by FailedReadAttempt; cold consumers verify the original archive closure. */
public record PlanningReadFailure(PlanningReadRequest request, String contractId, String requestId,
        PlanningReadGuard before, PlanningReadGuard after, NativeRequest prepared,
        NativeActionPort.DispatchOutcome original, ExactRef originalRef, ExactRef preparedRef,
        long headSequence, String headDigest) {
    public PlanningReadFailure {
        Objects.requireNonNull(request); StrictJson.text(contractId); StrictJson.text(requestId);
        Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(prepared);
        Objects.requireNonNull(original); Objects.requireNonNull(originalRef); Objects.requireNonNull(preparedRef);
        StrictJson.require(headSequence >= 0 && headDigest != null && headDigest.matches("[0-9a-f]{64}"),
                "actual failed-read writer head required");
        StrictJson.require(originalRef.bytes() > 0 && preparedRef.bytes() > 0,
                "actual failed-read outcome and preparation archives required");
        StrictJson.require(original.requestId().equals(requestId) && returnedRead(original),
                "failed-read observation requires the identical returned READ, never a pre-write rejection");
        NativeStepDiscriminator.requireRequest(request.operation(), ExecutableStepBindings.Kind.READ, prepared);
        StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay
                && before.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && after.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && before.paused() && before.mapReady() && before.playerAlive()
                && after.paused() && after.mapReady() && after.playerAlive(),
                "failed-read observation requires the actual living paused gameplay frame");
        StrictJson.require(request.origin().equals(before.binding().origin())
                && before.binding().origin().equals(after.binding().origin())
                && before.originalBindingSha256().equals(after.originalBindingSha256()),
                "failed READ changed its exact Game/player/date/revisions or modal binding");
        StrictJson.require(request.source().equals(before.binding().source())
                && request.source().equals(after.binding().source())
                && request.sessionId().equals(before.binding().sessionId())
                && request.sessionId().equals(after.binding().sessionId())
                && request.operation().equals(before.binding().operation())
                && request.operation().equals(after.binding().operation())
                && before.binding().connectionGeneration().equals(after.binding().connectionGeneration())
                && before.binding().authorityId().equals(after.binding().authorityId()),
                "failed READ crossed its actual source/session/connection/authority");
    }
    /** A retained request packet alone cannot prove that its write returned. */
    public static boolean returnedRead(NativeActionPort.DispatchOutcome original) {
        Objects.requireNonNull(original);
        if (original instanceof NativeActionPort.AckReceived ack)
            return ack.outbound().isPresent() && ack.custody().isPresent();
        return original instanceof NativeActionPort.Unknown unknown
                && unknown.originalRequestPacket().length > 0
                && unknown.failureCause().filter(cause -> cause.stage() == NativeActionPort.FailureStage.RESPONSE_WAIT
                        && cause.kind() != NativeActionPort.FailureKind.INTERRUPTED).isPresent();
    }
}
