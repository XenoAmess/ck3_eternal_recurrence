package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Pure original business DATA and shared public-wire consumers. No Complete/private Root proof is fabricated. */
final class ArmyStructuralActionsTest {
    static final BigInteger WIDE=new BigInteger("18446744073709551614");
    static IntegerValue n(long value){return new IntegerValue(BigInteger.valueOf(value));}
    static Obj put(Obj original,String key,Value value){var fields=new LinkedHashMap<>(original.members());fields.put(key,value);return new Obj(fields);}
    static Obj army(int id){return new Obj(Map.ofEntries(Map.entry("army_id",n(id)),Map.entry("controllable",new Bool(true)),
            Map.entry("owner_character_id",n(73)),Map.entry("current_province_id",n(9)),Map.entry("move_target_province_id",n(11)),
            Map.entry("in_combat",new Bool(false)),Map.entry("retreating",new Bool(false)),Map.entry("army_state",new Text("idle")),
            Map.entry("army_state_code",n(0)),Map.entry("route_read_status",new Text("complete_nonempty")),
            Map.entry("route_province_ids",new Arr(List.of(n(9),n(11))))));}
    static Obj frame(String snapshot,BigInteger revision,BigInteger nativeRevision,int... ids) {
        var fields=new LinkedHashMap<String,Value>();fields.put("snapshot_id",new Text(snapshot));fields.put("revision",new IntegerValue(revision));
        fields.put("native_revision",new IntegerValue(nativeRevision));fields.put("date_raw",n(-2147483648L));
        fields.put("episode_run_id",new Text("software-episode"));fields.put("paused",new Bool(true));fields.put("map_ready",new Bool(true));
        fields.put("played_character",new Obj(Map.of("character_id",n(73),"alive",new Bool(true))));
        fields.put("diagnostics",new Obj(Map.of("bridge_pid",n(42),"connection_generation",new IntegerValue(WIDE))));
        fields.put("active_event",Nil.INSTANCE);fields.put("pending_character_interaction",Nil.INSTANCE);
        fields.put("top_exclusive_modal_choice_hint",new Obj(Map.of("status",new Text("absent"))));
        var armies=new java.util.ArrayList<Value>();for(int id:ids)armies.add(army(id));fields.put("player_armies",new Arr(armies));return new Obj(fields);
    }
    static Obj before(){return frame("native:before",WIDE.subtract(BigInteger.ONE),WIDE.subtract(BigInteger.ONE),0,7,8);}
    static Obj after(int... ids){return frame("native:after",WIDE,WIDE,ids);}
    static ArmyStructuralActions.Call call(String text){return ArmyStructuralActions.parse(new OperationKey(text)).orElseThrow();}
    static RawJson primitive(ArmyStructuralActions.Call call){return new RawJson(DriverJson.encode(new Obj(Map.of("step",new Text(call.operation().value()),
            "accepted",new Bool(true),"backend_id",new Text("native-headless"),"native_payload",new Obj(Map.of("untouched",new Text("original")))))));}
    static Obj formatted(ArmyStructuralActions.Call call,Obj before,Obj after){return DriverJson.object(ArmyStructuralActions.format(call,before,after,primitive(call)).bytes(),DriverJson.MAX_NATIVE_BYTES);}
    static Obj action(Obj formatted){return object(formatted.get("war_action"),"war_action");}
    static Obj request(String step){return new Obj(Map.of("type",new Text("execute_step"),"protocol_version",n(1),"step",new Text(step),
            "expected_revision",new IntegerValue(WIDE.subtract(BigInteger.ONE)),"request_id",new Text("original-request")));}
    static Obj rejection(){return new Obj(Map.of("type",new Text("command_result"),"protocol_version",n(1),"request_id",new Text("original-request"),
            "ok",new Bool(false),"error",new Text("CK3 halt-army command validation failed")));}
    static ArmyTypes.Context context(){
        var ref=new ExactRef("software-structural-data-no-native-permit",1,"a".repeat(64));
        var source=new G2Source("software-structural","2026-10-24T00:00:00Z","1.20.0.4",ref);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.ONE,BigInteger.valueOf(77)),"native:1",BigInteger.ONE,"software-episode");
        return new ArmyTypes.Context(new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1),source,"software-session",Instant.parse("2026-10-25T00:00:00Z"));
    }
    @Test void selectorsKeepCanonicalZeroMaximumAndDistinctMergeRoles() {
        for(String text:List.of("halt-army-0","split-army-half-2147483647","merge-armies-0-with-2147483647"))assertEquals(text,call(text).operation().value());
        for(String text:List.of("halt-army-00","halt-army--1","halt-army-2147483648","halt-army-٠","split-army-half-1.0","merge-armies-1-with-1","merge-armies-01-with-2"))
            assertTrue(ArmyStructuralActions.parse(new OperationKey(text)).isEmpty(),text);
    }
    @Test void splitNeedsExactlyOneNewControllableSiblingAndRetainsOriginalSetSemantics() {
        var call=call("split-army-half-0");assertTrue(ArmyStructuralActions.applied(call,before(),after(0,7,8,9)));
        assertTrue(ArmyStructuralActions.applied(call,before(),after(0,9)),"original branch permits other old armies to disappear");
        for(Obj after:List.of(after(7,8,9),after(0,7,8),after(0,7,8,9,10)))assertFalse(ArmyStructuralActions.applied(call,before(),after));
        Obj result=formatted(call,before(),after(0,7,8,9));assertEquals(new Text("split_applied"),action(result).get("status"));assertEquals(n(9),action(result).get("sibling_army_id"));
        assertFalse(action(formatted(call,before(),after(0,7,8))).members().containsKey("sibling_army_id"));
    }
    @Test void mergeNeedsEveryIndependentPostconditionAndExactControllableIdDelta() {
        var call=call("merge-armies-0-with-7");Obj valid=after(0,8);assertTrue(ArmyStructuralActions.applied(call,before(),valid));
        for(Obj bad:List.of(after(0,7,8),after(0),after(0,8,9),put(valid,"paused",new Bool(false)),put(valid,"map_ready",new Bool(false)),
                put(valid,"revision",before().get("revision")),put(valid,"native_revision",before().get("native_revision")),
                put(valid,"snapshot_id",before().get("snapshot_id")),put(valid,"episode_run_id",new Text("foreign")),
                put(valid,"player_armies",new Arr(List.of(put(army(0),"owner_character_id",n(74)),army(8)))),
                put(valid,"player_armies",new Arr(List.of(put(army(0),"current_province_id",n(10)),army(8))))))assertFalse(ArmyStructuralActions.applied(call,before(),bad));
        Obj result=formatted(call,before(),valid);assertEquals(new Text("merge_applied"),action(result).get("status"));
        assertEquals(new Bool(true),action(result).get("postcondition_verified"));assertEquals(new Arr(List.of(n(0),n(7),n(8))),action(result).get("player_army_ids_before"));
        assertEquals(DriverJson.object(primitive(call).bytes(),DriverJson.MAX_NATIVE_BYTES),new Obj(result.members().entrySet().stream().filter(entry->!entry.getKey().equals("war_action"))
                .collect(java.util.stream.Collectors.toMap(Map.Entry::getKey,Map.Entry::getValue))));
    }
    @Test void preflightCannotTreatBooleanFloatOrStringAsIdsOrCombatStateCode() {
        var call=call("merge-armies-0-with-7");
        for(Value wrong:List.of(new Bool(false),new DecimalValue("0.0"),new Text("0"))) {
            Obj malformed=put(before(),"player_armies",new Arr(List.of(put(army(0),"army_id",wrong),army(7))));
            assertThrows(IllegalArgumentException.class,()->ArmyStructuralActions.preflight(call,malformed));
        }
        for(Value blocked:List.of(new Text("CoMbAt"),new Text("RETREATING")))assertTrue(ArmyStructuralActions.mergeBlocked(put(army(0),"army_state",blocked)));
        assertTrue(ArmyStructuralActions.mergeBlocked(put(army(0),"army_state_code",n(6))));
        assertFalse(ArmyStructuralActions.mergeBlocked(put(army(0),"army_state_code",new Bool(true))));
    }
    @Test void haltAckAlwaysReportsSubmittedAndSignedDateIsPreserved() {
        var call=call("halt-army-0");Obj result=formatted(call,before(),after(0,7,8));
        assertFalse(ArmyStructuralActions.applied(call,before(),after(0,7,8)));assertEquals(new Text("halt_submitted"),action(result).get("status"));
        assertEquals(new Bool(false),action(result).get("postcondition_verified"));assertEquals(n(-2147483648L),action(result).get("submitted_date_raw"));
        assertEquals(new Obj(Map.of("untouched",new Text("original"))),result.get("native_payload"));
    }
    @Test void exactHaltValidatorRefusalRetainsEveryOriginalAndNeverGrantsReplayOrSubmission() {
        var call=(ArmyStructuralActions.Halt)call("halt-army-0");Obj before=before(),after=after(0,7,8),request=request(call.operation().value()),response=rejection();
        Obj result=DriverJson.object(ArmyStructuralActions.haltDeferred(call,before,after,request,response,"original-request").bytes(),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(new Bool(false),result.get("accepted"));assertEquals(new Bool(false),result.get("business_submission"));assertEquals(new Bool(false),result.get("replay_allowed"));
        Obj evidence=object(result.get("halt_rejection_evidence"),"evidence");assertEquals(request,evidence.get("native_request"));assertEquals(response,evidence.get("native_command_result"));
        for(Obj bad:List.of(put(after,"date_raw",n(2)),put(after,"episode_run_id",new Text("other")),put(after,"active_event",new Obj(Map.of())),
                put(after,"player_armies",new Arr(List.of(put(army(0),"route_province_ids",new Arr(List.of(n(9),n(12)))),army(7),army(8))))))
            assertThrows(IllegalArgumentException.class,()->ArmyStructuralActions.haltDeferred(call,before,bad,request,response,"original-request"));
        assertThrows(IllegalArgumentException.class,()->ArmyStructuralActions.haltDeferred(call,before,after,request,put(response,"error",new Text("other native error")),"original-request"));
        assertThrows(IllegalArgumentException.class,()->ArmyStructuralActions.haltDeferred(call,before,after,request,put(response,"result",new Obj(Map.of())),"original-request"));
    }
    @Test void haltReadbackRefusalRetainsTheOriginalTypedFailureIncludingMissingArmyAndObjects() {
        var halt=(ArmyStructuralActions.Halt)call("halt-army-0");Obj before=before(),after=after(0,7,8);
        for(Obj bad:List.of(after(7,8),put(after,"diagnostics",Nil.INSTANCE),put(after,"played_character",Nil.INSTANCE),
                put(after,"date_raw",n(2)),put(after,"active_event",new Obj(Map.of())),
                put(after,"player_armies",new Arr(List.of(put(army(0),"route_province_ids",new Text("not a route"))))))) {
            var failure=assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.haltDeferred(halt,before,bad,
                    request(halt.operation().value()),rejection(),"original-request"));
            assertEquals(ArmyStructuralActions.DriverFailureReason.HALT_ROUTE_READBACK,failure.reason());
            assertEquals("native halt validator rejection lacks unchanged route/owner readback",failure.getMessage());
        }
        for(Obj bad:List.of(put(before,"diagnostics",Nil.INSTANCE),put(before,"played_character",Nil.INSTANCE),
                put(before,"player_armies",new Arr(List.of(put(army(0),"route_province_ids",Nil.INSTANCE))))))
            assertEquals(ArmyStructuralActions.DriverFailureReason.HALT_ROUTE_READBACK,
                    assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.haltDeferred(halt,bad,after,
                            request(halt.operation().value()),rejection(),"original-request")).reason());
    }
    @Test void haltOriginalPacketMismatchDoesNotEnterTheDeferredReadbackOrAcquireItsDriverFault() {
        var halt=(ArmyStructuralActions.Halt)call("halt-army-0");Obj before=put(before(),"revision",new IntegerValue(WIDE.subtract(BigInteger.TWO)));
        Obj request=request(halt.operation().value()),response=rejection();
        assertNotEquals(before.get("revision"),before.get("native_revision"));
        assertEquals(before.get("native_revision"),request.get("expected_revision"));
        assertTrue(ArmyStructuralActions.matchesHaltRefusal(halt,before,request,response,"original-request"));
        for(Obj wrong:List.of(put(response,"error",new Text("other native error")),put(response,"result",new Obj(Map.of())),
                put(response,"request_id",new Text("other")),put(response,"protocol_version",n(2)),put(response,"ok",new Bool(true))))
            assertFalse(ArmyStructuralActions.matchesHaltRefusal(halt,before,request,wrong,"original-request"));
        assertFalse(ArmyStructuralActions.matchesHaltRefusal(halt,before,put(request,"expected_revision",n(1)),response,"original-request"));
        assertFalse(ArmyStructuralActions.matchesHaltRefusal(halt,before,request,response,""));
    }
    @Test void actualFullFormattersUseSoleWireWideCounterPathsAndKeepNullMissingAndNumericIds() {
        var merge=call("merge-armies-0-with-7");Obj mergeData=formatted(merge,before(),after(0,8));
        RawJson mergeWire=ArmyPublicWire.encodeExactSourceBound(mergeData,context());assertEquals(mergeData,ArmyPublicWire.decodeExactSourceBound(mergeWire,context()));
        var encoded=ArmyJson.parse(mergeWire.bytes());assertEquals(WIDE.toString(),encoded.path("war_action").path("observed_public_revision").textValue());
        assertTrue(encoded.path("war_action").path("source_army_id").isIntegralNumber());assertEquals(-2147483648,encoded.path("war_action").path("submitted_date_raw").intValue());
        var halt=(ArmyStructuralActions.Halt)call("halt-army-0");Obj refusal=DriverJson.object(ArmyStructuralActions.haltDeferred(halt,before(),after(0,7,8),request(halt.operation().value()),rejection(),"original-request").bytes(),DriverJson.MAX_NATIVE_BYTES);
        RawJson refusalWire=ArmyPublicWire.encodeExactSourceBound(refusal,context());assertEquals(refusal,ArmyPublicWire.decodeExactSourceBound(refusalWire,context()));
        assertFalse(ArmyJson.parse(refusalWire.bytes()).path("halt_rejection_evidence").path("native_command_result").has("result"));
        Obj nullable=put(army(0),"move_target_province_id",Nil.INSTANCE);Obj halting=put(before(),"player_armies",new Arr(List.of(nullable)));
        Obj haltData=formatted(halt,halting,halting);assertEquals(Nil.INSTANCE,action(haltData).get("original_move_target_province_id"));
        assertEquals(haltData,ArmyPublicWire.decodeExactSourceBound(ArmyPublicWire.encodeExactSourceBound(haltData,context()),context()));
    }
    @Test void haltDateValidationOccursOnlyAfterSuccessfulPrimitiveAndNeverInExactDeferredBranch() {
        var halt=(ArmyStructuralActions.Halt)call("halt-army-0");
        for(Value wrong:List.of(Nil.INSTANCE,new Bool(true),new DecimalValue("1.0"),new Text("1"))) {
            Obj before=put(before(),"date_raw",wrong),after=put(after(0,7,8),"date_raw",wrong);
            assertDoesNotThrow(()->ArmyStructuralActions.preflight(halt,before));
            var fault=assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.format(halt,before,after,primitive(halt)));
            assertEquals(ArmyStructuralActions.DriverFailureReason.DATE_RAW,fault.reason());
            assertEquals("native halt starting snapshot lacks date_raw",fault.getMessage());
            assertDoesNotThrow(()->ArmyStructuralActions.haltDeferred(halt,before,after,request(halt.operation().value()),rejection(),"original-request"));
        }
    }
    @Test void originalDriverPreflightFaultsHaveFiniteTypedReasonsAndExactMessagesRatherThanGenericParserAliases() {
        for(String step:List.of("halt-army-0","split-army-half-0","merge-armies-0-with-7")) {
            var fault=assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.preflight(call(step),after(8)));
            assertEquals(step.startsWith("merge")?ArmyStructuralActions.DriverFailureReason.CONTROLLABLE_PAIR:ArmyStructuralActions.DriverFailureReason.CONTROLLABLE_SOURCE,fault.reason());
            assertEquals(step.startsWith("merge")?"native merge-armies requires two controllable player armies":step.startsWith("halt")?
                    "native halt requires a controllable player army":"native split-army-half-0 requires a controllable player army",fault.getMessage());
        }
        Obj combat=put(before(),"player_armies",new Arr(List.of(put(army(0),"in_combat",new Bool(true)),army(7))));
        var combatFault=assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.preflight(call("merge-armies-0-with-7"),combat));
        assertEquals(ArmyStructuralActions.DriverFailureReason.SAME_PROVINCE_NONCOMBAT,combatFault.reason());
        assertEquals("native merge-armies requires an advertised same-province non-combat pair",combatFault.getMessage());
        var dateFault=assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.preflight(call("split-army-half-0"),put(before(),"date_raw",new Bool(true))));
        assertEquals(ArmyStructuralActions.DriverFailureReason.DATE_RAW,dateFault.reason());assertEquals("native split-army-half starting snapshot lacks date_raw",dateFault.getMessage());
        assertThrows(IllegalArgumentException.class,()->ArmyStructuralActionCodec.decode(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
}
