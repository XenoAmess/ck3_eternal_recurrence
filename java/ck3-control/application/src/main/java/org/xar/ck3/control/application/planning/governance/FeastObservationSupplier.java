package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic.Kind;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Real query/storage boundary. Missing evidence never becomes an empty Feast ledger. */
public interface FeastObservationSupplier {
    Read<State> state(PlanningRequest request);
    Read<Planner> planner(PlanningRequest request);
    Read<Hosted> hosted(PlanningRequest request);
    Read<Obj> root(PlanningRequest request);
    Read<OrdinaryFinanceCollector.Spending> spending(PlanningRequest request);
    Read<OrdinaryFinanceCollector.Feast> feast(PlanningRequest request, OrdinaryFinanceCollector.Spending spending);
    default Read<ActivityConfigurationModels.StageOne> stageOne(PlanningRequest request) {
        return new Unavailable<>("actual native stage-one option read is not installed");
    }
    default Read<ActivityConfigurationModels.StageTwo> stageTwo(PlanningRequest request) {
        return new Unavailable<>("actual native stage-two option read is not installed");
    }
    default Read<ActivityConfigurationModels.Location> location(PlanningRequest request, int provinceId) {
        return new Unavailable<>("actual native stage-two location read is not installed");
    }

    record Terminal(BigInteger activityId, BigInteger actorId) {
        public Terminal { positiveU32(activityId); positiveU32(actorId); }
    }
    record State(ObservationIdentity observed, String sessionId, CadenceModels.State cadence,
            Optional<Obj> pending, Optional<Terminal> terminal, List<ActionReceipt> actualReceipts, Obj originalLedger) {
        public State {
            Objects.requireNonNull(observed); StrictJson.text(sessionId); Objects.requireNonNull(cadence);
            Objects.requireNonNull(pending); Objects.requireNonNull(terminal);
            actualReceipts = List.copyOf(actualReceipts); Objects.requireNonNull(originalLedger);
        }
        public void bind(PlanningRequest request) {
            StrictJson.require(observed.equals(request.before()) && sessionId.equals(request.sessionId())
                    && cadence.episodeRunId().equals(request.before().frame().episodeRunId()), "Feast durable binding drift");
        }
    }
    record Planner(Kind kind, Obj original) {
        public Planner { Objects.requireNonNull(kind); Objects.requireNonNull(original); }
        public boolean needsConfiguration() { return kind == Kind.ABSENT || kind == Kind.FEAST_STAGE_ONE || kind == Kind.FEAST_STAGE_TWO; }
    }
    record Hosted(BigInteger actorId, HostedFeastActivities activities, Obj original) {
        public Hosted { positiveU32(actorId); Objects.requireNonNull(activities); Objects.requireNonNull(original); }
        /** Current readable flags prevail, including known false/false. Stamps and counters never decide termination. */
        public boolean unresolved(Optional<Terminal> retained) {
            return activities.activities().stream().filter(row -> row.activityTypeKey().equals("activity_feast")).anyMatch(row -> {
                if (row.terminal() instanceof HostedFeastActivities.TerminalObserved flags)
                    return !(flags.completed() || flags.invalidated());
                return retained.filter(old -> old.activityId().equals(BigInteger.valueOf(row.activityId()))
                        && old.actorId().equals(actorId) && actorId.equals(BigInteger.valueOf(row.hostCharacterId()))).isEmpty();
            });
        }
    }
    private static void positiveU32(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0 && value.bitLength() <= 32, "positive full uint32 identity required");
    }
}
