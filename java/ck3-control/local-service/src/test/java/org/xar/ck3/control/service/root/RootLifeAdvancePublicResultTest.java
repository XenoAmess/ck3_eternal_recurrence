package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.advance.AdvanceResult;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.driver.DriverJson;

/** Pure representation DATA. Native/canonical producer coverage is the sole actual Life private-fixture test;
 * these controlled documents never grant an original result, Root Close, permission, Ready or a game day. */
final class RootLifeAdvancePublicResultTest {
    private static final BigInteger MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static Obj base(){return DriverJson.object(raw("{\"schema\":\""+AdvanceResult.SCHEMA+"\",\"step\":\"life-advance\",\"starting_revision\":"+MAX+",\"starting_native_revision\":"+MAX+",\"revision\":"+MAX+",\"native_revision\":"+MAX+",\"actions\":[],\"war_progress_before\":{\"wars\":[{\"player_relative_war_score\":-0.0}]},\"unrelated_text\":\"18446744073709551615\"}").bytes(),RawJson.MAXIMUM_BYTES);}
    private static Obj status(){return DriverJson.object(raw("{\"state\":\"triggered\",\"generation\":"+MAX+",\"starting_date_raw\":1,\"target_date_raw\":25,\"last_observed_date_raw\":25,\"trigger_date_raw\":25,\"speed\":1,\"mode\":\"terminal_or_sentinel\",\"army_count\":0,\"combat_count\":0,\"completed_daily_ticks\":1,\"intermediate_pause_count\":0,\"trigger_flags\":1,\"trigger_reasons\":[\"date_deadline\"],\"signed_date_delta_from_target_raw\":0,\"overshoot_days\":0,\"pause_wrapper_called\":true,\"pause_observed\":true,\"terminal_observed\":false,\"abnormal\":false}").bytes(),RawJson.MAXIMUM_BYTES);}
    private static RawJson encode(Obj value){return RootLifeAdvancePublicResult.encode(new RawJson(DriverJson.encode(value)));}
    @Test void canonicalUint64MetadataAndExactSentinelConsumerPreserveOriginalMinusZeroToken(){
        Obj token=new Obj(java.util.Map.of("tactical_daily_sentinel",status()));
        Obj action=new Obj(java.util.Map.of("step",new Text(ClockStatusRead.CANCEL_PREFIX+MAX),"result",token));
        Obj original=base().with("actions",new Arr(List.of(action))).with("exact_day_native_clock",new Obj(java.util.Map.of("armed",status(),"stopped",status(),"canceled",token)));
        RawJson encoded=encode(original);Obj view=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new Text(MAX.toString()),view.get("revision"));
        Obj clock=object(view.get("exact_day_native_clock"),"clock");assertEquals(new Text(MAX.toString()),object(clock.get("stopped"),"status").get("generation"));
        assertTrue(new String(encoded.bytes(),StandardCharsets.UTF_8).contains("-0.0"));
        assertEquals(original,DriverJson.object(RootLifeAdvancePublicResult.decode(encoded).bytes(),RawJson.MAXIMUM_BYTES));
        assertEquals(new Text(MAX.toString()),view.get("unrelated_text"));
    }
    @Test void wrongIntegerTypesNullMissingAndUnsignedOverflowAreNotAliases(){
        for(Value value:List.of(new Text(MAX.toString()),new Bool(true),new DecimalValue("1.0"),Nil.INSTANCE,new IntegerValue(MAX.add(BigInteger.ONE)),new IntegerValue(BigInteger.ONE.negate())))
            assertThrows(IllegalArgumentException.class,()->encode(base().with("revision",value)));
        var fields=new java.util.LinkedHashMap<>(base().members());fields.remove("revision");assertThrows(IllegalArgumentException.class,()->encode(new Obj(fields)));
        Obj publicTree=DriverJson.object(encode(base()).bytes(),RawJson.MAXIMUM_BYTES);
        for(String text:List.of("01","+1","-0"," 1",MAX.add(BigInteger.ONE).toString()))
            assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.decode(new RawJson(DriverJson.encode(publicTree.with("revision",new Text(text))))));
    }
    @Test void unknownUnsafeIntegerAndNonfiniteFloatRefuseWithoutBroadFieldNameConversion(){
        assertThrows(IllegalArgumentException.class,()->encode(base().with("unknown",new IntegerValue(MAX))));
        assertThrows(IllegalArgumentException.class,()->encode(base().with("unknown_float",new DecimalValue("1e999"))));
        assertThrows(IllegalArgumentException.class,()->encode(base().with("exact_day_native_clock",new Obj(java.util.Map.of("stopped",status().with("generation",new Bool(true)))))));
        assertThrows(IllegalArgumentException.class,()->encode(base().with("exact_day_native_clock",new Obj(java.util.Map.of("stopped",status().with("unrecognized",new Bool(true)))))));
        assertThrows(IllegalArgumentException.class,()->encode(base().with("step",new Text("pause-map"))));
    }
    private static final OperationKey HORIZON=new OperationKey("advance-route-contact-horizon-v1-2-to-3-h-2-4-5");
    private static final OperationKey WINDOW=new OperationKey("advance-route-contact-window-v1-2-to-3-days-2-h-2-4-5");
    @Test void actualTypedAdvanceResultProducerUsesTheSameClockRolesForOnlyItsExactHorizonStep(){
        RawJson actual=producedClockReport(HORIZON);
        RawJson encoded=RootLifeAdvancePublicResult.encodeClockReport(actual,HORIZON);
        Obj publicTree=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new Text(MAX.toString()),publicTree.get("revision"));
        assertEquals(new Text(HORIZON.value()),publicTree.get("step"));
        assertEquals(new IntegerValue(BigInteger.ONE),publicTree.get("elapsed_days"));
        assertTrue(new String(encoded.bytes(),StandardCharsets.UTF_8).contains("-0.0"));
        assertEquals(DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES),
                DriverJson.object(RootLifeAdvancePublicResult.decodeClockReport(encoded,HORIZON).bytes(),RawJson.MAXIMUM_BYTES));
        assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.encode(actual));
        assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.decode(encoded));
    }
    @Test void clockReportRequiresTheActualCanonicalHorizonAndDoesNotAliasWindowOrLife(){
        RawJson actual=producedClockReport(HORIZON);
        for(OperationKey unsupported:List.of(WINDOW,new OperationKey("life-advance"),new OperationKey("pause-map"),
                new OperationKey("advance-route-contact-horizon-v1-2-to-3-h-2-5-4")))
            assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.encodeClockReport(actual,unsupported));
        OperationKey other=new OperationKey("advance-route-contact-horizon-v1-2-to-3-h-1-4");
        assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.encodeClockReport(actual,other));
        assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.encodeClockReport(producedClockReport(WINDOW),HORIZON));
        assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.encodeClockReport(producedClockReport(new OperationKey("life-advance")),HORIZON));
        Obj tree=DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES);
        assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.encodeClockReport(new RawJson(DriverJson.encode(tree.with("schema",new Text("other")))),HORIZON));
        assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.encodeClockReport(new RawJson(DriverJson.encode(tree.with("revision",new Bool(true)))),HORIZON));
        RawJson encoded=RootLifeAdvancePublicResult.encodeClockReport(actual,HORIZON);
        assertThrows(IllegalArgumentException.class,()->RootLifeAdvancePublicResult.decodeClockReport(encoded,other));
    }
    /** Actual AdvanceResult.json production consumer on complete typed software DATA; no Root or day qualification. */
    private static RawJson producedClockReport(OperationKey step){return producedClockReport(step,MAX);}
    /** Shared test-only actual typed report producer; callers gain DATA only, never Root/clock qualification. */
    static RawJson producedClockReport(OperationKey step,BigInteger endingRevision){
        int date=100;var now=Instant.parse("2026-10-24T08:00:00Z");
        var source=new org.xar.ck3.control.g2.common.G2Source("pure-life-producer-DATA",now.toString(),"software-only",
                new ExactRef("pure-life-producer-DATA/source",1,"a".repeat(64)));
        var starting=reportFrame(source,"pure-life-before",endingRevision.subtract(BigInteger.ONE),date,1,now);
        var ending=reportFrame(source,"pure-life-after",endingRevision,date+24,2,now);
        var plan=new org.xar.ck3.control.application.advance.AdvancePlan(BigInteger.valueOf(date),BigInteger.valueOf(date+24),1,1,"pure-result-DATA",true,
                org.xar.ck3.control.application.advance.AdvancePlan.ClockMode.POLLED,Optional.empty());
        var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,starting.identity(),source,
                org.xar.ck3.control.application.advance.AdvancePlan.OBSERVER,plan.expected());
        var command=new ActionCommand("pure-life-result-DATA",starting.identity(),source,"pure-life-session",step,
                new Obj(java.util.Map.of()).with(org.xar.ck3.control.application.advance.AdvancePlan.KEY,plan.json()),expected,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),now.plusSeconds(30));
        var diagnostics=new org.xar.ck3.control.application.advance.AdvanceClock.Diagnostics(BigInteger.valueOf(date),BigInteger.valueOf(date+24),1,1,1,"pure-result-DATA",
                org.xar.ck3.control.application.advance.AdvanceClock.ProgressStatus.POSTCONDITION,Optional.empty(),Optional.empty(),false,java.util.List.of(),0L,Optional.empty());
        var result=new org.xar.ck3.control.application.advance.AdvanceResult(command,plan,starting,
                new org.xar.ck3.control.application.advance.AdvanceClock.Outcome(ending,diagnostics),java.util.List.of());
        return new RawJson(DriverJson.encode(result.json()));
    }
    private static org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame reportFrame(
            org.xar.ck3.control.g2.common.G2Source source,String id,BigInteger revision,int date,long sequence,Instant now){
        var proposal=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(35465),revision,BigInteger.valueOf(date)),id,revision,"pure-life-episode");
        var identity=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(4242,new PythonOnlyUInt64(BigInteger.ONE)),proposal,sequence);
        var semantic=DriverJson.object(raw("{\"snapshot_id\":\""+id+"\",\"revision\":"+revision+",\"native_revision\":"+revision+",\"date_raw\":"+date+",\"episode_run_id\":\"pure-life-episode\",\"played_character\":{\"character_id\":35465,\"alive\":true},\"paused\":true,\"map_ready\":true,\"speed\":1,\"active_wars\":[{\"war_id\":1,\"player_relative_war_score\":-0.0}],\"player_armies\":[],\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"diagnostics\":{}}").bytes(),RawJson.MAXIMUM_BYTES);
        byte[] original=DriverJson.encode(semantic);var reference=new ExactRef("pure-life-producer-DATA/"+id,original.length,ActionCodec.sha256(original));
        return new org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame(identity,source,"pure-life-session",semantic,"pure-query-"+id,now,reference);
    }
}
