package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Fixed terminal ordinal-zero reader. The new living player is the native actor; the old episode subject is only retained target. */
public final class PrisonerTerminalQueries {
    public static final String CONTRACT_ID = "family/prisoner-collection12004/lifecycle-terminal/0";
    private static final OperationKey OPERATION = new OperationKey(PrisonerNativeQueries.STEP);
    private PrisonerTerminalQueries() { }
    @FunctionalInterface public interface Admission {
        void verify(PlanningReadRequest request, LifecycleIdentity actual, PrisonerOptionIntent.Arguments arguments);
    }
    public static ReadContract<RawJson> contract(ExactRef definitionSource, Admission admission) {
        Objects.requireNonNull(definitionSource); Objects.requireNonNull(admission);
        return new ReadContract<>(CONTRACT_ID, OPERATION, Optional.empty(), PrisonerNativeQueries.PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, definitionSource,
                request -> {
                    LifecycleIdentity actual = actual(request); PrisonerOptionIntent.Arguments arguments = arguments(request);
                    admission.verify(request, actual, arguments);
                    ObjectNode fields = StrictJson.object().put("release_material_target_character_id", arguments.materialTarget().orElseThrow());
                    return new NativeRequest(PrisonerNativeQueries.STEP, Optional.empty(), new RawJson(StrictJson.canonical(fields)));
                }, receipt -> decode(receipt).normalized());
    }
    public static OpportunityJson.Obj arguments(LifecycleIdentity actual) {
        requireActual(actual); long oldSubject = actual.subject().characterId().longValueExact();
        return PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(), OptionalLong.of(oldSubject));
    }
    public static PrisonerOptionIntent.Arguments arguments(PlanningReadRequest request) {
        LifecycleIdentity actual = actual(request);
        PrisonerOptionIntent.Arguments arguments = PrisonerOptionIntent.decode(OpportunityJson.toNode(request.arguments()));
        StrictJson.require(arguments.options() instanceof PrisonerOptionIntent.Unconditional
                && arguments.materialTarget().isPresent() && arguments.materialTarget().getAsLong() == actual.subject().characterId().longValueExact(),
                "terminal prisoner read requires unconditional ordinal-zero observation of the original episode subject only");
        return arguments;
    }
    public static LifecycleIdentity actual(PlanningReadRequest request) {
        Objects.requireNonNull(request); StrictJson.require(request.operation().equals(OPERATION), "terminal prisoner read cannot change native operation");
        LifecycleIdentity actual = request.origin().requireLifecycleTerminal(); requireActual(actual);
        StrictJson.require(actual.machineId().equals(request.source().machineId()) && actual.sessionId().equals(request.sessionId())
                && request.source().exactBuild().equals(FamilyObligations.Build.CURRENT4.exactBuild()), "current terminal prisoner source/session/machine drift");
        return actual;
    }
    public static PrisonerNativeQueries.Decoded decode(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt); PlanningReadRequest request = receipt.request(); LifecycleIdentity actual = actual(request);
        PrisonerOptionIntent.Arguments arguments = arguments(request);
        StrictJson.require(receipt.contractId().equals(CONTRACT_ID) && receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "actual successful terminal prisoner query/token required");
        for (var guard : List.of(receipt.before(), receipt.after())) {
            StrictJson.require(guard.guardMode() == ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION
                    && actual.sameGuardFrame(guard.binding().origin().requireLifecycleTerminal())
                    && guard.binding().source().equals(request.source()) && guard.binding().sessionId().equals(request.sessionId())
                    && guard.binding().operation().equals(OPERATION) && guard.binding().connectionGeneration().equals(actual.connectionGeneration()),
                    "terminal prisoner read crossed actual original lifecycle frame/source/connection");
        }
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                && receipt.before().binding().authorityId().equals(receipt.after().binding().authorityId()), "terminal prisoner query lost the original held authority/binding");
        LifecycleIdentity.Frame frame = actual.frame(); LifecycleIdentity.Character successor = (LifecycleIdentity.Character) actual.currentPlayer();
        PrisonerNativeQueries.Decoded result = PrisonerNativeQueries.decodeNative(receipt.original().originalResultToken().orElseThrow(), 0,
                arguments, frame.snapshotId(), frame.revision(), frame.nativeRevision(), frame.dateRaw().intValueExact(), successor.characterId().longValueExact());
        StrictJson.require(result.retainedCustody().isPresent(), "terminal predecessor read requires an actual retained-target state group; missing is not death");
        return result;
    }
    private static void requireActual(LifecycleIdentity actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(actual.terminalReason() == LifecycleIdentity.TerminalReason.CHANGED
                && actual.currentPlayer() instanceof LifecycleIdentity.Character successor && successor.alive()
                && !successor.characterId().equals(actual.subject().characterId())
                && actual.frame().paused() && actual.frame().mapReady(), "terminal prisoner read requires the actual different living successor on the paused map");
        long current = ((LifecycleIdentity.Character) actual.currentPlayer()).characterId().longValueExact(), old = actual.subject().characterId().longValueExact();
        StrictJson.require(current > 0 && current < 0xffff_ffffL && old > 0 && old < 0xffff_ffffL && actual.frame().dateRaw().signum() > 0
                && actual.frame().dateRaw().compareTo(java.math.BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "actual prisoner parser identity/date ranges required");
    }
}
