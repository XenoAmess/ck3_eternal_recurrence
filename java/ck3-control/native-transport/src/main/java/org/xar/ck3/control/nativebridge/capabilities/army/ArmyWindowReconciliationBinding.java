package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.Objects;
import java.math.BigInteger;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.ReconciliationIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Pure binding of the two retained fixed-window UNKNOWN originals to their independent readonly query.
 * The installed Root authority separately verifies canonical membership, the unchanged original Driver,
 * complete source/native qualification, actual catalog object identity and the physical query response.
 * Construction and verification grant neither a query permit nor permission to repeat the original close.
 */
public final class ArmyWindowReconciliationBinding {
    private ArmyWindowReconciliationBinding() { }

    public static void verify(ActionReceipt actualPending, ActionState.Attempt actualAttempt,
            ReconciliationIdentity actualIdentity, ReadContract<?> actualReconContract, PlanningReadRequest actualQuery, BigInteger actualDriverConnectionGeneration) {
        Objects.requireNonNull(actualPending); Objects.requireNonNull(actualAttempt); Objects.requireNonNull(actualIdentity);
        Objects.requireNonNull(actualReconContract); Objects.requireNonNull(actualQuery);
        Objects.requireNonNull(actualDriverConnectionGeneration);
        StrictJson.require(actualDriverConnectionGeneration.signum()>=0 && actualDriverConnectionGeneration.compareTo(StrictJson.UINT64_MAX)<=0,
                "actual semantic Driver connection generation must be uint64, including zero");
        StrictJson.require(actualPending.state() instanceof ActionState.Unknown unknown
                && unknown.attempt().filter(actualAttempt::equals).isPresent(),
                "Window2 reconciliation requires the exact retained UNKNOWN primitive Attempt");
        StrictJson.require(!actualPending.settled() && actualPending.command().origin() instanceof CommandOrigin.Gameplay
                && actualPending.bodySha256().equals(ActionCodec.bodySha256(actualPending.command())),
                "Window2 pending must retain its complete original gameplay action body");
        var rebound = ReconciliationIdentity.fromCanonical(actualPending, actualIdentity.factual(), actualIdentity.source(),
                actualIdentity.sessionId(), actualIdentity.connectionGeneration(), actualIdentity.pending().originalReceipt(),
                actualIdentity.pending().originalBeforeDriver(), actualIdentity.evidence(), actualIdentity.observedAt());
        StrictJson.require(rebound.equals(actualIdentity), "Window2 factual query changed the original canonical action/Attempt binding");

        var command = actualPending.command();
        var arguments = ArmyOrdinaryActionArguments.decode(command.arguments());
        ArmyWindowCodec.Kind window = switch (command.operation().value()) {
            case "close-war-declared-overview-v1" -> {
                StrictJson.require(arguments.kind() == ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1,
                        "overview original has a different typed public action kind");
                yield ArmyWindowCodec.Kind.OVERVIEW;
            }
            case "close-war-results-window-v1" -> {
                StrictJson.require(arguments.kind() == ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_RESULTS_WINDOW_V1,
                        "results original has a different typed public action kind");
                yield ArmyWindowCodec.Kind.RESULTS;
            }
            default -> throw new IllegalArgumentException("only the two exact fixed-window close originals have Window2 scope");
        };
        switch(arguments.executionProfile()) {
            case SDK_ORDINARY -> StrictJson.require(arguments.preflightReads().size()==1,
                    "ordinary Window2 close retains exactly one original window preflight receipt");
            case DIRECT_FIXED_WINDOW -> StrictJson.require(arguments.preflightReads().isEmpty(),
                    "explicit direct fixed-window close has no invented preflight receipt");
            default -> throw new IllegalArgumentException("another execution profile cannot borrow fixed-window query scope");
        }
        // The sole public codec retains its admitted safe-integer/decimal-text domain and rejects bool,
        // fractional, missing, null, unsafe numeric and extra-selector inputs. Do not invent a second ABI.
        var originalCall = (ArmyCalls.Frame) ArmyCallCodec.decode(PublicMethod.valueOf(arguments.kind().name()), arguments.publicArguments());
        originalCall.revision().requireCurrent(command.before().frame().revision());

        StrictJson.require(actualQuery.origin() instanceof CommandOrigin.Reconciliation
                && actualQuery.origin().requireReconciliation().sameGuardFrame(actualIdentity)
                && actualQuery.source().equals(actualIdentity.source())
                && actualQuery.sessionId().equals(actualIdentity.sessionId()),
                "Window2 query cannot borrow gameplay, another original pending or another source/session");
        PublicMethod queryMethod = window == ArmyWindowCodec.Kind.OVERVIEW
                ? PublicMethod.QUERY_WAR_DECLARED_OVERVIEW_V1 : PublicMethod.QUERY_WAR_RESULTS_WINDOW_V1;
        var queryCall = (ArmyCalls.Frame) ArmyCallCodec.decode(queryMethod,
                new RawJson(OpportunityJson.encode(actualQuery.arguments())));
        queryCall.revision().requireCurrent(actualIdentity.factual().frame().revision());
        StrictJson.require(actualQuery.operation().value().equals(window.step(ArmyWindowCodec.Operation.QUERY))
                && actualQuery.arguments().equals(ArmyWindowReads.arguments(queryCall)),
                "Window2 query changed the actual producer's canonical original window selection");
        var selection = new ArmyWindowReads.ReconciliationSelection(actualIdentity, queryCall, actualQuery.deadline(), actualDriverConnectionGeneration);
        ArmyWindowReads.requireReconciliationContract(actualReconContract, selection);

        NativeRequest prepared = actualAttempt.preparedRequest();
        StrictJson.require(prepared.step().equals(command.operation().value())
                && prepared.requiredCapability().filter(window.capability(ArmyWindowCodec.Operation.CLOSE)::equals).isPresent(),
                "Window2 original prepared request changed its native close operation/capability");
        StrictJson.object(StrictJson.parse(prepared.additionalFields().bytes()), Set.of());
        // The original Attempt's native revision and the public revisions above are separate identities.
        // Neither is rewritten to make an old action acceptable on a later frame.
    }
}

