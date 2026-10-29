package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmySnapshotCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Preserved software native frame -> current full projection -> consumers -> original manifest replay. */
final class DriverCanonicalObservationTest {
    private static ObjectNode raw() {
        ObjectNode state=(ObjectNode)DriverJson.toNode(DriverJson.object(bytes(DriverObservationAssemblerTest.STATE),DriverJson.MAX_NATIVE_BYTES));
        ObjectNode explicit=state.withArray("player_armies").addObject().put("army_id",0).put("owner_character_id",73)
                .put("controllable",true).put("soldiers",101).putNull("siege_days_left");
        explicit.putArray("route_province_ids").add(300).add(300).add(301);
        explicit.put("route_read_status","complete_nonempty").put("route_source_count",3)
                .put("move_target_province_id",301).put("move_target_observable",true);
        ObjectNode war=state.withArray("active_wars").addObject().put("war_id",BigInteger.ONE.shiftLeft(70))
                .put("player_side","defender").put("player_relative_war_score",-12);
        war.putArray("targeted_title_ids").add(0).add(0).add(8);
        war.putArray("war_objective_province_ids").add(300);
        ObjectNode objective=war.putArray("objective_province_states").addObject().put("province_id",300)
                .put("occupation_observable",false).put("siege_observable",true);
        ObjectNode siege=objective.putObject("active_siege").put("siege_id",0).put("player_army_besieging",true);
        for(String key:List.of("progress_fraction","current_work","total_work"))
            siege.putObject(key).put("raw",key.equals("total_work")?100000:0).put("scale",100000);
        siege.put("assault_observable",false);
        var allied=war.putArray("allied_armies");
        allied.addObject().put("army_id",0).put("owner_character_id",73).put("controllable",true).put("soldiers",999);
        allied.addObject().put("army_id",4).put("owner_character_id",73).put("controllable",true).put("soldiers",22);
        allied.addObject().put("army_id",6).put("owner_character_id",74).put("controllable",false);
        war.putArray("enemy_armies").addObject().put("army_id",8).put("owner_character_id",75).put("controllable",false);
        return state;
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static DriverObservationFacts facts(org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame frame,
            long version,OpportunityJson.Obj extra) {
        var known=DriverStateAssemblerTest.known();
        return new DriverObservationFacts(known.driver(),3,7,frame.session(),frame.snapshotId(),frame.nativeRevision(),
                DriverJson.sha256(frame.state().bytes()),BigInteger.valueOf(2),version,DriverStateAssemblerTest.source(),extra,
                DriverStateAssemblerTest.ref(bytes("actual facts")));
    }
    private static DriverObservationAssembler.FullSnapshot project(ObjectNode state,long version) {
        var frame=DriverObservationAssemblerTest.actual(new String(DriverJson.encodeNode(state),StandardCharsets.UTF_8));
        return new DriverObservationAssembler().projectFull(frame,facts(frame,version,new OpportunityJson.Obj(Map.of())),
                DriverStateAssemblerTest.ref(frame.originalPacket()));
    }
    @Test void historicalVersionTwoKeepsFullWarsStableArmyUnionAndThePublicWarConsumer() {
        ObjectNode raw=raw();var projected=project(raw,2);var semantic=projected.semantic();
        var tree=DriverJson.toNode(semantic);var armies=tree.get("player_armies");var war=tree.get("active_wars").get(0);
        assertEquals(2,armies.size());assertEquals(0,armies.get(0).get("army_id").intValue());
        assertEquals(101,armies.get(0).get("soldiers").intValue());assertEquals(4,armies.get(1).get("army_id").intValue());
        assertEquals(3,armies.get(0).get("route_province_ids").size());
        assertTrue(armies.get(0).has("siege_days_left"));assertTrue(armies.get(0).get("siege_days_left").isNull());
        assertFalse(armies.get(1).has("siege_days_left"));
        assertEquals(BigInteger.ONE.shiftLeft(70),war.get("war_id").bigIntegerValue());
        assertEquals(2,war.get("targeted_title_ids").size());
        var siege=war.get("objective_province_states").get(0).get("active_siege");
        assertEquals(0,siege.get("siege_id").intValue());assertEquals(100000,siege.get("remaining_work").get("raw").intValue());
        assertTrue(siege.get("assault_in_progress").isNull());assertEquals("native",war.get("source").textValue());
        assertArrayEquals(DriverJson.encodeNode(raw),projected.actual().state().bytes());
        var publicState=ArmySnapshotCodec.state(DriverJson.encode(semantic),projected.actual().snapshotId(),
                projected.facts().publicRevision(),projected.actual().nativeRevision());
        var publicJson=DriverJson.object(ArmySnapshotCodec.encode(publicState).bytes(),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(semantic.get("active_wars"),publicJson.get("active_wars"));
        assertEquals(semantic.get("player_armies"),publicJson.get("player_armies"));
        assertEquals(2,projected.facts().observationVersion());
    }
    @Test void completeCurrentRulesRejectPartialWarsWrongTypesAndInconsistentRouteEvidence() {
        ObjectNode partial=raw();((ObjectNode)partial.get("active_wars").get(0)).remove("player_side");
        ObjectNode wrongScore=raw();((ObjectNode)wrongScore.get("active_wars").get(0)).put("player_relative_war_score",true);
        ObjectNode wrongOwner=raw();((ObjectNode)wrongOwner.get("player_armies").get(0)).put("owner_character_id",1.0);
        ObjectNode wrongRoute=raw();((ObjectNode)wrongRoute.get("player_armies").get(0)).put("route_source_count",2);
        ObjectNode wrongSiege=raw();((ObjectNode)wrongSiege.get("active_wars").get(0).get("objective_province_states").get(0).get("active_siege"))
                .putObject("current_work").put("raw",false).put("scale",100000);
        for(ObjectNode bad:List.of(partial,wrongScore,wrongOwner,wrongRoute,wrongSiege))
            assertThrows(IllegalArgumentException.class,()->project(bad,2));
        ObjectNode modal=raw();modal.remove("active_event");
        assertThrows(IllegalArgumentException.class,()->project(modal,2));
    }
    @Test void historicalProjectionIsExplicitAndUnknownVersionsNeverJoin() {
        ObjectNode state=raw();((ObjectNode)state.get("active_wars").get(0)).remove("player_side");
        var legacy=project(state,1);
        assertEquals(DriverJson.fromNode(state.get("active_wars")),legacy.semantic().get("active_wars"));
        assertThrows(IllegalArgumentException.class,()->project(state,2));
        assertThrows(IllegalArgumentException.class,()->project(raw(),99));
        ObjectNode missing=raw();missing.remove("active_wars");missing.putNull("player_armies");
        var current=project(missing,2).semantic();
        assertTrue(OpportunityJson.array(current.get("active_wars"),"active_wars").isEmpty());
        assertTrue(OpportunityJson.array(current.get("player_armies"),"player_armies").isEmpty());
    }
    @Test void canonicalCollectionsCannotOverwriteTheOriginalPacketOrBeInjectedThroughAuxiliary() {
        ObjectNode raw=raw();var frame=DriverObservationAssemblerTest.actual(new String(DriverJson.encodeNode(raw),StandardCharsets.UTF_8));
        var extra=new OpportunityJson.Obj(Map.of("player_armies",DriverObservationAssembler.canonicalNativeState(frame).semantic().get("player_armies")));
        assertThrows(IllegalArgumentException.class,()->new DriverObservationAssembler().projectFull(frame,facts(frame,2,extra),
                DriverStateAssemblerTest.ref(frame.originalPacket())));
        byte[] broken=frame.originalPacket();broken[0]^=1;
        var drifted=new org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame(frame.session(),frame.snapshotId(),
                frame.nativeRevision(),frame.state(),broken,frame.observedAt());
        assertThrows(IllegalArgumentException.class,()->DriverObservationAssembler.originalNativeState(drifted));
    }
    @Test void archivedVersionTwoReplaysIdenticalSemanticsAndRetainsOriginalDecimalTokens() {
        String wire=new String(DriverJson.encodeNode(raw()),StandardCharsets.UTF_8).replace("\"speed\":3","\"speed\":3,\"original_metric\":1.00");
        var actual=DriverObservationAssemblerTest.actual(wire);var known=DriverStateAssemblerTest.known();
        var driverRef=DriverStateAssemblerTest.ref(known.driver().encode());
        RawJson manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(2),2,DriverStateAssemblerTest.source(),
                new OpportunityJson.Obj(Map.of()),driverRef);
        var exact=DriverStateAssemblerTest.ref(manifest.bytes());
        var restored=DriverObservationEvidenceReader.nativeFrame(exact,manifest,actual.originalPacket());
        var decoded=DriverObservationEvidenceReader.decode(exact,manifest,new RawJson(known.driver().encode()),restored);
        var assembler=new DriverObservationAssembler();
        var before=assembler.projectFull(actual,decoded,DriverStateAssemblerTest.ref(actual.originalPacket()));
        var after=assembler.projectFull(restored,decoded,DriverStateAssemblerTest.ref(restored.originalPacket()));
        assertArrayEquals(actual.state().bytes(),restored.state().bytes());
        assertTrue(new String(restored.state().bytes(),StandardCharsets.UTF_8).contains("1.00"));
        assertEquals(before.semantic(),after.semantic());assertEquals(2,decoded.observationVersion());
        byte[] changed=actual.originalPacket();changed[changed.length-2]^=1;
        assertThrows(IllegalArgumentException.class,()->DriverObservationEvidenceReader.nativeFrame(exact,manifest,changed));
    }
    @Test void fullFrameTreeBridgeKeepsExactIntegersBeyondReceiptBudgetAndRejectsLossyOrForeignNodes() {
        ObjectNode tree=JsonNodeFactory.instance.objectNode().put("large","x".repeat(1048580))
                .put("id",BigInteger.ONE.shiftLeft(100)).putNull("nil");
        tree.putArray("ordered").add(0).add(0).add(BigInteger.ONE.shiftLeft(64));
        byte[] wire=DriverJson.encodeNode(tree);
        assertTrue(wire.length>1048576);
        var restored=DriverJson.toNode(DriverJson.object(wire,DriverJson.MAX_NATIVE_BYTES));
        assertArrayEquals(wire,DriverJson.encodeNode(restored));
        assertEquals(BigInteger.ONE.shiftLeft(100),restored.get("id").bigIntegerValue());
        assertThrows(IllegalArgumentException.class,()->DriverJson.fromNode(JsonNodeFactory.instance.numberNode(1.0)));
        assertThrows(IllegalArgumentException.class,()->DriverJson.fromNode(JsonNodeFactory.instance.binaryNode(new byte[]{1})));
        assertEquals(new OpportunityJson.DecimalValue("-0.0"),DriverJson.fromNormalizedNode(JsonNodeFactory.instance.numberNode(-0.0)));
        assertEquals(new OpportunityJson.DecimalValue("1.0"),DriverJson.fromNormalizedNode(JsonNodeFactory.instance.numberNode(1.0)));
        assertThrows(IllegalArgumentException.class,()->DriverJson.fromNormalizedNode(JsonNodeFactory.instance.numberNode(Double.NaN)));
    }
    @Test void newVersionCanonicalizesOnlyTheOriginalFrameAndLeavesHistoricalEventShapeUntouched() {
        ObjectNode state=raw();state.putObject("active_event");
        var old=project(state,2);var current=project(state,3);
        assertEquals(new OpportunityJson.Obj(Map.of()),old.semantic().get("active_event"));
        assertEquals(OpportunityJson.Nil.INSTANCE,OpportunityJson.object(current.semantic().get("active_event"),"event").get("option_count"));
        state.remove("active_event");
        assertThrows(IllegalArgumentException.class,()->project(state,2));
        assertEquals(OpportunityJson.Nil.INSTANCE,project(state,3).semantic().get("active_event"));
        assertEquals(new OpportunityJson.Obj(Map.of()),DriverObservationAssembler.originalNativeState(current.actual()).get("active_event"));
    }
}
