package org.xar.ck3.control.application.planning.identity;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original supported-branch DATA and persistence contracts; no Root/source qualification is invented. */
class OperatorPlayerSwitchTest {
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static ExactRef ref(String name){return new ExactRef(name,1,"a".repeat(64));}
    private static final OperatorPlayerSwitch.Request REQUEST=new OperatorPlayerSwitch.Request(7,BigInteger.TEN);
    @Test void strictPublicRequestAndExactSupportedBuild() {
        assertEquals(REQUEST,OperatorPlayerSwitch.decode(raw("{\"character_id\":7,\"expected_revision\":10}")));
        assertEquals(StrictJson.UINT64_MAX,OperatorPlayerSwitch.decode(raw("{\"character_id\":7,\"expected_revision\":\"18446744073709551615\"}")).expectedRevision());
        for(String invalid:List.of("true","7.0","-1","0","2147483648","\"7\""))assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.decode(raw("{\"character_id\":"+invalid+",\"expected_revision\":10}")));
        for(String invalid:List.of("true","10.0","-1","9007199254740992","\"01\"","null"))assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.decode(raw("{\"character_id\":7,\"expected_revision\":"+invalid+"}")));
        OperatorPlayerSwitch.requireSupported("1.19.0.6",OperatorPlayerSwitch.EXECUTABLE_SHA256,Set.of(OperatorPlayerSwitch.CAPABILITY));
        assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.requireSupported("1.20.0.4",OperatorPlayerSwitch.EXECUTABLE_SHA256,Set.of(OperatorPlayerSwitch.CAPABILITY)));
        assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.requireSupported("1.19.0.6","0".repeat(64),Set.of(OperatorPlayerSwitch.CAPABILITY)));
    }
    @Test void originalBeforeAllowsDeadActorButAfterMustIndependentlyShowAliveTarget() {
        var before=StrictJson.parse(raw("{\"revision\":10,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":3,\"alive\":false}}").bytes());
        OperatorPlayerSwitch.requireBefore(REQUEST,before);
        var after=StrictJson.parse(raw("{\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":7,\"alive\":true}}").bytes());
        OperatorPlayerSwitch.requireAfter(REQUEST,after);
        assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.requireAfter(REQUEST,before));
        OperatorPlayerSwitch.requireRebound(REQUEST,"same-run",StrictJson.parse(raw("{\"episode_character_id\":7,\"episode_run_id\":\"same-run\",\"one_life_terminal\":false,\"one_life_terminal_reason\":null}").bytes()));
        assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.requireRebound(REQUEST,"same-run",StrictJson.parse(raw("{\"episode_character_id\":7,\"episode_run_id\":\"other-run\",\"one_life_terminal\":false,\"one_life_terminal_reason\":null}").bytes())));
    }
    private static com.fasterxml.jackson.databind.JsonNode internalBefore(BigInteger revision) {
        var semantic=new OpportunityJson.Obj(Map.of("paused",new OpportunityJson.Bool(true),"map_ready",new OpportunityJson.Bool(true),
                "revision",new OpportunityJson.IntegerValue(revision)));
        return FullJsonTree.parse(DriverJson.encode(semantic),DriverJson.MAX_NATIVE_BYTES);
    }
    @Test void actualInternalSemanticProducerAndFullJsonTreePreserveTheEntireUnsignedIntegerDomain() {
        for(BigInteger revision:List.of(BigInteger.ZERO,BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER),
                new BigInteger("9007199254740992"),new BigInteger("9007199254740993"),StrictJson.UINT64_MAX)) {
            var request=new OperatorPlayerSwitch.Request(7,revision);
            assertEquals(revision,OperatorPlayerSwitch.internalRevision(new OpportunityJson.IntegerValue(revision)));
            var original=internalBefore(revision);
            assertTrue(original.get("revision").isIntegralNumber());assertEquals(revision,original.get("revision").bigIntegerValue());
            OperatorPlayerSwitch.requireBefore(request,original);
            var publicRequest=OperatorPlayerSwitch.decode(raw("{\"character_id\":7,\"expected_revision\":\""+revision+"\"}"));
            assertEquals(request,publicRequest);OperatorPlayerSwitch.requireBefore(publicRequest,original);
        }
    }
    @Test void internalIntegerBoundaryRejectsBooleanFractionalTextNullMissingNegativeOverflowAndMismatch() {
        for(String token:List.of("true","false","1.0","1e0","\"0\"","\"9007199254740993\"","null","-1","18446744073709551616")) {
            assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.requireBefore(new OperatorPlayerSwitch.Request(7,BigInteger.ZERO),
                    FullJsonTree.parse(raw("{\"paused\":true,\"map_ready\":true,\"revision\":"+token+"}").bytes(),DriverJson.MAX_NATIVE_BYTES)));
        }
        var missing=FullJsonTree.parse(raw("{\"paused\":true,\"map_ready\":true}").bytes(),DriverJson.MAX_NATIVE_BYTES);
        assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.requireBefore(REQUEST,missing));
        for(var invalid:List.<OpportunityJson.Value>of(new OpportunityJson.Bool(true),new OpportunityJson.Text("0"),OpportunityJson.Nil.INSTANCE,
                new OpportunityJson.IntegerValue(BigInteger.valueOf(-1)),new OpportunityJson.IntegerValue(StrictJson.UINT64_MAX.add(BigInteger.ONE))))
            assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.internalRevision(invalid));
        assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.requireBefore(REQUEST,internalBefore(BigInteger.valueOf(11))));
    }
    @Test void publicRequestAndCompletionRemainTheirOwnSafeNumberAndCanonicalStringDomains() {
        for(String token:List.of("0",Long.toString(StrictJson.MAX_SAFE_INTEGER),"\"9007199254740992\"","\"18446744073709551615\""))
            OperatorPlayerSwitch.decode(raw("{\"character_id\":7,\"expected_revision\":"+token+"}"));
        for(String token:List.of("9007199254740992","18446744073709551615","true","1.0","\"01\"","\"+1\"","\"-1\"","\"18446744073709551616\""))
            assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.decode(raw("{\"character_id\":7,\"expected_revision\":"+token+"}")));
        var request=new OperatorPlayerSwitch.Request(7,StrictJson.UINT64_MAX);
        var game=new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(1001)));
        var source=new G2Source("machine","2026-10-24T21:45:00Z","1.19.0.6",ref("source"));
        var refs=new OperatorPlayerSwitch.Artifacts(ref("hello"),ref("before"),ref("ack"),ref("after"),ref("old-driver"),ref("new-driver"),
                ref("old-aux"),ref("new-aux"),ref("commit"),ref("private-proof"),ref("rebound"));
        var completion=new OperatorPlayerSwitch.Completion(request,"action","b".repeat(64),"request",source,
                new NativeObservationPort.TransportSession("machine",game,BigInteger.ONE,"session"),"same-run",5,3,8,9,
                OperatorPlayerSwitch.NativeStatus.SWITCHED,StrictJson.UINT64_MAX,StrictJson.UINT64_MAX,100,refs);
        var decoded=OperatorPlayerSwitch.decodeCompletion(completion.encode());assertEquals(completion,decoded);
        var persisted=StrictJson.parse(completion.encode());assertTrue(persisted.get("expected_revision").isTextual());
        assertEquals(StrictJson.UINT64_MAX.toString(),persisted.get("expected_revision").textValue());
        var presented=StrictJson.parse(OperatorPlayerSwitch.publicResult(decoded,3L).bytes());
        for(String field:List.of("before_revision","after_revision","native_revision"))
            assertEquals(StrictJson.UINT64_MAX.toString(),presented.get(field).textValue());
        var malformed=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(completion.encode());
        malformed.put("expected_revision",BigInteger.ONE);
        assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.decodeCompletion(StrictJson.canonical(malformed)));
    }
    @Test void actualDriverProducerReplacementPreservesRunHistoryLifecycleAndSerializes() {
        var nil=new DriverStateSnapshot.NullValue();var lifecycle=new DriverStateSnapshot.Value("{\"original_terminal\":true}".getBytes(StandardCharsets.UTF_8));
        var original=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("pipe",123,BigInteger.valueOf(3),"same-run"),List.of(),nil,nil,nil,
                new DriverStateSnapshot.Value("{\"old_expectation\":true}".getBytes(StandardCharsets.UTF_8)),lifecycle,nil,nil);
        var aux=new OpportunityJson.Obj(Map.of("unrelated",new OpportunityJson.Text("retain"),"army_strength_query",new OpportunityJson.Text("stale")));
        var replacement=OperatorPlayerSwitch.replacement(original,aux,REQUEST);
        assertTrue(replacement.rebindPerformed());assertEquals("same-run",replacement.driver().session().episodeRunId());assertEquals(BigInteger.valueOf(7),replacement.driver().session().actorId());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,replacement.driver().successionExpectation());assertSame(lifecycle,replacement.driver().successionLifecycle());
        assertEquals(aux.get("unrelated"),replacement.auxiliary().get("unrelated"));assertEquals(OpportunityJson.Nil.INSTANCE,replacement.auxiliary().get("army_strength_query"));
        assertEquals(new OpportunityJson.Text("operator_played_character_rebind"),replacement.auxiliary().get("restore_kind"));
        assertEquals(OpportunityJson.Nil.INSTANCE,replacement.auxiliary().get("active_combat_retreat_token"));
        assertFalse(replacement.auxiliary().members().containsKey("driver_state_restore_kind"));
        assertFalse(replacement.auxiliary().members().containsKey("active_combat_retreat_v1_token"));
        assertFalse(replacement.auxiliary().members().containsKey("war_termination_options"));
        assertArrayEquals(replacement.driver().encode(),DriverStateSnapshot.decodeComplete(replacement.driver().encode()).encode());
        var unchanged=OperatorPlayerSwitch.replacement(replacement.driver(),replacement.auxiliary(),REQUEST);assertFalse(unchanged.rebindPerformed());assertSame(replacement.driver(),unchanged.driver());
    }
    @Test void completionPersistenceHasExactArtifactsAndSameEpochVersionSemantics() {
        var game=new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(1001)));
        var source=new G2Source("machine","2026-10-24T08:20:00Z","1.19.0.6",ref("source"));
        var transport=new NativeObservationPort.TransportSession("machine",game,BigInteger.ONE,"session");
        var refs=new OperatorPlayerSwitch.Artifacts(ref("hello"),ref("before"),ref("ack"),ref("after"),ref("old-driver"),ref("new-driver"),ref("old-aux"),ref("new-aux"),ref("commit"),ref("private-proof"),ref("rebound"));
        var value=new OperatorPlayerSwitch.Completion(REQUEST,"action","b".repeat(64),"request",source,transport,"same-run",5,3,8,9,
                OperatorPlayerSwitch.NativeStatus.SWITCHED,BigInteger.valueOf(11),BigInteger.valueOf(12),-10,refs);
        var decoded=OperatorPlayerSwitch.decodeCompletion(value.encode());assertEquals(value,decoded);assertEquals(5,decoded.episodeEpoch());assertEquals(11,decoded.references().size());
        var publicResult=StrictJson.parse(OperatorPlayerSwitch.publicResult(decoded,3L).bytes());assertEquals("10",publicResult.get("before_revision").textValue());assertTrue(publicResult.get("episode_rebind_performed").booleanValue());assertEquals("same-run",publicResult.get("episode_run_id").textValue());
        assertTrue(publicResult.get("date_raw").isIntegralNumber());assertEquals(-10,publicResult.get("date_raw").intValue());
        var malformed=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(value.encode());malformed.put("prior_actor",true);assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.decodeCompletion(StrictJson.canonical(malformed)));
        var wrongVersion=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(value.encode());wrongVersion.put("after_driver_version",10);assertThrows(RuntimeException.class,()->OperatorPlayerSwitch.decodeCompletion(StrictJson.canonical(wrongVersion)));
        for(long outside:new long[]{(long)Integer.MIN_VALUE-1,(long)Integer.MAX_VALUE+1})
            assertThrows(RuntimeException.class,()->new OperatorPlayerSwitch.Completion(value.request(),value.actionId(),value.bodySha256(),value.requestId(),value.source(),value.transport(),
                    value.episodeRunId(),value.episodeEpoch(),value.priorActor(),value.beforeDriverVersion(),value.afterDriverVersion(),value.status(),value.afterRevision(),value.nativeRevision(),outside,value.originals()));
    }
    @Test void actualAuxiliaryReplacementFeedsTheSoleSessionPresentationProducerAndItsStrictCodec() {
        var nil=new DriverStateSnapshot.NullValue();
        var original=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("pipe",123,BigInteger.valueOf(3),"same-run"),List.of(),nil,nil,nil,nil,nil,nil,nil);
        var auxiliary=new OpportunityJson.Obj(Map.of("driver_state_restored",new OpportunityJson.Bool(false),"driver_state_error",OpportunityJson.Nil.INSTANCE,
                "restore_kind",new OpportunityJson.Text("new_episode"),"episode_binding_state",new OpportunityJson.Text("active_new"),
                "cold_candidate_rejection",OpportunityJson.Nil.INSTANCE,"episode_transition_error",OpportunityJson.Nil.INSTANCE,
                "capability_session_paths",new OpportunityJson.Obj(Map.of("queue_dir",OpportunityJson.Nil.INSTANCE,"driver_state_path",OpportunityJson.Nil.INSTANCE))));
        var replaced=OperatorPlayerSwitch.replacement(original,auxiliary,REQUEST);
        var presented=org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.sessionPresentation(replaced.auxiliary());
        assertEquals(org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.BindingState.ACTIVE_OPERATOR_REBIND,presented.bindingState());
        assertEquals(java.util.Optional.of(org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.RestoreKind.OPERATOR_PLAYED_CHARACTER_REBIND),presented.restoreKind());
        var actualPublicFields=presented.original();
        assertEquals(new OpportunityJson.Text("operator_played_character_rebind"),actualPublicFields.get("driver_state_restore_kind"));
        assertFalse(actualPublicFields.members().containsKey("restore_kind"));
        assertEquals(presented,org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.decode(actualPublicFields));
    }
    @Test void identicalContentLocatorsAreDataAndCannotStandInForIndependentTransportCustody() {
        var game=new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(1001)));
        var source=new G2Source("machine","2026-10-24T09:10:00Z","1.19.0.6",ref("source"));
        var snapshot=ref("same-snapshot-content");
        var refs=new OperatorPlayerSwitch.Artifacts(ref("hello"),snapshot,ref("typed-ack"),snapshot,ref("driver"),ref("driver"),
                ref("aux"),ref("aux"),ref("actual-durable-ack-point"),ref("private-proof"),snapshot);
        var value=new OperatorPlayerSwitch.Completion(REQUEST,"action","b".repeat(64),"request",source,
                new NativeObservationPort.TransportSession("machine",game,BigInteger.ONE,"session"),"same-run",5,7,8,8,
                OperatorPlayerSwitch.NativeStatus.ALREADY_PLAYED,BigInteger.TEN,BigInteger.TEN,100,refs);
        assertFalse(value.rebindPerformed());assertEquals(value,OperatorPlayerSwitch.decodeCompletion(value.encode()));
        assertEquals(value.originals().beforeNative(),value.originals().afterNative());
        // No actual Root SourceFactory, writer, GuardEvidence or independent receive qualification is constructed here.
    }
}
