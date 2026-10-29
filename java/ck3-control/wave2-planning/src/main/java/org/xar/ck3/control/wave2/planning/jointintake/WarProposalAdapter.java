package org.xar.ck3.control.wave2.planning.jointintake;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.wave2.planning.jointintake.IntakeWire.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.warcash.WarcashCodec;
import org.xar.ck3.control.wave2.finance.warcash.WarcashModel;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/** Adapts the existing primary-defender continuation without widening its single-war policy. */
final class WarProposalAdapter {
    private WarProposalAdapter() { }
    static WarcashModel.Frame cashFrame(Frame frame) {
        return new WarcashModel.Frame(frame.playedCharacterId(), frame.nativeRevision(), frame.dateRaw(), frame.snapshotId(), frame.revision(), frame.episodeRunId());
    }
    static Obj adapt(Frame frame, Obj snapshot, Obj source) {
        Obj plan = object(source.get("plan"), "war plan"), observation = object(source.get("observation"), "war observation");
        equalsValue(plan.get("policy"), new Text("one-life-turn-v1"), "war policy");
        BigInteger warId = positive(plan.get("war_id"), "war id"); text(plan.get("selected_step"), "war step");
        equalsValue(observation.get("status"), new Text("available"), "war observation status"); equalsValue(observation.get("read_only"), new Bool(true), "war read only");
        sourceFrame(observation.get("source_frame"), frame, "played_character_id"); equalsValue(observation.get("war_id"), number(warId), "observation war");
        for (Value rows : List.of(presentOrNull(snapshot, "active_wars"), presentOrNull(plan, "active_wars"))) {
            List<Value> wars = array(rows, "active wars"); require(wars.size() == 1, "single primary-defender continuation required");
            Obj war = object(wars.getFirst(), "active war"); equalsValue(war.get("war_id"), number(warId), "active war id");
            equalsValue(war.get("player_side"), new Text("defender"), "primary defender side"); equalsValue(war.get("player_is_primary_war_leader"), new Bool(true), "primary defender leader");
        }
        List<BigInteger> armies = ids(observation.get("army_ids"), "army_ids", true), allies = ids(observation.get("ally_character_ids"), "ally_character_ids", false), characters = ids(observation.get("character_ids"), "character_ids", false);
        require(!armies.isEmpty(), "observed war army required"); Set<BigInteger> controllable = new HashSet<>();
        for (Value value : array(snapshot.get("player_armies"), "public armies")) if (value instanceof Obj army && new Bool(true).equals(army.get("controllable"))) controllable.add(integer(army.get("army_id"), "army id"));
        List<Value> bindings = array(observation.get("army_war_bindings"), "army war bindings"); require(bindings.size() == armies.size(), "binding count"); Set<BigInteger> bound = new HashSet<>();
        for (Value value : bindings) {
            Obj binding = object(value, "army war binding"); equalsValue(binding.get("war_id"), number(warId), "army binding war");
            BigInteger army = nonnegative(binding.get("army_id"), "bound army"); require(armies.contains(army), "army binding scope"); bound.add(army);
        }
        require(controllable.containsAll(armies) && bound.containsAll(armies), "war armies not controllable and bound");
        Obj rawCash = object(observation.get("war_cash_resource"), "war cash receipt");
        WarcashModel.SingleReceipt cash = WarcashCodec.verifyCompleteSingle(OpportunityJson.toNode(rawCash), cashFrame(frame), warId);
        Obj treasury = object(snapshot.get("played_character_gold"), "treasury");
        equalsValue(treasury.get("scale"), number(BigInteger.valueOf(100000)), "treasury scale");
        require(cash.treasuryRaw().equals(integer(treasury.get("raw"), "treasury raw")), "war treasury differs from snapshot");
        BigInteger supply = integer(observation.get("projected_supply_margin_raw"), "measured war supply"), cost = nonnegative(observation.get("incremental_gold_cost_raw"), "incremental war cost"), reserve = nonnegative(observation.get("minimum_gold_reserve_raw"), "war reserve");
        require(cost.equals(cash.value(WarcashModel.Amount.IMMEDIATE).orElseThrow()) && reserve.equals(cash.jointReserve().orElseThrow()), "proposal cash differs from verified war cash");
        List<String> keys = new ArrayList<>(); keys.add("active-war:" + warId); for (BigInteger army : armies) keys.add("active-war-army:" + warId + ":" + army);
        return proposal(frame, "war:continue:defender:" + warId, "war", "one-life-turn-v1", cost, reserve, number(supply), 0, armies, allies, characters, keys,
                obj(f("war_id", number(warId)), f("player_side", new Text("defender")), f("player_is_primary_war_leader", new Bool(true)), f("phase", presentOrNull(plan, "phase")),
                        f("selected_step", plan.get("selected_step")), f("active_war_slot_already_occupied", new Bool(true)), f("war_cash_resource", rawCash)), new Text("active_defensive_continuation"));
    }
}
