package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original stable owner/main-pump qualifications drive the real reducer; one ACK or one root never qualifies. */
final class FixtureBusinessQualificationTest {
    @TempDir Path temporary;
    private record Case(PreparedFixture prepared,FixtureStartSubmission submission,ObjectNode snapshot,ObjectNode root,FixtureQualificationLogs.Observation logs) { }
    private Case create()throws Exception {
        PreparedFixtureTest files=new PreparedFixtureTest();files.temporary=temporary;var fixture=files.create(false);
        JsonNode oracle;try(var input=getClass().getResourceAsStream("/frontend-fixture/python-producer-oracle04.json")){assertNotNull(input);oracle=StrictJson.parse(input.readAllBytes(),1<<20);}
        ObjectNode submitted=(ObjectNode)oracle.get("submissions").get(0).get("receipt").deepCopy();submitted.set("policy_binding",fixture.prepared().binding().toJson());
        ObjectNode snapshot=(ObjectNode)oracle.get("business_cases").get(0).get("snapshot").deepCopy();
        snapshot.put("local_player_id",1);snapshot.putNull("active_event");((ObjectNode)snapshot.get("played_character")).put("alive",true).put("source","native");
        ObjectNode heartbeat=(ObjectNode)snapshot.get("diagnostics").get("last_heartbeat");heartbeat.put("pid",71);
        ObjectNode mailbox=(ObjectNode)heartbeat.get("main_thread_query_mailbox_v1");mailbox.put("ready",true).put("stamp_read_success",true).put("owner_tid",81).put("current_tid",81);
        epoch(snapshot,1);
        ObjectNode root=(ObjectNode)oracle.get("business_cases").get(0).get("root").deepCopy();
        Files.createDirectories(fixture.profile().resolve("logs"));Files.writeString(fixture.profile().resolve("logs/debug.log"),"FIXTURE: qualified\nFIXTURE: switched\n");
        return new Case(fixture.prepared(),FixtureStartSubmission.fromJson(submitted),snapshot,root,FixtureQualificationLogs.observe(fixture.prepared()));
    }
    private static void epoch(ObjectNode snapshot,int value) {((ObjectNode)snapshot.get("diagnostics").get("last_heartbeat").get("main_thread_query_mailbox_v1")).put("pump_epochs",value).put("owner_verified_pump_epochs",value);}
    private static OpportunityJson.Obj value(ObjectNode raw) {return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(raw,1<<20)),"actual original fixture JSON");}
    @Test void twoStableOwnerAndTwoActualRootActorPumpObservationsFinallyProveTarget()throws Exception {
        var c=create();var reducer=new FixtureBusinessQualification(c.prepared(),c.submission());
        assertEquals(FixtureBusinessQualification.Stage.WAITING_OWNER,reducer.observeOwner(value(c.snapshot()),c.logs(),false).stage());
        epoch(c.snapshot(),2);assertEquals(FixtureBusinessQualification.Stage.OWNER_QUERY_ADMITTED,reducer.observeOwner(value(c.snapshot()),c.logs(),false).stage());
        var first=reducer.observeBusiness(value(c.snapshot()),value(c.root()),c.logs(),false);assertFalse(first.fixtureTargetIdentityProven());
        epoch(c.snapshot(),3);reducer.observeOwner(value(c.snapshot()),c.logs(),false);
        var actual=reducer.observeBusiness(value(c.snapshot()),value(c.root()),c.logs(),false);assertTrue(actual.fixtureTargetIdentityProven());
        assertEquals(FixtureBusinessQualification.Stage.QUALIFIED,actual.stage());assertEquals(java.math.BigInteger.valueOf(922),actual.actor().orElseThrow().actorCharacterId());
    }
    @Test void samePumpAndChangedOriginalOwnerNeverAdmitWholeRootQuery()throws Exception {
        var c=create();var reducer=new FixtureBusinessQualification(c.prepared(),c.submission());
        reducer.observeOwner(value(c.snapshot()),c.logs(),false);assertEquals(FixtureBusinessQualification.Stage.WAITING_OWNER,reducer.observeOwner(value(c.snapshot()),c.logs(),false).stage());
        epoch(c.snapshot(),2);c.snapshot().put("revision",11);assertEquals(FixtureBusinessQualification.Stage.WAITING_OWNER,reducer.observeOwner(value(c.snapshot()),c.logs(),false).stage());
        assertThrows(IllegalArgumentException.class,()->reducer.observeBusiness(value(c.snapshot()),value(c.root()),c.logs(),false));
    }
    @Test void logQualificationPrecedesAnyWholeRootAndRepeatedInitializationIsFatal()throws Exception {
        var c=create();var reducer=new FixtureBusinessQualification(c.prepared(),c.submission());
        assertEquals(FixtureBusinessQualification.Stage.WAITING_LOGS,reducer.observeOwner(value(c.snapshot()),new FixtureQualificationLogs.Observation(false,java.util.Optional.empty(),java.util.List.of()),false).stage());
        Files.writeString(c.prepared().profileDirectory().resolve("logs/debug.log"),"FIXTURE: qualified\nFIXTURE: qualified\nFIXTURE: switched\n");
        assertThrows(IllegalStateException.class,()->reducer.observeOwner(value(c.snapshot()),FixtureQualificationLogs.observe(c.prepared()),false));
    }
    @Test void changedProcessBooleanIdentityAndUnverifiedActiveEventCannotBecomeOwnerProof()throws Exception {
        var c=create();ObjectNode changed=c.snapshot().deepCopy();((ObjectNode)changed.get("diagnostics")).put("connection_generation",3);
        assertThrows(IllegalArgumentException.class,()->FixtureBusinessQualification.owner(value(changed),c.submission(),false));
        ObjectNode bool=c.snapshot().deepCopy();((ObjectNode)bool.get("played_character")).put("character_id",true);
        assertThrows(IllegalArgumentException.class,()->FixtureBusinessQualification.owner(value(bool),c.submission(),false));
        ObjectNode event=c.snapshot().deepCopy();event.putObject("active_event").put("instance_id",5);
        assertTrue(FixtureBusinessQualification.owner(value(event),c.submission(),false).isEmpty());
    }
}
