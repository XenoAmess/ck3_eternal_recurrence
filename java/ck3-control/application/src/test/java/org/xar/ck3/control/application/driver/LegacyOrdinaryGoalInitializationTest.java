package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Exercises the real Driver owner/goal serde/ordinary consumer. Reader is an explicit software I/O seam. */
final class LegacyOrdinaryGoalInitializationTest {
    private static final Instant NOW=Instant.parse("2026-10-25T00:00:00Z");
    private static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
    private static DriverSnapshotFacts.Known legacy(boolean ordinary){
        var nil=new DriverStateSnapshot.NullValue();
        var lifecycle=new DriverStateSnapshot.Value(bytes("{\"lifecycle\":\""+(ordinary?"ordinary_campaign_succession":"rogue_one_life")+"\"}"));
        var d=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-pipe",42,BigInteger.valueOf(73),"episode-real-1"),
                List.of(),nil,new DriverStateSnapshot.Value(bytes("{\"old\":true}")),nil,nil,lifecycle,nil,new DriverStateSnapshot.Value(bytes("[]")));
        return DriverFactsRepository.imported(DriverStateAssemblerTest.ref(d.encode()),d.encode(),3,7,DriverStateAssemblerTest.game(),new OpportunityJson.Obj(java.util.Map.of()));
    }
    private static NativeObservationPort.ObservedFrame frame(String actor){
        byte[] raw=bytes("{\"paused\":true,\"map_ready\":true,\"date_raw\":53144328,\"played_character\":{\"character_id\":"+actor+",\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"active_wars\":[],\"player_armies\":[]}");
        byte[] body=bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":2,\"state\":"+new String(raw,StandardCharsets.UTF_8)+"}");
        byte[] packet=ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        return new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",DriverStateAssemblerTest.game(),BigInteger.ONE,"held-session"),"snapshot-9",BigInteger.TWO,new RawJson(raw),packet,NOW);
    }
    private static final class Reader implements DriverObservationFacts.Reader {
        final DriverFactsRepository repository;int calls;
        Reader(DriverFactsRepository r){repository=r;}
        @Override public DriverObservationFacts.Result read(NativeObservationPort.ObservedFrame actual){
            calls++;var k=(DriverSnapshotFacts.Known)repository.locked(state->state);
            return new DriverObservationFacts.Known(new DriverObservationFacts(k.driver(),k.stamp().driverVersion(),k.stamp().episodeEpoch(),actual.session(),actual.snapshotId(),actual.nativeRevision(),DriverJson.sha256(actual.state().bytes()),BigInteger.valueOf(9),1,DriverStateAssemblerTest.source(),DriverObservationAssembler.originalNativeState(actual),DriverStateAssemblerTest.ref(bytes("software-manifest-"+calls))));
        }
    }
    private record Fixture(DriverStateAssembler owner,DriverFactsRepository repository,Reader reader) { }
    private static Fixture fixture(DriverSnapshotFacts.Known k,List<ActionReceipt> actions){
        var repository=new DriverFactsRepository(k);var reader=new Reader(repository);
        var journal=new DriverStateAssemblerTest.Journal(DriverStateAssemblerTest.snapshot(k,actions));
        ActionJournal facade=new ActionJournal(){
            @Override public <T>T locked(java.util.function.Function<LockedJournal,T> work){return journal.locked(work);}
            @Override public <T>T locked(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,java.util.function.Function<LockedJournal,T> work){assertSame(RAW_SESSION,same);return journal.locked(work);}
        };
        return new Fixture(new DriverStateAssembler(new ActionSnapshotReader(facade),repository,reader),repository,reader);
    }
    private static final org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session RAW_SESSION=new org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session(){
        @Override public void requireWriter(java.nio.file.Path p){throw new AssertionError("software scope has no writer");}
        @Override public org.xar.ck3.control.continuity.writer.WriterContracts.Pin capturePin(org.xar.ck3.control.contracts.ExactRef ref,int max){throw new AssertionError("no pins");}
        @Override public void verifyPin(org.xar.ck3.control.continuity.writer.WriterContracts.Pin pin){throw new AssertionError("no pins");}
        @Override public org.xar.ck3.control.continuity.writer.WriterContracts.Head head(){throw new AssertionError("journal supplies original snapshot");}
        @Override public org.xar.ck3.control.continuity.writer.WriterContracts.Prepared preview(org.xar.ck3.control.continuity.writer.WriterContracts.Request r){throw new AssertionError("no mutation");}
        @Override public org.xar.ck3.control.continuity.writer.WriterContracts.Receipt commit(org.xar.ck3.control.continuity.writer.WriterContracts.Prepared p){throw new AssertionError("no mutation");}
        @Override public org.xar.ck3.control.contracts.ExactRef persistedHead(){throw new AssertionError("no new head");}
    };
    @Test void rawRestoreProbeKeepsOriginalNullUntilLaterOrdinaryObservation()throws Exception{
        var before=legacy(true);var f=fixture(before,List.of());var actual=frame("73");
        f.owner().withFrozenRawObservation(actual,RAW_SESSION,frozen->{
            assertEquals(3,frozen.state().stamp().driverVersion());
            assertArrayEquals(before.driver().encode(),frozen.state().driver().encode());return null;
        });
        assertEquals(1,f.reader().calls);
        var retained=(DriverSnapshotFacts.Known)f.repository().locked(state->state);
        assertInstanceOf(DriverStateSnapshot.NullValue.class,retained.driver().campaignGoal());
        var ordinary=assertInstanceOf(DriverObservationFacts.Known.class,f.owner().read(actual)).facts();
        assertEquals(4,ordinary.driverVersion());assertInstanceOf(DriverStateSnapshot.Value.class,ordinary.driver().campaignGoal());
    }
    @Test void acceptedLegacyNullBecomesOnePersistedGoalUsedByActualOrdinaryCore(){
        var before=legacy(true);var f=fixture(before,List.of());var actual=frame("73");
        var observed=assertInstanceOf(DriverObservationFacts.Known.class,f.owner().read(actual)).facts();
        assertEquals(4,observed.driverVersion());assertEquals(2,f.reader().calls);
        var restored=DriverStateSnapshot.decodeComplete(observed.driver().encode());
        var goal=GoalCodec.decodeGoal(assertInstanceOf(DriverStateSnapshot.Value.class,restored.campaignGoal()).json());
        assertEquals(OrdinaryCampaignGoal.newGoal("episode-real-1",73),goal);
        assertEquals(DriverJson.object(before.driver().encode(),65536),DriverJson.object(restored.encode(),65536).with("campaign_goal",OpportunityJson.Nil.INSTANCE));
        var full=new DriverObservationAssembler().projectFull(actual,observed,DriverStateAssemblerTest.ref(actual.originalPacket()));
        var semanticGoal=GoalCodec.decodeGoal(DriverJson.encode(OpportunityJson.object(full.semantic().get("campaign_goal"),"actual semantic goal")));
        assertEquals(goal,semanticGoal);
        var request=new PlanningRequest(DriverStateAssemblerTest.identity(),DriverStateAssemblerTest.source(),"held-session",NOW.plusSeconds(60),new PlanningObservation(full.semantic(),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.of(semanticGoal),Optional.empty(),false));
        assertEquals(Optional.of("marriage"),OrdinaryCorePolicy.focus(request));
        assertEquals(goal,GoalCodec.decodeGoal(GoalCodec.encodeGoal(goal)));
        var again=assertInstanceOf(DriverObservationFacts.Known.class,f.owner().read(actual)).facts();
        assertEquals(4,again.driverVersion());assertArrayEquals(restored.encode(),again.driver().encode());
        assertEquals(3,f.reader().calls);assertInstanceOf(DriverStateSnapshot.NullValue.class,before.driver().campaignGoal());
    }
    @Test void rogueAndUnknownKeepNullWithoutGoalCas(){
        var rogue=fixture(legacy(false),List.of());
        assertEquals(3,assertInstanceOf(DriverObservationFacts.Known.class,rogue.owner().read(frame("73"))).facts().driverVersion());
        var k=legacy(true);var command=DriverStateAssemblerTest.command();
        var unknown=new ActionReceipt(1,8,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"software unknown",List.of(DriverStateAssemblerTest.ref(bytes("unknown")))));
        var f=fixture(k,List.of(unknown));
        var result=assertInstanceOf(DriverObservationFacts.Known.class,f.owner().read(frame("73"))).facts();
        assertEquals(3,result.driverVersion());assertInstanceOf(DriverStateSnapshot.NullValue.class,result.driver().campaignGoal());assertEquals(1,f.reader().calls);
    }
    @Test void wrongActorAndIntegerTypesCannotInitializeGoal(){
        for(String actor:List.of("74","true","73.0")){
            var f=fixture(legacy(true),List.of());
            assertThrows(IllegalArgumentException.class,()->f.owner().read(frame(actor)));
            var retained=(DriverSnapshotFacts.Known)f.repository().locked(state->state);
            assertEquals(3,retained.stamp().driverVersion());assertInstanceOf(DriverStateSnapshot.NullValue.class,retained.driver().campaignGoal());
        }
    }
}
