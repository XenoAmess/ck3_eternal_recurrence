package org.xar.ck3.control.application.planning;

import java.time.Instant;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Exact shared Game/session/episode/actor/frame input to the ordinary planner. */
public record PlanningRequest(ObservationIdentity before, G2Source source, String sessionId,
        Instant deadline, PlanningObservation observations) {
    public PlanningRequest {
        Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId);
        Objects.requireNonNull(deadline); Objects.requireNonNull(observations);
        StrictJson.require(before.machineId().equals(source.machineId()), "planner source machine differs");
        var snapshot = observations.snapshot(); var frame = before.frame();
        StrictJson.require(frame.snapshotId().equals(PlanningObservation.text(snapshot.get("snapshot_id"), "snapshot_id"))
                && frame.episodeRunId().equals(PlanningObservation.text(snapshot.get("episode_run_id"), "episode_run_id"))
                && frame.revision().equals(PlanningObservation.integer(snapshot.get("revision"), "revision"))
                && frame.identity().nativeRevision().equals(PlanningObservation.integer(snapshot.get("native_revision"), "native_revision"))
                && frame.identity().dateRaw().equals(PlanningObservation.integer(snapshot.get("date_raw"), "date_raw"))
                && frame.identity().player().equals(PlanningObservation.integer(
                    PlanningObservation.object(snapshot.get("played_character"), "played_character").get("character_id"), "character_id")),
                "complete semantic snapshot differs from planner observation identity");
        Set<String> facts = new HashSet<>();
        observations.actionFacts().forEach(fact -> {
            StrictJson.require(facts.add(fact.actionId()), "duplicate action fact must be reduced by the sole writer");
            StrictJson.require(before.machineId().equals(fact.origin().machineId()) && before.game().equals(fact.origin().game())
                    && before.frame().episodeRunId().equals(fact.origin().frame().episodeRunId()), "action fact crossed Game or episode");
        });
        observations.campaignGoal().ifPresent(goal -> StrictJson.require(
                before.frame().identity().player().equals(java.math.BigInteger.valueOf(goal.currentCharacterId())),
                "campaign goal current actor differs from real snapshot"));
    }

    /** Original battle epoch recursion trims history, while retaining every other exact input binding. */
    public PlanningRequest withHistory(java.util.List<org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj> history) {
        return new PlanningRequest(before, source, sessionId, deadline,
                new PlanningObservation(observations.snapshot(), history, observations.actionSteps(), observations.bridgeCapabilities(),
                        observations.battleSpeedReadiness(), observations.actionFacts(), observations.campaignGoal(), observations.crossRunPlan(),
                        observations.initialLifestyleFocusRequired()));
    }
}
