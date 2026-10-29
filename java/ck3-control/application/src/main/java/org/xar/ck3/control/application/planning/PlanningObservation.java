package org.xar.ck3.control.application.planning;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * One frozen semantic observation. Raw JSON is retained only at this dynamic
 * boundary; domain policies must use their existing typed decoders. It is not
 * a native qualification and cannot be constructed from G2 metadata alone.
 */
public record PlanningObservation(OpportunityJson.Obj snapshot, List<OpportunityJson.Obj> history,
        Set<OperationKey> actionSteps, Set<String> bridgeCapabilities, Optional<OpportunityJson.Obj> battleSpeedReadiness, List<ExternalFact> actionFacts,
        Optional<Goal> campaignGoal, Optional<OpportunityJson.Obj> crossRunPlan, boolean initialLifestyleFocusRequired) {
    public PlanningObservation {
        Objects.requireNonNull(snapshot); history = List.copyOf(history); actionSteps = Set.copyOf(actionSteps);
        bridgeCapabilities = Set.copyOf(bridgeCapabilities); actionFacts = List.copyOf(actionFacts);
        Objects.requireNonNull(campaignGoal); Objects.requireNonNull(crossRunPlan); Objects.requireNonNull(battleSpeedReadiness);
        bridgeCapabilities.forEach(StrictJson::text);
        // Existing immutable JSON domain rejects duplicate fields, booleans and floats as integers.
        DriverJson.object(DriverJson.encode(snapshot), DriverJson.MAX_NATIVE_BYTES);
        bool(snapshot.get("paused"), "paused"); bool(snapshot.get("map_ready"), "map_ready");
        for (String key : List.of("revision", "native_revision"))
            StrictJson.require(integer(snapshot.get(key), key).signum() > 0, "positive " + key + " required");
        StrictJson.require(integer(snapshot.get("date_raw"), "date_raw").signum() >= 0, "nonnegative game date required");
        text(snapshot.get("snapshot_id"), "snapshot_id"); text(snapshot.get("episode_run_id"), "episode_run_id");
        OpportunityJson.Obj actor = object(snapshot.get("played_character"), "played_character");
        NativeCharacterId.of(integer(actor.get("character_id"), "character_id"));
        OpportunityJson.array(snapshot.get("active_wars"), "active_wars");
        OpportunityJson.array(snapshot.get("player_armies"), "player_armies");
    }
    public boolean paused() { return bool(snapshot.get("paused"), "paused"); }
    public boolean mapReady() { return bool(snapshot.get("map_ready"), "map_ready"); }
    public boolean warInProgress() { return !OpportunityJson.array(snapshot.get("active_wars"), "active_wars").isEmpty(); }
    public boolean foregroundPresent() {
        return present(snapshot.get("active_event")) || present(snapshot.get("pending_character_interaction"))
                || snapshot.get("top_exclusive_modal_choice_hint") instanceof OpportunityJson.Obj hint
                    && new OpportunityJson.Text("present").equals(hint.get("status"));
    }
    private static boolean present(OpportunityJson.Value value) { return value != null && value != OpportunityJson.Nil.INSTANCE; }
    static boolean bool(OpportunityJson.Value value, String field) { return OpportunityJson.bool(value, field); }
    static BigInteger integer(OpportunityJson.Value value, String field) { return OpportunityJson.integer(value, field); }
    static String text(OpportunityJson.Value value, String field) { return OpportunityJson.text(value, field); }
    static OpportunityJson.Obj object(OpportunityJson.Value value, String field) { return OpportunityJson.object(value, field); }
}
