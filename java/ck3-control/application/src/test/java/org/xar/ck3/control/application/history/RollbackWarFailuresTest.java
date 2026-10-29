package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real NativeDriver discarded-branch regression shapes, exercising the shared production producer. */
final class RollbackWarFailuresTest {
    private static Obj json(String value) { return OpportunityJson.object(OpportunityJson.parse(value.getBytes(StandardCharsets.UTF_8)), "fixture"); }
    private static Obj checkpoint() { return json("{\"sha256\":\"" + "a".repeat(64) + "\",\"size\":17,\"date_raw\":24000,\"history_index\":1}"); }
    private static Obj restored(int armyId) { return json("{\"date_raw\":24000,\"player_armies\":[{\"army_id\":"+armyId+",\"current_province_id\":48}],\"active_wars\":[{\"war_id\":25,\"allied_armies\":[{\"army_id\":"+armyId+",\"controllable\":true}]}]}"); }
    private static Obj row(int index, String command, Obj result) {
        return json("{\"index\":"+index+",\"command\":\""+command+"\",\"ok\":true}").with("result",result);
    }
    private static List<Obj> epoch(int army, int target) {
        return List.of(row(2,"preview-move-army-"+army+"-to-"+target,json("{\"route_preview\":{\"status\":\"available\",\"army_id\":"+army+",\"origin_province_id\":48,\"target_province_id\":"+target+",\"route_province_ids\":[50,53,"+target+"],\"previewed_date_raw\":24000}}")),
                row(3,"move-army-"+army+"-to-"+target,json("{\"war_action\":{\"status\":\"moving\",\"army_id\":"+army+",\"target_province_id\":"+target+",\"submitted_date_raw\":24000},\"player_armies\":[{\"army_id\":"+army+",\"move_target_province_id\":"+target+",\"route_province_ids\":[53,"+target+"]}]}")));
    }
    private static Obj event(int index) { return row(index,"query-current-event-window-context-v1",json("{\"accepted\":true,\"status\":\"available\",\"current_event_instance_id\":3,\"current_event_window_context\":{\"status\":\"available\",\"window_match_count\":1,\"current_event_instance_id\":3,\"event_definition_key\":\"death_management.1000\"}}")); }
    private static RollbackWarFailures.Failure derive(List<Obj> rows,int army) {
        return RollbackWarFailures.deriveEpoch(rows,checkpoint(),restored(army),"native-31853-r849",Optional.empty()).orElseThrow();
    }
    @Test void actualUnresolvedEventDoesNotBecomeFalseRouteFailure() {
        var healthy = new ArrayList<>(epoch(304,52)); healthy.add(event(4));
        assertTrue(RollbackWarFailures.deriveEpoch(healthy,checkpoint(),restored(304),"native-31853-r849",Optional.empty()).isEmpty());
        var selected = new ArrayList<>(epoch(304,52)); selected.add(row(4,"select-event-option-2",json("{\"status\":\"postcondition_verified\"}"))); selected.add(event(5));
        assertEquals(52,derive(selected,304).entry().targetProvinceId());
        var queryNotLast = new ArrayList<>(healthy); queryNotLast.add(row(5,"query-campaign-root-context-v1",json("{\"status\":\"available\"}")));
        assertEquals(52,derive(queryNotLast,304).entry().targetProvinceId());
    }
    @Test void discardedRouteComesFromFreshPreviewAndRealStillMovingPoststate() {
        var failure=derive(epoch(304,52),304);
        assertEquals(List.of(50,53,52),failure.entry().provinceIds()); assertEquals(48,failure.scope().restoredOriginProvinceId());
        assertEquals(52,failure.terminal().orElseThrow().targetProvinceId());
        var rows = new ArrayList<>(epoch(304,52));
        rows.set(1,row(3,"move-army-304-to-52",json("{\"war_action\":{\"status\":\"moving\",\"army_id\":304,\"target_province_id\":52,\"submitted_date_raw\":24024},\"player_armies\":[{\"army_id\":304,\"move_target_province_id\":52,\"route_province_ids\":[52]}]}")));
        assertTrue(RollbackWarFailures.deriveEpoch(rows,checkpoint(),restored(304),"e",Optional.empty()).isEmpty());
        assertTrue(RollbackWarFailures.deriveEpoch(epoch(304,52),checkpoint(),restored(304),"e",Optional.of(json("{\"date_raw\":24024,\"player_armies\":[]}"))).isEmpty());
    }
    @Test void publicZeroIdentitySurvivesProducerSerdeAndScopeDedupe() {
        var first=derive(epoch(0,52),0); var second=derive(epoch(0,54),0); var differentScope=derive(epoch(1,55),1);
        Obj encoded=RollbackWarFailures.encode(first);
        assertEquals(first,RollbackWarFailures.decode(OpportunityJson.parse(OpportunityJson.encode(encoded))).orElseThrow());
        assertEquals(List.of(first,second),RollbackWarFailures.bounded(List.of(first,first,differentScope,second)));
        assertEquals(0,first.scope().armyId());
        assertTrue(RollbackWarFailures.decode(encoded.with("army_id",new Bool(false))).isEmpty());
        assertTrue(RollbackWarFailures.decode(encoded.with("army_id",new DecimalValue("0.0"))).isEmpty());
        assertTrue(RollbackWarFailures.decode(encoded.with("unexpected_alias",new Text("x"))).isEmpty());
        var nullable=encoded.with("abandoned_date_raw",Nil.INSTANCE);
        assertEquals(Nil.INSTANCE,RollbackWarFailures.encode(RollbackWarFailures.decode(nullable).orElseThrow()).get("abandoned_date_raw"));
        var fields=new java.util.LinkedHashMap<>(encoded.members()); fields.remove("abandoned_date_raw");
        assertFalse(RollbackWarFailures.encode(RollbackWarFailures.decode(new Obj(fields)).orElseThrow()).members().containsKey("abandoned_date_raw"));
    }
    @Test void newestCompletedEpochFallbackNeverCrossesCheckpointAnchorOrLimit() {
        List<Obj> history=new ArrayList<>(); history.add(row(1,"save-checkpoint",json("{}").with("checkpoint",checkpoint())));
        history.addAll(epoch(304,52)); history.add(row(4,"restore-checkpoint",json("{\"status\":\"restored\"}")));
        for(Obj original:epoch(304,54)) history.add(original.with("index",new IntegerValue(BigInteger.valueOf(history.size()+1L))));
        history.add(row(7,"restore-checkpoint",json("{\"status\":\"restored\"}")));
        var one=RollbackWarFailures.deriveCompleted(history,checkpoint(),restored(304),"native-31853-r849",1);
        assertEquals(List.of(54),one.stream().map(value->value.entry().targetProvinceId()).toList());
        var two=RollbackWarFailures.deriveCompleted(history,checkpoint(),restored(304),"native-31853-r849",2);
        assertEquals(List.of(54,52),two.stream().map(value->value.entry().targetProvinceId()).toList());
        assertEquals(54,RollbackWarFailures.deriveCurrent(history,checkpoint(),restored(304),"native-31853-r849",Optional.empty(),2).orElseThrow().entry().targetProvinceId());
        assertTrue(RollbackWarFailures.deriveCurrent(history,checkpoint().with("history_index",new Bool(true)),restored(304),"native-31853-r849",Optional.empty(),2).isEmpty());
    }
    @Test void autoTurnOuterPresenceAndArrivalCloseActualEpoch() {
        var rows=new ArrayList<>(epoch(304,52)); Obj direct=rows.getLast();
        Obj decorated=row(3,"auto-turn",json("{\"auto_turn\":{\"selected_step\":\"move-army-304-to-52\"}}").with("player_armies",new Arr(List.of()))
                .with("war_action",OpportunityJson.object(direct.get("result"),"r").get("war_action")));
        rows.set(1,decorated); assertTrue(RollbackWarFailures.deriveEpoch(rows,checkpoint(),restored(304),"e",Optional.empty()).isEmpty());
        rows=new ArrayList<>(epoch(304,52)); rows.add(row(4,"move-army-304-to-52",json("{\"war_action\":{\"status\":\"arrived\"}}")));
        assertTrue(RollbackWarFailures.deriveEpoch(rows,checkpoint(),restored(304),"e",Optional.empty()).isEmpty());
    }
}
