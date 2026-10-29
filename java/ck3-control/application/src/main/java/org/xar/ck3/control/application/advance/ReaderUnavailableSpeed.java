package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.military.BattleReaderWatch;

/** Changes only the rate of a previously selected hands-off exact day; it grants no battle/retreat prediction. */
public final class ReaderUnavailableSpeed {
    public static final String POLICY = "exact_one_day_reader_unavailable_native_speed_5";
    private ReaderUnavailableSpeed() { }
    public static boolean ready(Obj frame, List<Obj> completeHistory, boolean exactOneDay, String resultStep,
            Optional<String> proofKind, Set<String> capabilities, Set<OperationKey> steps, boolean assaultInProgress) {
        if (!exactOneDay || !resultStep.equals("life-advance-one-day") || proofKind.isPresent() || assaultInProgress
                || !ClockStatusRead.available(capabilities)
                || !steps.containsAll(Set.of(new OperationKey("life-advance-one-day"),new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map")))
                || !AdvancePolicy.truth(frame,"paused") || !AdvancePolicy.truth(frame,"map_ready") || !AdvancePolicy.falsehood(frame,"one_life_terminal")
                || frame.get("active_event") != Nil.INSTANCE || frame.get("pending_character_interaction") != Nil.INSTANCE || !AdvancePolicy.truth(frame,"war_objective_assault_supported")) return false;
        if (!(frame.get("top_exclusive_modal_choice_hint") instanceof Obj hint) || !new Text("absent").equals(hint.get("status")) || !AdvancePolicy.truth(hint,"owner_verified")
                || !(frame.get("played_character") instanceof Obj played) || !AdvancePolicy.truth(played,"alive") || !(played.get("character_id") instanceof IntegerValue)
                || !(frame.get("player_armies") instanceof Arr armies) || armies.items().isEmpty()) return false;
        try {
            BigInteger province = null;
            for (Value value : armies.items()) {
                Obj army = object(value,"army"); BigInteger current = integer(army.get("current_province_id"),"current_province_id");
                if (!AdvancePolicy.truth(army,"controllable") || !java.util.Objects.equals(army.get("owner_character_id"),played.get("character_id"))
                        || !AdvancePolicy.truth(army,"in_combat") || !AdvancePolicy.falsehood(army,"retreating") || current.signum() <= 0
                        || army.get("move_target_province_id") != Nil.INSTANCE || !(army.get("route_province_ids") instanceof Arr route) || !route.items().isEmpty()
                        || !new Text("combat").equals(army.get("army_state")) || province != null && !province.equals(current)) return false;
                province = current;
            }
            // The shared watch validates the exact failed native request/response, complete
            // scope and continuous one-day lineage. No second receipt parser lives here.
            List<Obj> bounded = completeHistory.subList(Math.max(0,completeHistory.size()-256),completeHistory.size());
            Optional<Obj> selected = BattleReaderWatch.select(frame,bounded);
            return selected.filter(watch -> new Text("reader_unavailable_hands_off").equals(watch.get("status"))
                    && java.util.Objects.equals(watch.get("observed_date_raw"),frame.get("date_raw"))
                    && AdvancePolicy.falsehood(watch,"prediction_ready") && AdvancePolicy.falsehood(watch,"retreat_authorized")).isPresent();
        } catch (IllegalArgumentException | ArithmeticException malformed) { return false; }
    }
}
