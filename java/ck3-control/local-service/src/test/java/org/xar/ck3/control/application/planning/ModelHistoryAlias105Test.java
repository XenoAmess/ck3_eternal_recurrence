package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Qualified pure history shapes reach the actual payload; originals and inverse are checked as encoded bytes. */
final class ModelHistoryAlias105Test {
    private static final int MATERIAL=FullJsonTree.MAXIMUM_BYTES;
    private static final List<String> TECHNICAL=List.of("decoder_source","definition_source","original_receipt","supporting_evidence","source");

    @Test void distinctOrderedRootFactsRemainDistinctAndTrueThirdDuplicateStillAliases()throws Exception {
        Obj a=obj("x",num(1),"y",num(2)),b=obj("y",num(2),"x",num(1));
        List<Obj> original=List.of(rootRow(1,a),rootRow(2,b),rootRow(3,a));
        JsonNode payload=wire(original);
        assertEquals(2,payload.path("root_facts").size());
        assertEquals(List.of(0,1,0),java.util.stream.StreamSupport.stream(payload.path("history").spliterator(),false)
                .map(row->row.path("result").path("campaign_root_context").path("root_ref").intValue()).toList());
        ArrayNode restored=(ArrayNode)payload.path("history").deepCopy();
        for(JsonNode row:restored) {
            ObjectNode result=(ObjectNode)row.get("result");
            JsonNode ref=result.get("campaign_root_context");
            ObjectNode root=(ObjectNode)payload.path("root_facts").get(ref.path("root_ref").intValue()).deepCopy();
            root.set("snapshot_revision",ref.get("snapshot_revision"));
            ((ObjectNode)root.get("player_heir_candidate_v1")).set("snapshot_revision",ref.get("player_heir_candidate_v1_snapshot_revision"));
            result.set("campaign_root_context",root);
        }
        ArrayNode expected=(ArrayNode)toNode(new Arr(new ArrayList<Value>(original)));
        expected.forEach(row->((ObjectNode)row.get("read_history_source")).remove(TECHNICAL));
        assertArrayEquals(bytes(expected),bytes(restored),"inverse retains all ordered game facts, stamps and nontechnical metadata");
    }

    @Test void distinctWholeWarArraysKeepOriginalRowsAndTrueThirdDuplicateReferencesItsActualFirstPosition()throws Exception {
        Arr a=new Arr(List.of(obj("id",num(11),"unknown",obj("x",num(1),"y",num(2)))));
        Arr b=new Arr(List.of(obj("id",num(11),"unknown",obj("y",num(2),"x",num(1)))));
        List<Obj> original=List.of(otherRow(1),warRow(2,a),warRow(3,b),warRow(4,a));
        JsonNode payload=wire(original);
        assertEquals("xar.model-history-declarable-wars-alias/v1",payload.path("history_declarable_wars_projection_schema").textValue());
        assertFalse(payload.has("declarable_war_facts"),"existing whole-array alias path is retained");
        ArrayNode history=(ArrayNode)payload.get("history");
        assertTrue(history.get(2).path("result").has("declarable_wars"),"reordered B cannot reference A");
        assertEquals(1,history.get(3).path("result").path("declarable_wars_history_ref").intValue(),"actual first row position, not intern ordinal");
        ArrayNode restored=history.deepCopy();
        for(JsonNode row:restored) {
            ObjectNode result=(ObjectNode)row.get("result");
            JsonNode ref=result.remove("declarable_wars_history_ref");
            if(ref!=null)result.set("declarable_wars",restored.get(ref.intValue()).path("result").get("declarable_wars").deepCopy());
        }
        assertArrayEquals(bytes(toNode(new Arr(new ArrayList<Value>(original)))),bytes(restored),"whole history exact inverse includes each row's original metadata");
    }

    @Test void occupiedAliasNameKeepsTheExistingWholeHistoryFallbackAndNumericTokensRemainExact()throws Exception {
        Arr a=new Arr(List.of(obj("id",new IntegerValue(new BigInteger("18446744073709551615")),
                "precise",new DecimalValue("1.230000000000000000000000000000e-23"),"zero",new DecimalValue("-0.000"))));
        Obj occupied=otherRow(1).with("result",obj("status",new Text("fixture"),"declarable_wars_history_ref",num(7),"unknown",Nil.INSTANCE));
        List<Obj> original=List.of(occupied,warRow(2,a),warRow(3,a));
        JsonNode payload=wire(original);
        assertFalse(payload.has("history_declarable_wars_projection_schema"));
        assertArrayEquals(bytes(toNode(new Arr(new ArrayList<Value>(original)))),bytes(payload.get("history")));
    }

