package org.xar.ck3.control.application.planning.events;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningWire;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome;

/** Controlled semantic snapshot DATA -> both shared producer entries -> real request/command codecs -> actual projector.
 * No ordinary Ready, private read permission, Core, native reader, ACK or Game is constructed. */
final class NativeEventExpectationProducerTest {
    private static final ExactRef REF=new ExactRef("controlled-event-snapshot-data",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("event-expectation-software","2026-10-24T07:00:00Z","1.20.0.4",REF);
    private static final String GENERATION="18446744073709551615";
    private static final OpportunityJson.Obj PLAN=new OpportunityJson.Obj(Map.of());
    private static final Instant DEADLINE=Instant.parse("2026-10-24T07:10:00Z");
    private static ObservationIdentity identity(int revision,int nativeRevision){
        return new ObservationIdentity(SOURCE.machineId(),new GameGeneration(101,new PythonOnlyUInt64(new BigInteger("9007199254740993"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(29829),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(53144520)),
                        "p"+revision,BigInteger.valueOf(revision),"event-expectation-episode"),1);
    }
    private static OpportunityJson.Obj snapshot(int revision,int nativeRevision,String event,String pending,String generation){
        String raw="{\"snapshot_id\":\"p"+revision+"\",\"revision\":"+revision+",\"native_revision\":"+nativeRevision+
                ",\"date_raw\":53144520,\"episode_run_id\":\"event-expectation-episode\",\"paused\":true,\"map_ready\":true,"+
                "\"played_character\":{\"character_id\":29829},\"active_wars\":[],\"player_armies\":[],"+
                "\"diagnostics\":{\"bridge_pid\":101,\"connection_generation\":"+generation+"}"+
                (event==null?"":",\"active_event\":"+event)+(pending==null?"":",\"pending_character_interaction\":"+pending)+"}";
        return object(raw);
    }
    private static OpportunityJson.Obj object(String json){
        return OpportunityJson.object(OpportunityJson.parse(json.getBytes(StandardCharsets.UTF_8)),"controlled semantic input");
    }
    private static PlanningRequest request(OpportunityJson.Obj actual){
        return new PlanningRequest(identity(900,51),SOURCE,"controlled-event-session",DEADLINE,
                new PlanningObservation(actual,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static NativeEventPostconditionPort legacy(){
        return new NativeEventPostconditionPort((command,deadline)->{throw new AssertionError("pure expectation preparation must not read native state");});
    }
    private static ExpectedPostcondition expected(OpportunityJson.Obj actual,String operation){
        return NativeEventPostconditionPort.expected(identity(900,51),SOURCE,actual,new OperationKey(operation),PLAN,Optional.empty()).orElseThrow();
    }
    private static BigInteger old(ExpectedPostcondition value){
        return value.values().stream().filter(v->v.field().value().equals("old_instance_id")).map(ExpectedInteger.class::cast).findFirst().orElseThrow().value();
    }
    private static NativeEventPostconditionPort.BoundSnapshot after(String event,String pending,String generation){
        return new NativeEventPostconditionPort.BoundSnapshot(identity(902,53),SOURCE,"controlled-event-session",
                snapshot(902,53,event,pending,generation),"distinct-independent-read",Instant.parse("2026-10-24T07:00:01Z"),REF);
    }
    @Test void actualPlanningEntryAndPrivateSnapshotEntryShareOneProducerIncludingTraitSeparation(){
        var actual=snapshot(900,51,"{\"instance_id\":17}","{\"instance_id\":-2}",GENERATION);
        var ordinary=request(actual);var roundtrip=PlanningWire.decodeRequest(PlanningWire.encodeRequest(ordinary));assertEquals(ordinary,roundtrip);
        var material=new PoetTraitOutcome.Ready(new PoetTraitOutcome.Binding(PoetTraitOutcome.Choice.POET,
                new PoetTraitOutcome.PublicFrame("p900",BigInteger.valueOf(900),new EventTraitMembership.Frame(BigInteger.valueOf(51),53144520,29829))));
        Optional<PoetTraitOutcome.Expectation> trait=Optional.of(material);
        EventPolicies.NativeExpectationPort publicPort=legacy();
        for(String step:List.of("select-event-option-1","accept-pending-character-interaction","reject-pending-character-interaction",
                "block-pending-character-interaction","acknowledge-pending-character-interaction")){
            var operation=new OperationKey(step);
            var pure=NativeEventPostconditionPort.expected(roundtrip.before(),roundtrip.source(),roundtrip.observations().snapshot(),operation,PLAN,trait);
            assertEquals(publicPort.expected(roundtrip,operation,PLAN,trait),pure);
            assertEquals(NativeEventPostconditionPort.expected(roundtrip.before(),roundtrip.source(),actual,operation,PLAN,Optional.empty()),pure);
            var value=pure.orElseThrow();assertEquals(4,value.values().size(),"material trait proof remains the separate existing effect producer");
            assertEquals(GENERATION,value.values().stream().filter(v->v.field().value().equals("connection_generation_decimal")).map(ExpectedText.class::cast).findFirst().orElseThrow().value());
            assertEquals(step.startsWith("select-event-option-")?BigInteger.valueOf(17):BigInteger.valueOf(-2),old(value));
        }
    }
    @Test void exactNativeInstanceAndIntegerTokenGuardsRemainShared(){
        for(String id:List.of("1","2147483647")){
            var actual=snapshot(900,51,"{\"instance_id\":"+id+"}",null,GENERATION);
            assertEquals(new BigInteger(id),old(expected(actual,"select-event-option-1")));
            assertEquals(legacy().expected(request(actual),new OperationKey("select-event-option-1"),PLAN,Optional.empty()).orElseThrow(),expected(actual,"select-event-option-1"));
        }
        for(String id:List.of("-2147483648","-2","0","2147483647")){
            var actual=snapshot(900,51,null,"{\"instance_id\":"+id+"}",GENERATION);
            assertEquals(new BigInteger(id),old(expected(actual,"reject-pending-character-interaction")));
            assertEquals(legacy().expected(request(actual),new OperationKey("reject-pending-character-interaction"),PLAN,Optional.empty()).orElseThrow(),
                    expected(actual,"reject-pending-character-interaction"));
        }
        for(String id:List.of("0","-1","2147483648","-2147483649","true","1.0","null","\"17\"")){
            assertThrows(IllegalArgumentException.class,()->expected(snapshot(900,51,"{\"instance_id\":"+id+"}",null,GENERATION),"select-event-option-1"));
        }
        for(String id:List.of("-1","2147483648","-2147483649","true","1.0","null","\"-2\"")){
            assertThrows(IllegalArgumentException.class,()->expected(snapshot(900,51,null,"{\"instance_id\":"+id+"}",GENERATION),"accept-pending-character-interaction"));
        }
        for(String generation:List.of("true","1.0","null","\"7\"")){
            assertThrows(IllegalArgumentException.class,()->expected(snapshot(900,51,"{\"instance_id\":17}",null,generation),"select-event-option-1"));
        }
        assertThrows(IllegalArgumentException.class,()->expected(snapshot(900,51,"{}",null,GENERATION),"select-event-option-1"));
        assertThrows(IllegalArgumentException.class,()->expected(object("{\"active_event\":{\"instance_id\":17}}"),"select-event-option-1"));
    }
    @Test void unsupportedMissingAndNullInstancesProduceNoInventedExpectation(){
        for(String instance:new String[]{null,"null","false","[]","\"unknown\""}){
            var actual=snapshot(900,51,instance,instance,GENERATION);
            for(String operation:List.of("select-event-option-1","reject-pending-character-interaction")){
                assertTrue(NativeEventPostconditionPort.expected(identity(900,51),SOURCE,actual,new OperationKey(operation),PLAN,Optional.empty()).isEmpty());
                assertEquals(legacy().expected(request(actual),new OperationKey(operation),PLAN,Optional.empty()),
                        NativeEventPostconditionPort.expected(identity(900,51),SOURCE,actual,new OperationKey(operation),PLAN,Optional.empty()));
            }
        }
        var actual=snapshot(900,51,"{\"instance_id\":17}",null,GENERATION);
        assertTrue(NativeEventPostconditionPort.expected(identity(900,51),SOURCE,actual,new OperationKey("unregistered-event-action"),PLAN,Optional.empty()).isEmpty());
        assertThrows(NullPointerException.class,()->NativeEventPostconditionPort.expected(identity(900,51),SOURCE,actual,new OperationKey("select-event-option-1"),null,Optional.empty()));
        assertThrows(NullPointerException.class,()->NativeEventPostconditionPort.expected(identity(900,51),SOURCE,actual,new OperationKey("select-event-option-1"),PLAN,null));
    }
    @Test void actualProducerCommandSerdeFeedsUnchangedProjectorWithoutReplayingUnknown(){
        for(String operation:List.of("select-event-option-1","reject-pending-character-interaction")){
            boolean event=operation.startsWith("select-event-option-");
            var actual=snapshot(900,51,event?"{\"instance_id\":17}":null,event?null:"{\"instance_id\":-2147483648}",GENERATION);
            var produced=expected(actual,operation);
            var command=new ActionCommand("controlled-event",identity(900,51),SOURCE,"controlled-event-session",new OperationKey(operation),PLAN,
                    produced,new Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
            var replayed=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));assertEquals(command,replayed);
            var consumed=after(event?"null":null,event?null:"null",GENERATION);
            var facts=NativeEventPostconditionPort.project(replayed.before(),replayed.source(),replayed.sessionId(),replayed.expected(),replayed.arguments(),consumed);
            assertEquals(produced.values(),facts.orElseThrow());
            var unchanged=after(event?"{\"instance_id\":17}":null,event?null:"{\"instance_id\":-2147483648}",GENERATION);
            assertTrue(NativeEventPostconditionPort.project(replayed.before(),replayed.source(),replayed.sessionId(),replayed.expected(),replayed.arguments(),unchanged).isEmpty());
            assertTrue(NativeEventPostconditionPort.project(replayed.before(),replayed.source(),replayed.sessionId(),replayed.expected(),replayed.arguments(),after(null,null,GENERATION)).isEmpty());
            assertTrue(NativeEventPostconditionPort.project(replayed.before(),replayed.source(),replayed.sessionId(),replayed.expected(),replayed.arguments(),after(event?"null":null,event?null:"null","7")).isEmpty());
        }
    }
}
