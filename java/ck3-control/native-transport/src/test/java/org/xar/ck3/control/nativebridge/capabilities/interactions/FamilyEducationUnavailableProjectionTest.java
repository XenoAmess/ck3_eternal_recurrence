package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Synthetic failed READ DTOs only; no Installed, Native query, live guard or skills getter. */
final class FamilyEducationUnavailableProjectionTest {
    private static final ExactRef SOURCE = new ExactRef("D:/fixture/guardian-source", 1, "a".repeat(64));
    private static final ExactRef OUTCOME = new ExactRef("D:/fixture/guardian-return", 1, "b".repeat(64));
    private static final Instant NOW = Instant.parse("2026-11-18T00:00:00Z");
    private static final Instant DEADLINE = NOW.plusSeconds(10);

    @Test void florinMissingGetterRemainsTypedUnavailableWithoutCreatingALegacyContext() {
        var missing = new PlanningReadResult.Unavailable<InteractionModels.OrdinaryContext>(
                "interaction_native_contract_unmigrated:1.21.0", Optional.empty());
        var projected = missing(FamilyEducationNativeProjection.projectResult(missing));
        assertEquals(missing.reason(), projected.reason());
        assertTrue(projected.original().isEmpty());
        assertTrue(projected.decodeFailure().isEmpty());
        assertTrue(projected.observedFailure().isEmpty());
    }

    @Test void sourceOwnedDecoderCustodySurvivesTheActualGuardianProjection() {
        var ack = new NativeActionPort.AckReceived("guardian-decoder", true, Optional.of(raw("{}")),
                raw("{}"), new byte[]{1});
        OriginalReadDecodeFailure marker = (contract, request, receipt) -> {
            throw new AssertionError("an unavailable projection cannot invoke the live decoder marker");
        };
        var original = new PlanningReadResult.Unavailable<InteractionModels.OrdinaryContext>(
                "exact1210 guardian getter unavailable", Optional.of(ack), Optional.of(marker));
        var projected = missing(FamilyEducationNativeProjection.projectResult(original));
        assertEquals(original.reason(), projected.reason());
        assertSame(ack, projected.original().orElseThrow());
        assertSame(marker, projected.decodeFailure().orElseThrow());
        assertTrue(projected.observedFailure().isEmpty());
    }

    @Test void returnedUnknownKeepsItsOriginalAfterObservationAndDeadline() {
        var request = request();
        var outcome = new NativeActionPort.Unknown("guardian-unknown", "original returned unknown",
                new byte[]{1}, Optional.empty(), Optional.of(new NativeActionPort.FailureCause(
                        NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED,
                        NativeActionPort.FailureStage.RESPONSE_WAIT, Optional.empty(), Optional.empty(), Optional.empty())));
        var prepared = new NativeRequest(OrdinaryInteractionCodec.QUERY_STEP, Optional.empty(), raw("{}"));
        var guard = guard(request);
        var observed = new PlanningReadFailure(request, "guardian-software-read", outcome.requestId(),
                guard, guard, prepared, outcome, OUTCOME, SOURCE, 7, "c".repeat(64));
        var original = new PlanningReadResult.Unavailable<InteractionModels.OrdinaryContext>(
                outcome.reason(), Optional.of(outcome), Optional.empty(), Optional.of(observed));
        var projected = missing(FamilyEducationNativeProjection.projectResult(original));
        assertSame(outcome, projected.original().orElseThrow());
        assertSame(observed, projected.observedFailure().orElseThrow());
        assertEquals(DEADLINE, projected.observedFailure().orElseThrow().request().deadline());
        assertEquals("1.21.0", projected.observedFailure().orElseThrow().request().source().exactBuild());
        assertTrue(projected.decodeFailure().isEmpty());
    }

    @Test void zeroDispatchRefusalDoesNotAcquireAnAfterObservationOrKnownValue() {
        var refusal = new NativeActionPort.RejectedBeforeDispatch("guardian-before-write",
                new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,
                        0, "original admission refused", Optional.empty()));
        var original = new PlanningReadResult.Unavailable<InteractionModels.OrdinaryContext>(
                "exact1210 getter not admitted", Optional.of(refusal));
        var projected = missing(FamilyEducationNativeProjection.projectResult(original));
        assertSame(refusal, projected.original().orElseThrow());
        assertEquals(0, refusal.proof().requestBytesWritten());
        assertTrue(projected.observedFailure().isEmpty());
    }

    private static PlanningReadResult.Unavailable<Obj> missing(PlanningReadResult<Obj> result) {
        if (result instanceof PlanningReadResult.Unavailable<Obj> unavailable) return unavailable;
        throw new AssertionError("the original unavailable READ became Known");
    }
    private static RawJson raw(String json) { return new RawJson(json.getBytes(StandardCharsets.UTF_8)); }
    private static PlanningReadRequest request() {
        var source = new G2Source("guardian-software", NOW.toString(), "1.21.0", SOURCE);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),
                BigInteger.valueOf(17), BigInteger.valueOf(123456)), "guardian-snapshot", BigInteger.valueOf(19), "guardian-episode");
        var before = new ObservationIdentity(source.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        return new PlanningReadRequest(before, source, "guardian-session",
                new OperationKey(OrdinaryInteractionCodec.QUERY_STEP), new Obj(Map.of()), DEADLINE);
    }
    private static PlanningReadGuard guard(PlanningReadRequest request) {
        var binding = new GuardEvidence(request.before(), request.source(), request.sessionId(), BigInteger.ONE,
                request.operation(), SOURCE, SOURCE, "guardian-software-authority", NOW, DEADLINE);
        return new PlanningReadGuard(binding, true, true, true, "d".repeat(64));
    }
}