    private static Obj rootRow(int index,Obj unknown) {
        Obj root=obj("status",new Text("available"),"unknown",unknown,
                "large_id",new IntegerValue(new BigInteger("18446744073709551615")),
                "precise",new DecimalValue("1.230000000000000000000000000000e-23"),
                "player_heir_candidate_v1",obj("candidate",num(7),"snapshot_revision",num(70+index)),
                "snapshot_revision",num(40+index));
        return row(index,"query-campaign-root-context-v1",source(index,"CAMPAIGN_ROOT_CONTEXT","campaign_root_context",true),
                obj("status",new Text("available"),"row_marker",new Text("root-row-"+index),
                        "query_sequence",num(index),"campaign_root_context",root));
    }
    private static Obj warRow(int index,Arr wars) {
        return row(index,"query-declarable-wars",source(index,"DECLARABLE_WARS","declarable_wars",false),
                obj("status",new Text("available"),"row_marker",new Text("war-row-"+index),"query_sequence",num(index),"declarable_wars",wars));
    }
    private static Obj otherRow(int index){return row(index,"fixture-history-opaque",obj("kind",new Text("unfamiliar")),obj("status",new Text("fixture")));}
    private static Obj source(int index,String kind,String field,boolean technical) {
        Obj source=obj("schema",new Text("xar.driver-read-history-source/v1"),"kind",new Text(kind),"payload_field",new Text(field),
                "source_frame",obj("frame",obj("unique_frame",num(index)),"game",obj("fixture_game",num(123)),"machine_id",new Text("fixture-machine")),
                "retained_unknown_metadata",new Text("source-"+index));
        if(technical)for(String key:TECHNICAL)source=source.with(key,new Text("fixture-only-"+key));
        return source;
    }
    private static Obj row(int index,String command,Obj source,Obj result){return obj("index",num(index),"command",new Text(command),"ok",new Bool(true),"read_history_source",source,"result",result);}

    private static JsonNode wire(List<Obj> history)throws Exception {
        // Reuse already qualified P104 fixture builders, never an old @Test method or a copied projection.
        Class<?> fixtures=Class.forName("org.xar.ck3.control.application.planning.ModelHistoryByteIdentity104Test");
        Method snapshot=fixtures.getDeclaredMethod("lifeSnapshot");snapshot.setAccessible(true);
        Obj originalSnapshot=(Obj)snapshot.invoke(null);
        Method scene=fixtures.getDeclaredMethod("scene",String.class,Obj.class,List.class);scene.setAccessible(true);
        Object fixture=scene.invoke(null,"generic",originalSnapshot,history);
        Method selected=fixture.getClass().getDeclaredMethod("proposal");selected.setAccessible(true);
        PlanningResult.ActionSelected proposal=(PlanningResult.ActionSelected)selected.invoke(fixture);
        byte[] beforeCommand=ActionCodec.encodeCommand(proposal.command());
        String beforeSha=ActionCodec.bodySha256(proposal.command());
        byte[] beforeHistory=bytes(toNode(new Arr(new ArrayList<Value>(history))));
        byte[] beforeSnapshot=bytes(toNode(originalSnapshot));
        Method actual=fixtures.getDeclaredMethod("wire",fixture.getClass());actual.setAccessible(true);
        JsonNode result;
        try{result=(JsonNode)actual.invoke(null,fixture);}
        catch(InvocationTargetException failure){if(failure.getCause() instanceof Exception error)throw error;if(failure.getCause() instanceof Error error)throw error;throw failure;}
        assertArrayEquals(beforeCommand,ActionCodec.encodeCommand(proposal.command()));
        assertEquals(beforeSha,ActionCodec.bodySha256(proposal.command()));
        assertEquals(beforeSha,result.path("body_sha256").textValue());
        assertArrayEquals(beforeHistory,bytes(toNode(new Arr(new ArrayList<Value>(history)))));
        assertArrayEquals(beforeSnapshot,bytes(toNode(originalSnapshot)));
        return result;
    }
    private static byte[] bytes(JsonNode node){return FullJsonTree.encode(node,MATERIAL);}
    private static IntegerValue num(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Obj obj(Object... pairs){Map<String,Value> fields=new LinkedHashMap<>();for(int i=0;i<pairs.length;i+=2)fields.put((String)pairs[i],(Value)pairs[i+1]);return new Obj(fields);}
}
