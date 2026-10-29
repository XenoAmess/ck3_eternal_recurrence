package org.xar.ck3.control.wave2.military.forecast;

import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatNumbers.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;

/** Complete active_counter_current_basis.py current-frame pure projector. */
public final class ActiveCurrentCounterProjector {
    private ActiveCurrentCounterProjector() { }
    public record Projection(List<BigInteger> attacks, List<List<BigInteger>> retentions) {
        public Projection { attacks = List.copyOf(attacks); retentions = retentions.stream().map(List::copyOf).toList(); require(attacks.size() == 2 && retentions.size() == 2, "two counter sides required"); }
    }
    /** The native normalizer owns full source/census qualification; this consumes its exact operands. */
    public static Projection project(JsonNode frame) {
        JsonNode counter = field(frame, "active_counter_inputs_v1");
        require(counter != null && counter.isObject() && is(counter.get("status"), "available") && yes(counter.get("operand_census_complete")) && is(field(frame, "side_scope"), "full_side"), "complete actual current-frame counter census required");
        int count = intValue(counter.get("class_count"), "counter class count"); List<JsonNode> sides = elements(counter.get("sides"), "counter sides"), contexts = elements(counter.get("contexts"), "counter contexts");
        require(count > 0 && count <= 4096 && sides.size() == 2 && contexts.size() == 2, "current-frame counter shape is incomplete");
        List<List<BigInteger>> retentions = new ArrayList<>();
        for (int index = 0; index < 2; index++) {
            JsonNode context = contexts.get(index); require(intValue(context.get("countered_side_index"), "countered side") == index && intValue(context.get("countering_side_index"), "countering side") == 1 - index, "directional counter context disagrees");
            List<BigInteger> own = new ArrayList<>(), pressure = new ArrayList<>(); for (int c = 0; c < count; c++) { own.add(ZERO); pressure.add(ZERO); }
            for (JsonNode entry : elements(sides.get(index).get("men_at_arms_entries"), "own counter MAA")) if (is(entry.get("status"), "available")) { int c = classIndex(entry.get("class_index"), count); own.set(c, own.get(c).add(integer(entry.get("current_chunk_raw"), "counter chunk"))); }
            for (JsonNode entry : elements(sides.get(1 - index).get("men_at_arms_entries"), "opposing counter MAA")) if (is(entry.get("status"), "available")) for (JsonNode target : elements(entry.get("targets"), "counter targets")) {
                int c = classIndex(target.get("class_index"), count); BigInteger value = mul(mul(integer(entry.get("current_chunk_raw"), "counter chunk"), integer(target.get("effectiveness_raw"), "counter effectiveness")), integer(context.get("context_scale_raw"), "counter context scale")); pressure.set(c, pressure.get(c).add(value));
            }
            List<BigInteger> retention = new ArrayList<>(); for (int c = 0; c < count; c++) retention.add(own.get(c).signum() == 0 ? SCALE : SCALE.subtract(mul(SCALE.min(fixedDiv(fixedDiv(pressure.get(c), own.get(c)), n(200_000))), n(90_000)))); retentions.add(retention);
        }
        List<BigInteger> attacks = new ArrayList<>();
        for (int side = 0; side < 2; side++) {
            JsonNode battle = field(frame, side == 0 ? "attacker" : "defender"); BigInteger total = ZERO;
            for (JsonNode entry : elements(field(battle, "levy_entries"), "current levy entries")) if (yes(entry.get("fights_in_main_phase"))) total = total.add(mul(integer(entry.get("effective_damage_raw"), "levy damage"), integer(entry.get("current_fighting_raw"), "levy current")));
            List<JsonNode> entries = elements(field(battle, "men_at_arms_entries"), "current MAA entries"), operands = elements(sides.get(side).get("men_at_arms_entries"), "paired counter MAA");
            require(entries.size() == operands.size(), "MAA counter census disagrees with battle entries");
            for (int i = 0; i < entries.size(); i++) {
                JsonNode entry = entries.get(i), operand = operands.get(i);
                require(integer(entry.get("regiment_id"), "RegimentID").equals(integer(operand.get("regiment_id"), "counter RegimentID")) && integer(entry.get("current_fighting_raw"), "current").equals(integer(operand.get("current_fighting_raw"), "counter current")), "MAA counter entry differs from current battle entry");
                if (!yes(entry.get("fights_in_main_phase"))) continue;
                BigInteger damage = integer(entry.get("effective_damage_raw"), "MAA damage");
                if (is(operand.get("status"), "available")) damage = mul(damage, retentions.get(side).get(classIndex(operand.get("class_index"), count)));
                total = total.add(mul(damage, integer(entry.get("current_fighting_raw"), "MAA current")));
            }
            attacks.add(total);
        }
        return new Projection(attacks, retentions);
    }
    static int classIndex(JsonNode value, int count) { int result = intValue(value, "counter class index"); require(result >= 0 && result < count, "counter class outside census"); return result; }
}
