package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Executes the production data validator against the real original startup producer's retained cases. */
final class FixtureStartupObservationTest {
    @TempDir Path temporary;
    private static JsonNode resource(String name)throws Exception {
        try(var input=FixtureStartupObservationTest.class.getResourceAsStream("/frontend-fixture/"+name)){assertNotNull(input);return StrictJson.parse(input.readAllBytes(),1<<20);}
    }
    private static OpportunityJson.Obj value(JsonNode n) {return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(n,1<<20)),"original startup fixture");}
    @Test void originalReadOnlyScenarioProducerAndAllSevenMalformedBranchesAgree()throws Exception {
        PreparedFixtureTest files=new PreparedFixtureTest();files.temporary=temporary;PreparedFixture fixture=files.create(true).prepared();
        JsonNode oracle=resource("python-startup-oracle04.json");
        ObjectNode submitted=(ObjectNode)resource("python-producer-oracle04.json").get("submissions").get(2).get("receipt").deepCopy();submitted.set("policy_binding",fixture.binding().toJson());
        var submission=FixtureStartSubmission.fromJson(submitted);int count=0;
        for(JsonNode row:oracle.get("cases")) {
            ObjectNode base=(ObjectNode)oracle.get("base").deepCopy();ObjectNode before=(ObjectNode)base.get("before"),after=(ObjectNode)base.get("after"),packet=(ObjectNode)base.get("packet");
            ObjectNode context=(ObjectNode)packet.get("current_event_window_context");String change=row.get("mutation").asText();
            switch(change) {
                case "none"->{ }
                case "duplicate-index"->((ObjectNode)context.withArray("options").get(1)).put("native_option_index",2);
                case "bool-index"->((ObjectNode)context.withArray("options").get(0)).put("native_option_index",true);
                case "wrong-definition"->context.put("event_definition_key","other.1");
                case "after-event-change"->((ObjectNode)after.get("active_event")).put("instance_id",918);
                case "wrong-frame"->packet.put("queried_revision",11);
                case "wrong-build"->((ObjectNode)before.get("diagnostics").get("hello")).put("expected_ck3_version","1.20.0.3");
                default->fail("original producer case not consumed: "+change);
            }
            var current=FixtureBusinessQualification.owner(value(before),submission,true).orElseThrow();var previous=current.stable();
            if(row.get("error").isNull())assertEquals(List.of(2,5),FixtureStartupObservation.validatePresentation(fixture,submission,previous,current,value(before),value(packet),value(after)));
            else assertThrows(IllegalArgumentException.class,()->FixtureStartupObservation.validatePresentation(fixture,submission,previous,current,value(before),value(packet),value(after)),change);
            count++;
        }
        assertEquals(7,count);
    }
    @Test void privateActualReadProofCannotBeRehydratedFromPureValidatedData() {
        assertTrue(java.util.Arrays.stream(FixtureStartupObservation.Proof.class.getDeclaredConstructors()).allMatch(c->java.lang.reflect.Modifier.isPrivate(c.getModifiers())));
        assertTrue(java.util.Arrays.stream(FixtureStartupObservation.Proof.class.getMethods()).noneMatch(m->m.getName().equals("fromJson")||m.getName().equals("decode")));
    }
}
